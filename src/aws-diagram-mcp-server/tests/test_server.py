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

"""Tests for the MCP server tools.

When calling MCP tool functions directly (outside the MCP framework), Pydantic
Field() defaults resolve to FieldInfo objects rather than actual values. All
tests must therefore pass every parameter explicitly.
"""

import pytest
import tempfile
from awslabs.aws_diagram_mcp_server.consts import (
    DEFAULT_ANIMATE_INTERVAL,
    DEFAULT_LAYOUT_ENGINE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TIMEOUT,
)
from awslabs.aws_diagram_mcp_server.models import D2RenderResult
from awslabs.aws_diagram_mcp_server.server import (
    mcp_generate_diagram,
    mcp_generate_scenario,
    mcp_get_diagram_examples,
    mcp_get_scenario_examples,
    mcp_list_aws_icons,
)
from unittest.mock import patch


# Default kwargs to pass when calling tool functions directly (avoids FieldInfo issues)
_GEN_DEFAULTS = {
    'output_format': DEFAULT_OUTPUT_FORMAT,
    'theme': None,
    'layout': DEFAULT_LAYOUT_ENGINE,
    'sketch': False,
    'shadow': False,
    'three_d': False,
    'animated': False,
    'font_family': None,
    'filename': None,
    'timeout': DEFAULT_TIMEOUT,
    'workspace_dir': None,
}

_SCENARIO_DEFAULTS = {
    'title': None,
    'title_position': 'top-center',
    'description': None,
    'description_position': 'center-right',
    'theme': None,
    'layout': DEFAULT_LAYOUT_ENGINE,
    'sketch': False,
    'shadow': False,
    'three_d': False,
    'animate_interval': DEFAULT_ANIMATE_INTERVAL,
    'font_family': None,
    'filename': None,
    'timeout': DEFAULT_TIMEOUT,
    'workspace_dir': None,
}

# Minimal valid D2 source with a scenarios: block
_SCENARIO_SOURCE = """\
a: Node A
b: Node B
a -> b: connection

scenarios: {
  highlight_a: {
    a.style.stroke: "#FF9900"
  }
}
"""


