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

"""aws-diagram-mcp-server implementation.

This server provides tools to generate diagrams using D2, a modern declarative
diagramming language. It accepts D2 DSL source code and renders SVG/PNG/PDF
output via the D2 CLI binary.
"""

import re
import tempfile
import uuid
from awslabs.aws_diagram_mcp_server.consts import (
    DEFAULT_ANIMATE_INTERVAL,
    DEFAULT_LAYOUT_ENGINE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SCENARIO_PAD,
    DEFAULT_TIMEOUT,
    MAX_TIMEOUT,
    MIN_TIMEOUT,
    THEME_TOOLTIP,
    VALID_NEAR_POSITIONS,
    get_highlight_for_theme,
)
from awslabs.aws_diagram_mcp_server.d2_renderer import render_d2
from awslabs.aws_diagram_mcp_server.d2_validator import validate_d2_source
from awslabs.aws_diagram_mcp_server.examples import get_examples, get_scenario_examples
from awslabs.aws_diagram_mcp_server.icons import (
    build_icon_index,
    ensure_icons_available,
    find_icons,
    resolve_icon_placeholders,
)
from awslabs.aws_diagram_mcp_server.models import (
    AwsIconsResponse,
    DiagramExampleResponse,
    DiagramGenerateResponse,
)
from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Optional


# Create the MCP server
mcp = FastMCP(
    'aws-diagram-mcp-server',
    dependencies=[
        'pydantic',
        'loguru',
        'httpx',
    ],
    log_level='ERROR',
    instructions="""Use this server to generate professional architecture diagrams using D2, a modern declarative diagramming language.

WORKFLOW:
1. list-aws-icons:
   - Discover available AWS Architecture Icons (official SVG icons)
   - Browse by category (Compute, Database, Machine-Learning, etc.)
   - Search by name (Lambda, EC2, Bedrock, etc.)
   - Icons are automatically downloaded and cached on first use

2. get-diagram-examples:
   - Get ready-to-use D2 code examples by category
   - Categories: aws, genai, serverless, containers, data, networking, security, animation
   - Examples include ${ICON:Name} placeholders that are resolved to real icon paths
   - Study examples to learn D2 syntax and patterns

3. generate-diagram:
   - Write D2 DSL code (declarative, not Python — no imports needed)
   - Use ${ICON:Name} placeholders for AWS icons (resolved automatically)
   - Choose output format: svg (default), png, or pdf
   - Choose theme, layout engine (dagre/elk), sketch mode
   - Use animated=True for animated dashes on ALL connections
   - NOTE: steps: and layers: blocks are NOT supported. For animated
     multi-frame diagrams, use generate-scenario instead.
   - Both .d2 source and output image are saved for later modification

4. get-scenario-examples:
   - Get D2 examples that use scenarios: blocks for animated multi-frame diagrams
   - Study these before using generate-scenario

5. generate-scenario:
   - Generate animated scenario diagrams with automatic SVG output
   - D2 source MUST contain a scenarios: {} block
   - Provide title and description as parameters (auto-injected into D2 source)
   - Highlight color is auto-selected based on theme for good contrast
   - Title, explanation, and vars blocks are injected — do NOT include them in D2 source

D2 LANGUAGE BASICS:
- Nodes: `mynode: My Label`
- Connections: `a -> b: label`
- Containers: `vpc: { subnet: { ec2: Instance } }`
- Icons: `ec2.icon: ${ICON:Amazon-EC2}`
- Styles: `ec2.style.stroke: "#FF9900"`
- Direction: `direction: right` (right, down, left, up)
- Shapes: `shape: person`, `shape: cloud`, `shape: diamond`

D2 SCENARIOS (animated multi-path diagrams):
- Use generate-scenario tool (not generate-diagram)
- Define ALL nodes and connections in the base diagram first
- Add a scenarios: {} block with named scenario sub-blocks
- Inside scenarios, ONLY modify styles — never use "a -> b" (creates new arrows)
- Use connection references to style existing connections:
  (source -> target)[0].style.animated: true
  (source -> target)[0].style.stroke: "${highlight}"
  (source -> target)[0].label: new label
- Highlight active nodes: node.style.stroke: "${highlight}"
- Dim inactive nodes: node.style.opacity: 0.3
- Place explanation with near: center-right (most reliable — renders as side legend)
- Left-side and bottom positions may clip large descriptions (D2 layout limitation)
- Keep descriptions concise (3-5 items) — height is bounded by diagram height
- See get-scenario-examples for the complete pattern

ANIMATED CONNECTIONS (two approaches):
1. animated=True flag on generate-diagram: applies animated dashes to ALL connections
   globally via a glob. Simple, but all-or-nothing.
2. Inline style.animated: true on individual connections in D2 source: selective
   control — use when forward and return paths need different styles/colors.

SUPPORTED FEATURES:
- AWS architecture diagrams with official icons
- GenAI/Bedrock architecture patterns
- Serverless, containers, networking, security patterns
- Hand-drawn sketch mode
- Dark/light themes (15+ built-in themes)
- Animated SVG diagrams with scenarios (multi-frame) or animated connections
- ELK and dagre layout engines
- SVG, PNG, and PDF output

IMPORTANT:
- D2 must be installed on the system (https://d2lang.com/releases)
- Always provide workspace_dir to save diagrams in the user's project
- The .d2 source file is always saved alongside the output for future edits
- Use get-diagram-examples first to understand D2 syntax""",
)


