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

import tempfile
import uuid
from awslabs.aws_diagram_mcp_server.consts import (
    DEFAULT_LAYOUT_ENGINE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TIMEOUT,
    MAX_TIMEOUT,
    MIN_TIMEOUT,
    THEME_TOOLTIP,
)
from awslabs.aws_diagram_mcp_server.d2_renderer import render_d2
from awslabs.aws_diagram_mcp_server.d2_validator import validate_d2_source
from awslabs.aws_diagram_mcp_server.examples import get_examples
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
   - Use animation (steps: blocks) for animated SVG output
   - Both .d2 source and output image are saved for later modification

D2 LANGUAGE BASICS:
- Nodes: `mynode: My Label`
- Connections: `a -> b: label`
- Containers: `vpc: { subnet: { ec2: Instance } }`
- Icons: `ec2.icon: ${ICON:Amazon-EC2}`
- Styles: `ec2.style.stroke: "#FF9900"`
- Direction: `direction: right` (right, down, left, up)
- Shapes: `shape: person`, `shape: cloud`, `shape: diamond`

SUPPORTED FEATURES:
- AWS architecture diagrams with official icons
- GenAI/Bedrock architecture patterns
- Serverless, containers, networking, security patterns
- Hand-drawn sketch mode
- Dark/light themes (15+ built-in themes)
- Animated SVG diagrams with steps
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
        description='D2 DSL source code. Use declarative syntax like "a -> b: label" and ${ICON:Name} placeholders for AWS icons.',
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
        description='Enable hand-drawn sketch mode.',
    ),
    animate_interval: Optional[int] = Field(
        default=None,
        description='Milliseconds between animation frames (SVG only, for scenarios: or steps: blocks).',
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
        description='Apply animated dashes to all connections (injects connection animated glob).',
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
        resolved_source = d2_source

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
        animate_interval=animate_interval,
        shadow=shadow,
        three_d=three_d,
        animated=animated,
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


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