class TestGenerateDiagram:
    """Tests for the generate-diagram tool."""

    @pytest.mark.asyncio
    async def test_generate_diagram_success(self, mock_icons_available):
        """Test successful diagram generation."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ):
            result = await mcp_generate_diagram(
                d2_source='a -> b: connection',
                **{**_GEN_DEFAULTS, 'filename': 'test'},
            )
            assert result['status'] == 'success'
            assert result['image_path'] == '/tmp/test.svg'
            assert result['source_path'] == '/tmp/test.d2'

    @pytest.mark.asyncio
    async def test_generate_diagram_validation_error(self):
        """Test that empty source fails validation."""
        result = await mcp_generate_diagram(d2_source='', **_GEN_DEFAULTS)
        assert result['status'] == 'error'
        assert 'validation' in result['message'].lower()

    @pytest.mark.asyncio
    async def test_generate_diagram_no_declarations(self):
        """Test that source without declarations fails validation."""
        result = await mcp_generate_diagram(d2_source='random text here', **_GEN_DEFAULTS)
        assert result['status'] == 'error'

    @pytest.mark.asyncio
    async def test_generate_diagram_render_error(self, mock_icons_available):
        """Test handling of D2 render errors."""
        render_result = D2RenderResult(
            success=False,
            source_path='/tmp/test.d2',
            stderr='syntax error',
            message='D2 rendering failed: syntax error',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ):
            result = await mcp_generate_diagram(d2_source='a -> b', **_GEN_DEFAULTS)
            assert result['status'] == 'error'

    @pytest.mark.asyncio
    async def test_generate_diagram_with_workspace_dir(self, mock_icons_available):
        """Test generating with workspace_dir."""
        render_result = D2RenderResult(
            success=True,
            image_path='/workspace/generated-diagrams/test.svg',
            source_path='/workspace/generated-diagrams/test.d2',
            message='Rendered successfully',
        )

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                'awslabs.aws_diagram_mcp_server.server.render_d2',
                return_value=render_result,
            ),
        ):
            result = await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'workspace_dir': tmpdir},
            )
            assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_generate_diagram_invalid_format_defaults_to_svg(self, mock_icons_available):
        """Test that invalid format falls back to svg."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'output_format': 'invalid'},
            )
            # Should have been corrected to 'svg'
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['output_format'] == 'svg'

    @pytest.mark.asyncio
    async def test_generate_diagram_icon_failure_continues(self):
        """Test that icon resolution failure still renders."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with (
            patch(
                'awslabs.aws_diagram_mcp_server.server.ensure_icons_available',
                side_effect=RuntimeError('download failed'),
            ),
            patch(
                'awslabs.aws_diagram_mcp_server.server.render_d2',
                return_value=render_result,
            ),
        ):
            result = await mcp_generate_diagram(d2_source='a -> b', **_GEN_DEFAULTS)
            assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_generate_diagram_passes_none_animate_interval(self, mock_icons_available):
        """Test that generate-diagram always passes animate_interval=None to renderer."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            result = await mcp_generate_diagram(
                d2_source='a -> b: connection',
                **_GEN_DEFAULTS,
            )
            assert result['status'] == 'success'
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['animate_interval'] is None

    @pytest.mark.asyncio
    async def test_generate_diagram_with_shadow(self, mock_icons_available):
        """Test generating with shadow global style."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            result = await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'shadow': True},
            )
            assert result['status'] == 'success'
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['shadow'] is True

    @pytest.mark.asyncio
    async def test_generate_diagram_with_three_d(self, mock_icons_available):
        """Test generating with 3D global style."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            result = await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'three_d': True},
            )
            assert result['status'] == 'success'
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['three_d'] is True

    @pytest.mark.asyncio
    async def test_generate_diagram_with_animated_connections(self, mock_icons_available):
        """Test generating with animated connections global style."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            result = await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'animated': True},
            )
            assert result['status'] == 'success'
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['animated'] is True

    @pytest.mark.asyncio
    async def test_generate_diagram_with_font_family(self, mock_icons_available):
        """Test generating with font_family parameter."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            result = await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'font_family': 'amazon-ember'},
            )
            assert result['status'] == 'success'
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['font_family'] == 'amazon-ember'

    @pytest.mark.asyncio
    async def test_generate_diagram_timeout_clamping(self, mock_icons_available):
        """Test that timeout is clamped to valid range."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_diagram(
                d2_source='a -> b',
                **{**_GEN_DEFAULTS, 'timeout': 9999},
            )
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['timeout'] <= 300


class TestGetDiagramExamples:
    """Tests for the get-diagram-examples tool."""

    @pytest.mark.asyncio
    async def test_get_all_examples(self):
        """Test getting all examples."""
        result = await mcp_get_diagram_examples(category='all')
        assert 'examples' in result
        assert len(result['examples']) > 0

    @pytest.mark.asyncio
    async def test_get_aws_examples(self):
        """Test filtering by aws category."""
        result = await mcp_get_diagram_examples(category='aws')
        assert 'examples' in result
        for ex in result['examples'].values():
            assert ex['category'] == 'aws'

    @pytest.mark.asyncio
    async def test_get_genai_examples(self):
        """Test filtering by genai category."""
        result = await mcp_get_diagram_examples(category='genai')
        assert 'examples' in result
        assert len(result['examples']) > 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_category(self):
        """Test that nonexistent category returns empty examples."""
        result = await mcp_get_diagram_examples(category='nonexistent')
        assert 'examples' in result
        assert len(result['examples']) == 0


class TestListAwsIcons:
    """Tests for the list-aws-icons tool."""

    @pytest.mark.asyncio
    async def test_list_all_icons(self, mock_icons_available):
        """Test listing all icons."""
        result = await mcp_list_aws_icons(category_filter=None, search=None)
        assert 'categories' in result
        assert result['total_count'] > 0
        assert result['filtered'] is False

    @pytest.mark.asyncio
    async def test_list_icons_with_category_filter(self, mock_icons_available):
        """Test listing icons with category filter."""
        result = await mcp_list_aws_icons(category_filter='Compute', search=None)
        assert 'categories' in result
        assert result['filtered'] is True

    @pytest.mark.asyncio
    async def test_list_icons_with_search(self, mock_icons_available):
        """Test listing icons with search term."""
        result = await mcp_list_aws_icons(category_filter=None, search='EC2')
        assert 'categories' in result
        assert result['filtered'] is True
        assert result['total_count'] > 0

    @pytest.mark.asyncio
    async def test_list_icons_load_failure(self):
        """Test handling of icon load failure."""
        with patch(
            'awslabs.aws_diagram_mcp_server.server.ensure_icons_available',
            side_effect=RuntimeError('download failed'),
        ):
            result = await mcp_list_aws_icons(category_filter=None, search=None)
            assert result['total_count'] == 0
            assert len(result['categories']) == 0

    @pytest.mark.asyncio
    async def test_list_icons_combined_filters(self, mock_icons_available):
        """Test listing icons with both category and search filters."""
        result = await mcp_list_aws_icons(category_filter='Compute', search='Lambda')
        assert 'categories' in result
        assert result['filtered'] is True


class TestGenerateScenario:
    """Tests for the generate-scenario tool."""

    @pytest.mark.asyncio
    async def test_generate_scenario_success(self, mock_icons_available):
        """Test successful scenario generation."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ):
            result = await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **{**_SCENARIO_DEFAULTS, 'filename': 'test'},
            )
            assert result['status'] == 'success'
            assert result['image_path'] == '/tmp/test.svg'

    @pytest.mark.asyncio
    async def test_generate_scenario_missing_scenarios_block(self):
        """Test that source without scenarios: block returns error."""
        result = await mcp_generate_scenario(
            d2_source='a -> b: connection',
            **_SCENARIO_DEFAULTS,
        )
        assert result['status'] == 'error'
        assert 'scenarios:' in result['message']

    @pytest.mark.asyncio
    async def test_generate_scenario_with_title(self, mock_icons_available):
        """Test that title is injected into D2 source."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **{**_SCENARIO_DEFAULTS, 'title': 'My Scenario'},
            )
            call_kwargs = mock_render.call_args[1]
            assert 'title: My Scenario' in call_kwargs['d2_source']
            assert 'near: top-center' in call_kwargs['d2_source']

    @pytest.mark.asyncio
    async def test_generate_scenario_with_description(self, mock_icons_available):
        """Test that description is injected as markdown explanation block."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **{**_SCENARIO_DEFAULTS, 'description': 'Step 1: do something'},
            )
            call_kwargs = mock_render.call_args[1]
            assert 'explanation: |md' in call_kwargs['d2_source']
            assert 'Step 1: do something' in call_kwargs['d2_source']
            assert 'near: center-right' in call_kwargs['d2_source']

    @pytest.mark.asyncio
    async def test_generate_scenario_invalid_title_position(self):
        """Test that invalid title_position returns error."""
        result = await mcp_generate_scenario(
            d2_source=_SCENARIO_SOURCE,
            **{**_SCENARIO_DEFAULTS, 'title_position': 'invalid-position'},
        )
        assert result['status'] == 'error'
        assert 'title_position' in result['message']

    @pytest.mark.asyncio
    async def test_generate_scenario_invalid_description_position(self):
        """Test that invalid description_position returns error."""
        result = await mcp_generate_scenario(
            d2_source=_SCENARIO_SOURCE,
            **{**_SCENARIO_DEFAULTS, 'description_position': 'nowhere'},
        )
        assert result['status'] == 'error'
        assert 'description_position' in result['message']

    @pytest.mark.asyncio
    async def test_generate_scenario_forces_svg(self, mock_icons_available):
        """Test that scenario renders always use SVG output format."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **_SCENARIO_DEFAULTS,
            )
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['output_format'] == 'svg'

    @pytest.mark.asyncio
    async def test_generate_scenario_passes_animate_interval(self, mock_icons_available):
        """Test that animate_interval is passed to renderer."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **{**_SCENARIO_DEFAULTS, 'animate_interval': 2000},
            )
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['animate_interval'] == 2000

    @pytest.mark.asyncio
    async def test_generate_scenario_highlight_color_default(self, mock_icons_available):
        """Test that default highlight color (AWS orange) is injected."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **_SCENARIO_DEFAULTS,
            )
            call_kwargs = mock_render.call_args[1]
            assert 'highlight: "#FF9900"' in call_kwargs['d2_source']

    @pytest.mark.asyncio
    async def test_generate_scenario_highlight_color_terminal_theme(self, mock_icons_available):
        """Test that Terminal theme uses green highlight."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **{**_SCENARIO_DEFAULTS, 'theme': 300},
            )
            call_kwargs = mock_render.call_args[1]
            assert 'highlight: "#00FF41"' in call_kwargs['d2_source']

    @pytest.mark.asyncio
    async def test_generate_scenario_skips_duplicate_vars(self, mock_icons_available):
        """Test that vars block is not injected if user already has one."""
        source_with_vars = 'vars: {\n  custom: "value"\n}\n\n' + _SCENARIO_SOURCE
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=source_with_vars,
                **_SCENARIO_DEFAULTS,
            )
            call_kwargs = mock_render.call_args[1]
            # Should not have double vars blocks
            assert call_kwargs['d2_source'].count('vars:') == 1

    @pytest.mark.asyncio
    async def test_generate_scenario_passes_pad(self, mock_icons_available):
        """Test that scenario renders pass extra padding to D2 CLI."""
        render_result = D2RenderResult(
            success=True,
            image_path='/tmp/test.svg',
            source_path='/tmp/test.d2',
            message='Rendered successfully',
        )

        with patch(
            'awslabs.aws_diagram_mcp_server.server.render_d2',
            return_value=render_result,
        ) as mock_render:
            await mcp_generate_scenario(
                d2_source=_SCENARIO_SOURCE,
                **_SCENARIO_DEFAULTS,
            )
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs['pad'] == 200  # DEFAULT_SCENARIO_PAD

    async def test_generate_scenario_validation_error(self):
        """Test that empty source fails validation."""
        result = await mcp_generate_scenario(d2_source='', **_SCENARIO_DEFAULTS)
        assert result['status'] == 'error'
        assert 'validation' in result['message'].lower()