@mcp.tool(name='generate-diagram')
async def mcp_generate_diagram(
    d2_source: str = Field(
        ...,
        description=(
            'D2 DSL source code. Use declarative syntax like "a -> b: label" '
            'and ${ICON:Name} placeholders for AWS icons. '
            'NOTE: steps: and layers: blocks are not supported. '
            'For animated scenario diagrams, use generate-scenario instead.'
        ),
    ),
    output_format: str = Field(
        default=DEFAULT_OUTPUT_FORMAT,
        description='Output format: "svg" (default), "png", or "pdf".',
    ),
    theme: Optional[int] = Field(
        default=None,
        description=THEME_TOOLTIP,
    ),
    layout: str = Field(
        default=DEFAULT_LAYOUT_ENGINE,
        description='Layout engine: "dagre" (default) or "elk".',
    ),
    sketch: bool = Field(
        default=False,
        description='Enable hand-drawn sketch mode. Overrides font_family (D2 uses its own hand-drawn fonts).',
    ),
    shadow: bool = Field(
        default=False,
        description='Apply drop shadow to all shapes (injects **.style.shadow: true glob).',
    ),
    three_d: bool = Field(
        default=False,
        description=(
            'Apply 3D effect to all rectangular/square/hexagon shapes. '
            'Non-compatible shapes (person, cloud, etc.) are auto-excluded.'
        ),
    ),
    animated: bool = Field(
        default=False,
        description=(
            'Apply animated dashes to ALL connections via a global glob. '
            'For selective animation, use inline style.animated: true on '
            'individual connections in D2 source instead.'
        ),
    ),
    font_family: Optional[str] = Field(
        default=None,
        description=(
            'Font family for diagram text. Options: '
            '"amazon-ember" (Amazon brand, must be installed on system), '
            '"exo-2" (futuristic/technical geometric — bundled), '
            '"bitcount" (retro pixel/bitmap style — bundled), '
            '"caveat" (casual handwriting — bundled). '
            'None uses D2 default (Source Sans Pro). '
            'Ignored when sketch=True.'
        ),
    ),
    filename: Optional[str] = Field(
        default=None,
        description='Output filename without extension. Auto-generated if not provided.',
    ),
    timeout: int = Field(
        default=DEFAULT_TIMEOUT,
        description=f'Maximum render time in seconds ({MIN_TIMEOUT}-{MAX_TIMEOUT}).',
    ),
    workspace_dir: Optional[str] = Field(
        default=None,
        description="User's workspace directory. Output saved to generated-diagrams/ subdirectory.",
    ),
) -> dict:
    """Generate a diagram from D2 DSL source code.

    Renders D2 source to SVG/PNG/PDF using the D2 CLI. Saves both the .d2
    source file and the rendered output for later modification.

    D2 is a declarative diagramming language — no Python imports needed.
    Use ${ICON:Name} placeholders for AWS Architecture Icons.

    NOTE: For animated scenario diagrams (scenarios: blocks), use the
    generate-scenario tool instead. steps: and layers: are not supported.

    Returns:
        Dictionary with status, image_path, source_path, and message.
    """
    # Clamp timeout
    timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))

    # Validate D2 source
    validation = validate_d2_source(d2_source)
    if not validation.valid:
        return DiagramGenerateResponse(
            status='error',
            message=f'D2 validation failed: {"; ".join(validation.errors)}',
        ).model_dump()

    # Resolve icon placeholders
    try:
        icons_dir = ensure_icons_available()
        icon_index = build_icon_index(icons_dir)
        resolved_source = resolve_icon_placeholders(d2_source, icon_index)
    except Exception as e:
        logger.warning(f'Icon resolution failed (continuing without icons): {e}')
        # Strip all ${ICON:...} placeholders and empty icon: lines
        resolved_source = re.sub(r'\$\{ICON:[^}]+\}', '', d2_source)
        resolved_source = re.sub(r'^[ \t]*icon:\s*$', '', resolved_source, flags=re.MULTILINE)

    # Generate filename if not provided
    if not filename:
        filename = f'diagram-{uuid.uuid4().hex[:8]}'

    # Determine output directory
    output_dir = workspace_dir if workspace_dir else tempfile.gettempdir()

    # Validate output format
    if output_format not in ('svg', 'png', 'pdf'):
        output_format = DEFAULT_OUTPUT_FORMAT

    # Render
    result = await render_d2(
        d2_source=resolved_source,
        output_dir=output_dir,
        filename=filename,
        output_format=output_format,
        theme=theme,
        layout=layout,
        sketch=sketch,
        animate_interval=None,
        shadow=shadow,
        three_d=three_d,
        animated=animated,
        font_family=font_family,
        timeout=timeout,
        workspace_dir=workspace_dir,
    )

    return DiagramGenerateResponse(
        status='success' if result.success else 'error',
        image_path=result.image_path,
        source_path=result.source_path,
        message=result.message,
    ).model_dump()


