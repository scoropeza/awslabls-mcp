# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""D2 CLI subprocess wrapper for diagram rendering.

Handles D2 binary detection, async subprocess execution, timeout enforcement,
and structured result parsing. No Python code execution — D2 CLI does all
rendering in its own process.
"""

import asyncio
import os
import re
import shutil
from awslabs.aws_diagram_mcp_server.consts import (
    BUNDLED_FONTS_DIR,
    DEFAULT_LAYOUT_ENGINE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TIMEOUT,
    FONT_FAMILIES,
    OUTPUT_SUBDIRECTORY,
    get_font_search_dirs,
)
from awslabs.aws_diagram_mcp_server.models import D2RenderResult, D2VersionInfo
from loguru import logger


async def check_d2_installed() -> D2VersionInfo | None:
    """Check if D2 is installed and return version info.

    Returns:
        D2VersionInfo if D2 is found, None otherwise.
    """
    d2_path = shutil.which('d2')
    if d2_path is None:
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            d2_path,
            '--version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        version = stdout.decode().strip()
        return D2VersionInfo(version=version, path=d2_path)
    except Exception as e:
        logger.warning(f'Failed to get D2 version: {e}')
        return None


# D2 shapes that do NOT support the 3d style property.
# 3d only works on: square, rectangle, hexagon.
_NON_3D_SHAPES = frozenset(
    {
        'person',
        'cloud',
        'cylinder',
        'diamond',
        'oval',
        'circle',
        'stored_data',
        'page',
        'package',
        'queue',
        'callout',
        'parallelogram',
        'image',
    }
)


def _find_3d_compatible_node_paths(d2_source: str) -> list[str]:
    """Scan D2 source for node paths that support the 3d style.

    D2 only allows style.3d on square, rectangle, and hexagon shapes.
    The ** glob cannot be used because it fails at compile time if any
    incompatible shape exists. Instead, this function finds all node
    declarations and returns only those with compatible shapes (or no
    explicit shape, since the default shape is rectangle).

    Performs a best-effort line-by-line parse tracking brace nesting.

    Args:
        d2_source: D2 DSL source code.

    Returns:
        List of D2 node paths that can have style.3d: true applied.
    """
    # Track all nodes and their shapes
    # key: node path, value: shape name or None (default = rectangle)
    nodes: dict[str, str | None] = {}
    path_stack: list[str] = []

    for line in d2_source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Dot-notation shape: node.shape: value
        dot_m = re.match(r'^([\w][\w.-]*?)\.shape:\s*(\w+)', stripped)
        if dot_m:
            node_path = dot_m.group(1)
            nodes[node_path] = dot_m.group(2)
            continue

        # Block shape: shape: value (inside a node block)
        shape_m = re.match(r'^shape:\s*(\w+)', stripped)
        if shape_m and path_stack:
            full_path = '.'.join(path_stack)
            nodes[full_path] = shape_m.group(1)
            continue

        # Track nesting via brace counts (skip connections and style lines)
        net_open = stripped.count('{') - stripped.count('}')
        if net_open > 0 and '->' not in stripped and '<-' not in stripped:
            name_m = re.match(r'^([\w][\w-]*)', stripped)
            if name_m:
                node_name = name_m.group(1)
                # Skip D2 keywords that are not real nodes
                if node_name not in ('style', 'vars', 'steps', 'scenarios', 'layers'):
                    path_stack.append(node_name)
                    full_path = '.'.join(path_stack)
                    # Register node if not already registered with a shape
                    if full_path not in nodes:
                        nodes[full_path] = None  # default shape = rectangle
        elif net_open < 0:
            for _ in range(abs(net_open)):
                if path_stack:
                    path_stack.pop()

    # Return only paths with 3d-compatible shapes
    return [path for path, shape in nodes.items() if shape is None or shape not in _NON_3D_SHAPES]


def _inject_global_styles(
    d2_source: str,
    shadow: bool = False,
    three_d: bool = False,
    animated: bool = False,
) -> str:
    """Inject D2 glob patterns and overrides for global style options.

    Preamble globs go before the source; 3d shape overrides go after the
    source (D2 requires nodes to be declared before overrides are applied,
    otherwise the glob fails at compile time on incompatible shapes).

    Args:
        d2_source: Original D2 DSL source code.
        shadow: Apply drop shadow to all shapes.
        three_d: Apply 3D effect to compatible shapes (auto-excludes incompatible).
        animated: Apply animated dashes to all connections.

    Returns:
        D2 source with style injections (or unchanged if no flags set).
    """
    preamble: list[str] = []
    epilogue: list[str] = []

    if shadow:
        preamble.append('**.style.shadow: true')
    if three_d:
        # Cannot use **.style.3d: true — D2 fails at compile time if ANY
        # non-rectangular shape exists. Instead, apply per-node after
        # all declarations.
        for path in _find_3d_compatible_node_paths(d2_source):
            epilogue.append(f'{path}.style.3d: true')
    if animated:
        preamble.append('(** -> **)[*].style.animated: true')

    if not preamble and not epilogue:
        return d2_source

    parts: list[str] = []
    if preamble:
        parts.append('\n'.join(preamble))
    parts.append(d2_source)
    if epilogue:
        parts.append('\n'.join(epilogue))
    return '\n\n'.join(parts)


def _resolve_font_family(font_family: str) -> dict[str, str] | None:
    """Resolve a font family name to TTF file paths on the system.

    Searches platform-appropriate font directories for TTF files matching
    the requested font family. Returns partial results if only some
    variants are found (D2 falls back to Source Sans Pro for missing ones).

    Args:
        font_family: Font family key from FONT_FAMILIES registry.

    Returns:
        Dict mapping variant names ('regular', 'bold', 'italic', 'semibold')
        to absolute TTF file paths, or None if the family is unknown or no
        variant files were found.
    """
    family_key = font_family.lower().strip()
    if family_key not in FONT_FAMILIES:
        return None

    variants = FONT_FAMILIES[family_key]
    # Check bundled fonts directory first, then system font directories
    search_dirs = [BUNDLED_FONTS_DIR] + get_font_search_dirs()
    resolved: dict[str, str] = {}

    for variant, candidate_filenames in variants.items():
        for font_dir in search_dirs:
            for candidate in candidate_filenames:
                full_path = os.path.join(font_dir, candidate)
                if os.path.isfile(full_path):
                    resolved[variant] = full_path
                    break
            if variant in resolved:
                break

    return resolved if resolved else None


async def render_d2(
    d2_source: str,
    output_dir: str,
    filename: str = 'diagram',
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    theme: int | None = None,
    layout: str = DEFAULT_LAYOUT_ENGINE,
    sketch: bool = False,
    animate_interval: int | None = None,
    shadow: bool = False,
    three_d: bool = False,
    animated: bool = False,
    font_family: str | None = None,
    pad: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    workspace_dir: str | None = None,
) -> D2RenderResult:
    """Render D2 source to an image using the D2 CLI.

    Writes the D2 source to a .d2 file, then invokes the D2 binary to render it.
    Uses asyncio.create_subprocess_exec (no shell=True) to prevent injection.

    Args:
        d2_source: D2 DSL source code.
        output_dir: Directory for output files (fallback if workspace_dir not set).
        filename: Output filename without extension.
        output_format: Output format ('svg', 'png', 'pdf').
        theme: D2 theme ID (None for default).
        layout: Layout engine ('dagre' or 'elk').
        sketch: Whether to use hand-drawn mode.
        animate_interval: Milliseconds between animation frames (SVG only).
        shadow: Apply drop shadow to all shapes via glob.
        three_d: Apply 3D effect to rectangular shapes via glob.
        animated: Apply animated dashes to all connections via glob.
        font_family: Font family name from FONT_FAMILIES registry (auto-detected from system).
        pad: Padding in pixels around the diagram (D2 default is 100).
        timeout: Maximum render time in seconds.
        workspace_dir: User workspace directory; output goes to generated-diagrams/ subdirectory.

    Returns:
        D2RenderResult with status, file paths, and any error messages.
    """
    # Determine output directory
    if workspace_dir:
        final_output_dir = os.path.join(workspace_dir, OUTPUT_SUBDIRECTORY)
    else:
        final_output_dir = output_dir

    os.makedirs(final_output_dir, exist_ok=True)

    # File paths
    source_path = os.path.join(final_output_dir, f'{filename}.d2')
    image_path = os.path.join(final_output_dir, f'{filename}.{output_format}')

    # Inject global style globs if any flags are set
    d2_source = _inject_global_styles(d2_source, shadow=shadow, three_d=three_d, animated=animated)

    # Write D2 source file
    try:
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(d2_source)
    except OSError as e:
        return D2RenderResult(
            success=False,
            message=f'Failed to write D2 source file: {e}',
        )

    # Find D2 binary
    d2_path = shutil.which('d2')
    if d2_path is None:
        return D2RenderResult(
            success=False,
            source_path=source_path,
            message=(
                'D2 is not installed. Install it from https://d2lang.com/releases '
                'or via: curl -fsSL https://d2lang.com/install.sh | sh'
            ),
        )

    # Build CLI args — no shell=True, prevents injection
    args: list[str] = [d2_path]

    if theme is not None:
        args.extend(['--theme', str(theme)])

    if layout:
        args.extend(['--layout', layout])

    if sketch:
        args.append('--sketch')

    if animate_interval is not None and output_format == 'svg':
        args.extend(['--animate-interval', str(animate_interval)])

    if pad is not None:
        args.extend(['--pad', str(pad)])

    # Resolve and inject font flags (skip in sketch mode — D2 uses its own hand-drawn fonts)
    if font_family and not sketch:
        font_paths = _resolve_font_family(font_family)
        if font_paths:
            # D2 uses separate fonts for regular (container titles), bold (node labels),
            # italic (connection labels), and semibold. If a variant is missing, fill it
            # with the regular font so all text uses the custom font instead of falling
            # back to Source Sans Pro.
            base_font = font_paths.get('regular', next(iter(font_paths.values())))
            font_flag_map = {
                'regular': '--font-regular',
                'bold': '--font-bold',
                'italic': '--font-italic',
                'semibold': '--font-semibold',
            }
            for variant, flag in font_flag_map.items():
                args.extend([flag, font_paths.get(variant, base_font)])
        else:
            logger.warning(f'Font family "{font_family}" not found on system, using default')

    # Input and output paths
    args.append(source_path)
    args.append(image_path)

    # Execute D2 CLI
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_data, stderr_data = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        stderr_text = stderr_data.decode().strip() if stderr_data else None
        stdout_text = stdout_data.decode().strip() if stdout_data else None

        if proc.returncode == 0:
            message = f'Diagram rendered successfully: {image_path}'
            if stderr_text:
                message += f' (warnings: {stderr_text})'
            return D2RenderResult(
                success=True,
                image_path=image_path,
                source_path=source_path,
                stderr=stderr_text or None,
                message=message,
            )
        else:
            error_msg = stderr_text or stdout_text or 'Unknown D2 error'
            return D2RenderResult(
                success=False,
                source_path=source_path,
                stderr=error_msg,
                message=f'D2 rendering failed: {error_msg}',
            )

    except asyncio.TimeoutError:
        return D2RenderResult(
            success=False,
            source_path=source_path,
            message=f'D2 rendering timed out after {timeout} seconds',
        )
    except FileNotFoundError:
        return D2RenderResult(
            success=False,
            source_path=source_path,
            message='D2 binary not found at expected path',
        )
    except Exception as e:
        return D2RenderResult(
            success=False,
            source_path=source_path,
            message=f'Unexpected error during D2 rendering: {e}',
        )