class TestGetScenarioExamples:
    """Tests for the get-scenario-examples tool."""

    @pytest.mark.asyncio
    async def test_get_scenario_examples_not_empty(self):
        """Test that scenario examples are returned."""
        result = await mcp_get_scenario_examples()
        assert 'examples' in result
        assert len(result['examples']) > 0

    @pytest.mark.asyncio
    async def test_get_scenario_examples_contain_scenarios_block(self):
        """Test that all returned examples contain scenarios: in D2 source."""
        result = await mcp_get_scenario_examples()
        for name, ex in result['examples'].items():
            assert 'scenarios:' in ex['d2_source'], f'Example {name} missing scenarios: block'


class TestServerIntegration:
    """Integration tests for the server module."""

    @pytest.mark.asyncio
    async def test_server_tool_registration(self):
        """Test that the server tools are registered correctly."""
        assert hasattr(mcp_generate_diagram, '__name__')
        assert hasattr(mcp_generate_scenario, '__name__')
        assert hasattr(mcp_get_diagram_examples, '__name__')
        assert hasattr(mcp_get_scenario_examples, '__name__')
        assert hasattr(mcp_list_aws_icons, '__name__')

    @pytest.mark.asyncio
    async def test_generate_diagram_docstring(self):
        """Test that generate-diagram has proper documentation."""
        assert mcp_generate_diagram.__doc__ is not None
        assert 'D2' in mcp_generate_diagram.__doc__

    @pytest.mark.asyncio
    async def test_generate_scenario_docstring(self):
        """Test that generate-scenario has proper documentation."""
        assert mcp_generate_scenario.__doc__ is not None
        assert 'scenario' in mcp_generate_scenario.__doc__.lower()

    @pytest.mark.asyncio
    async def test_get_examples_docstring(self):
        """Test that get-diagram-examples has proper documentation."""
        assert mcp_get_diagram_examples.__doc__ is not None
        assert 'examples' in mcp_get_diagram_examples.__doc__.lower()

    @pytest.mark.asyncio
    async def test_get_scenario_examples_docstring(self):
        """Test that get-scenario-examples has proper documentation."""
        assert mcp_get_scenario_examples.__doc__ is not None
        assert 'scenario' in mcp_get_scenario_examples.__doc__.lower()

    @pytest.mark.asyncio
    async def test_list_icons_docstring(self):
        """Test that list-aws-icons has proper documentation."""
        assert mcp_list_aws_icons.__doc__ is not None
        assert 'icon' in mcp_list_aws_icons.__doc__.lower()