@mcp.tool(name='get-diagram-examples')
async def mcp_get_diagram_examples(
    category: str = Field(
        default='all',
        description='Example category: aws, genai, serverless, containers, data, networking, security, animation, or all.',
    ),
) -> dict:
    """Get D2 diagram examples by category.

    Returns ready-to-use D2 code examples with ${ICON:Name} placeholders
    for AWS icons. Use these to learn D2 syntax and as templates.

    Available categories: aws, genai, serverless, containers, data,
    networking, security, animation.

    Returns:
        Dictionary with examples mapped by name, each containing title,
        description, d2_source, category, and uses_animation flag.
    """
    examples = get_examples(category)
    return DiagramExampleResponse(examples=examples).model_dump()


@mcp.tool(name='list-aws-icons')
async def mcp_list_aws_icons(
    category_filter: Optional[str] = Field(
        default=None,
        description='Filter by AWS category (e.g., "Compute", "Database", "Machine Learning").',
    ),
    search: Optional[str] = Field(
        default=None,
        description='Search by icon name (e.g., "Lambda", "EC2", "Bedrock").',
    ),
) -> dict:
    """List available AWS Architecture Icons.

    Downloads and caches the official AWS Architecture Icon package on first use.
    Returns icons organized by category with name, label, path, and category.

    Use icon paths in D2 source as: `node.icon: /path/to/icon.svg`
    Or use ${ICON:Name} placeholders in generate-diagram (resolved automatically).

    Returns:
        Dictionary with categories (icons grouped by AWS category),
        total_count, and filtered flag.
    """
    try:
        icons_dir = ensure_icons_available()
        icon_index = build_icon_index(icons_dir)
    except Exception as e:
        logger.error(f'Failed to load AWS icons: {e}')
        return AwsIconsResponse(
            categories={},
            total_count=0,
            filtered=False,
        ).model_dump()

    # Apply filters
    filtered = find_icons(icon_index, search=search, category=category_filter)
    is_filtered = search is not None or category_filter is not None

    total = sum(len(icons) for icons in filtered.values())

    return AwsIconsResponse(
        categories=filtered,
        total_count=total,
        filtered=is_filtered,
    ).model_dump()


def _build_scenario_preamble(
    highlight_color: str,
    title: str | None = None,
    title_position: str = 'top-center',
    description: str | None = None,
    description_position: str = 'center-right',
) -> str:
    """Build D2 preamble for scenario diagrams.

    Generates vars, title, and explanation blocks to prepend to the user's
    D2 source. The highlight color is referenced as ${highlight} in scenario
    style overrides.

    Args:
        highlight_color: Hex color for the vars.highlight variable.
        title: Optional diagram title text.
        title_position: D2 near: value for title placement.
        description: Optional markdown description text.
        description_position: D2 near: value for description placement.

    Returns:
        D2 source preamble string to prepend.
    """
    parts: list[str] = []

    parts.append(f'vars: {{\n  highlight: "{highlight_color}"\n}}')

    if title:
        parts.append(
            f'title: {title} {{\n'
            f'  near: {title_position}\n'
            f'  style.font-size: 24\n'
            f'  style.underline: true\n'
            f'}}'
        )

    if description:
        # Indent each line of the description by 2 spaces for D2 block scalar
        indented_lines = '\n'.join(f'  {line}' for line in description.splitlines())
        parts.append(
            f'explanation: |md\n{indented_lines}\n| {{\n  near: {description_position}\n}}'
        )

    return '\n\n'.join(parts)


@mcp.tool(name='generate-scenario')
async def mcp_generate_scenario(
    d2_source: str = Field(
        ...,
        description=(
            'D2 DSL source code that MUST contain a scenarios: {} block. '
            'Define all nodes and connections in the base diagram, then use '
            'scenarios to apply style overrides per frame. '
            'Do NOT include vars:, title:, or explanation: blocks — these '
            'are auto-injected from the title/description parameters. '
            'Use ${ICON:Name} placeholders for AWS icons.'
        ),
    ),
    title: Optional[str] = Field(
        default=None,
        description='Diagram title. Auto-injected as a D2 title node with underline styling.',
    ),
    title_position: str = Field(
        default='top-center',
        description=(
            'Position for the title. Valid: top-left, top-center, top-right, '
            'center-left, center-right, bottom-left, bottom-center, bottom-right.'
        ),
    ),
    description: Optional[str] = Field(
        default=None,
        description=(
            'Markdown description for the diagram explanation panel. '
            'Keep to 3-5 items — height is bounded by diagram height. '
            'Supports **bold**, *italic*, and numbered lists.'
        ),
    ),
    description_position: str = Field(
        default='center-right',
        description=(
            'Position for the description panel. Strongly recommended: center-right '
            '(renders as side legend in blank space). Left-side and bottom positions '
            'may clip large descriptions due to a D2 layout limitation. '
            'Valid: top-left, top-center, top-right, center-left, center-right, '
            'bottom-left, bottom-center, bottom-right.'
        ),
    ),
    theme: Optional[int] = Field(
        default=None,
        description=THEME_TOOLTIP,
    ),
    layout: str = Field(
        default=DEFAULT_LAYOUT_ENGINE,
        description='Layout engine: "dagre" (default) or "elk".',
    ),
    sketch: bool = Field(
        default=False,
        description='Enable hand-drawn sketch mode.',
    ),
    shadow: bool = Field(
        default=False,
        description='Apply drop shadow to all shapes.',
    ),
    three_d: bool = Field(
        default=False,
        description='Apply 3D effect to compatible shapes.',
    ),
    animate_interval: int = Field(
        default=DEFAULT_ANIMATE_INTERVAL,
        description=f'Milliseconds between scenario frames. Default: {DEFAULT_ANIMATE_INTERVAL}ms.',
    ),
    font_family: Optional[str] = Field(
        default=None,
        description=(
            'Font family for diagram text. Options: '
            '"amazon-ember", "exo-2", "bitcount", "caveat". '
            'None uses D2 default. Ignored when sketch=True.'
        ),
    ),
    filename: Optional[str] = Field(
        default=None,
        description='Output filename without extension. Auto-generated if not provided.',
    ),
    timeout: int = Field(
        default=DEFAULT_TIMEOUT,
        description=f'Maximum render time in seconds ({MIN_TIMEOUT}-{MAX_TIMEOUT}).',
    ),
    workspace_dir: Optional[str] = Field(
        default=None,
        description="User's workspace directory. Output saved to generated-diagrams/ subdirectory.",
    ),
) -> dict:
    """Generate an animated scenario diagram from D2 DSL source code.

    Renders D2 source containing a scenarios: block to animated SVG. Auto-injects
    title, description, and highlight color vars into the D2 source. The highlight
    color is chosen for good contrast with the selected theme.

    D2 source MUST contain a scenarios: {} block — use generate-diagram for
    static diagrams without scenarios.

    Returns:
        Dictionary with status, image_path, source_path, and message.
    """
    # Clamp timeout
    timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))

    # Validate D2 source
    validation = validate_d2_source(d2_source)
    if not validation.valid:
        return DiagramGenerateResponse(
            status='error',
            message=f'D2 validation failed: {"; ".join(validation.errors)}',
        ).model_dump()

    # Validate scenarios: block is present
    if 'scenarios:' not in d2_source:
        return DiagramGenerateResponse(
            status='error',
            message=(
                'D2 source must contain a scenarios: {} block. '
                'For static diagrams, use generate-diagram instead.'
            ),
        ).model_dump()

    # Validate positions
    if title_position not in VALID_NEAR_POSITIONS:
        return DiagramGenerateResponse(
            status='error',
            message=(
                f'Invalid title_position: "{title_position}". '
                f'Valid options: {", ".join(VALID_NEAR_POSITIONS)}'
            ),
        ).model_dump()

    if description_position not in VALID_NEAR_POSITIONS:
        return DiagramGenerateResponse(
            status='error',
            message=(
                f'Invalid description_position: "{description_position}". '
                f'Valid options: {", ".join(VALID_NEAR_POSITIONS)}'
            ),
        ).model_dump()

    # Resolve icon placeholders
    try:
        icons_dir = ensure_icons_available()
        icon_index = build_icon_index(icons_dir)
        resolved_source = resolve_icon_placeholders(d2_source, icon_index)
    except Exception as e:
        logger.warning(f'Icon resolution failed (continuing without icons): {e}')
        resolved_source = re.sub(r'\$\{ICON:[^}]+\}', '', d2_source)
        resolved_source = re.sub(r'^[ \t]*icon:\s*$', '', resolved_source, flags=re.MULTILINE)

    # Build and prepend scenario preamble (vars, title, explanation)
    # Skip injection if user already included these blocks
    highlight_color = get_highlight_for_theme(theme)
    inject_title = title if 'title:' not in d2_source else None
    inject_desc = description if 'explanation:' not in d2_source else None
    inject_vars = 'vars:' not in d2_source

    if inject_vars or inject_title or inject_desc:
        preamble = _build_scenario_preamble(
            highlight_color=highlight_color if inject_vars else '',
            title=inject_title,
            title_position=title_position,
            description=inject_desc,
            description_position=description_position,
        )
        if not inject_vars:
            # Remove the empty vars block if user already has one
            preamble = re.sub(r'vars: \{\n  highlight: ""\n\}\n*', '', preamble)
        resolved_source = f'{preamble}\n\n{resolved_source}'

    # Generate filename if not provided
    if not filename:
        filename = f'scenario-{uuid.uuid4().hex[:8]}'

    # Determine output directory
    output_dir = workspace_dir if workspace_dir else tempfile.gettempdir()

    # Render (always SVG for scenarios)
    result = await render_d2(
        d2_source=resolved_source,
        output_dir=output_dir,
        filename=filename,
        output_format='svg',
        theme=theme,
        layout=layout,
        sketch=sketch,
        animate_interval=animate_interval,
        shadow=shadow,
        three_d=three_d,
        animated=False,
        font_family=font_family,
        pad=DEFAULT_SCENARIO_PAD,
        timeout=timeout,
        workspace_dir=workspace_dir,
    )

    return DiagramGenerateResponse(
        status='success' if result.success else 'error',
        image_path=result.image_path,
        source_path=result.source_path,
        message=result.message,
    ).model_dump()


@mcp.tool(name='get-scenario-examples')
async def mcp_get_scenario_examples() -> dict:
    """Get D2 scenario diagram examples.

    Returns examples that use D2 scenarios: blocks for animated multi-frame
    diagrams. These demonstrate the pattern expected by generate-scenario:
    base diagram with all nodes/connections, then scenario blocks that apply
    style overrides per frame.

    Returns:
        Dictionary with examples mapped by name, each containing title,
        description, d2_source, category, and uses_animation flag.
    """
    examples = get_scenario_examples()
    return DiagramExampleResponse(examples=examples).model_dump()


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
