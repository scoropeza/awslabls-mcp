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

"""Tests for D2 renderer module."""

import asyncio
import os
import pytest
import tempfile
from awslabs.aws_diagram_mcp_server.d2_renderer import (
    _find_3d_compatible_node_paths,
    _inject_global_styles,
    _resolve_font_family,
    check_d2_installed,
    render_d2,
)
from unittest.mock import AsyncMock, patch


class TestCheckD2Installed:
    """Tests for check_d2_installed function."""

    @pytest.mark.asyncio
    async def test_d2_not_found(self):
        """Test when D2 is not installed."""
        with patch('awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which', return_value=None):
            result = await check_d2_installed()
            assert result is None

    @pytest.mark.asyncio
    async def test_d2_found(self):
        """Test when D2 is installed."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'v0.6.9\n', b''))

        with (
            patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                return_value='/usr/local/bin/d2',
            ),
            patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                return_value=mock_proc,
            ),
        ):
            result = await check_d2_installed()
            assert result is not None
            assert result.version == 'v0.6.9'
            assert result.path == '/usr/local/bin/d2'

    @pytest.mark.asyncio
    async def test_d2_version_fails(self):
        """Test when D2 is found but version command fails."""
        with (
            patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                return_value='/usr/local/bin/d2',
            ),
            patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                side_effect=OSError('exec failed'),
            ),
        ):
            result = await check_d2_installed()
            assert result is None


class TestRenderD2:
    """Tests for render_d2 function."""

    @pytest.mark.asyncio
    async def test_render_success(self):
        """Test successful D2 rendering."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    return_value=mock_proc,
                ),
            ):
                result = await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    filename='test_diagram',
                )
                assert result.success is True
                assert result.source_path is not None
                assert result.image_path is not None
                assert 'test_diagram.d2' in result.source_path
                assert 'test_diagram.svg' in result.image_path

                # Verify source file was written
                assert os.path.exists(result.source_path)
                with open(result.source_path, 'r') as f:
                    assert f.read() == 'a -> b'

    @pytest.mark.asyncio
    async def test_render_with_workspace_dir(self):
        """Test rendering with workspace_dir creates subdirectory."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    return_value=mock_proc,
                ),
            ):
                result = await render_d2(
                    d2_source='a -> b',
                    output_dir='/unused',
                    filename='test',
                    workspace_dir=tmpdir,
                )
                assert result.success is True
                assert 'generated-diagrams' in result.image_path

    @pytest.mark.asyncio
    async def test_render_with_theme(self):
        """Test that theme argument is passed to D2 CLI."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    theme=3,
                )
                # Verify --theme was passed
                call_args = create_mock.call_args[0]
                assert '--theme' in call_args
                assert '3' in call_args

    @pytest.mark.asyncio
    async def test_render_with_sketch(self):
        """Test that sketch flag is passed to D2 CLI."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    sketch=True,
                )
                call_args = create_mock.call_args[0]
                assert '--sketch' in call_args

    @pytest.mark.asyncio
    async def test_render_with_animation(self):
        """Test that animate-interval is passed for SVG output."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='steps: { step1: { a -> b } }',
                    output_dir=tmpdir,
                    output_format='svg',
                    animate_interval=1000,
                )
                call_args = create_mock.call_args[0]
                assert '--animate-interval' in call_args
                assert '1000' in call_args

    @pytest.mark.asyncio
    async def test_render_animation_ignored_for_png(self):
        """Test that animate-interval is NOT passed for non-SVG output."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    output_format='png',
                    animate_interval=1000,
                )
                call_args = create_mock.call_args[0]
                assert '--animate-interval' not in call_args

    @pytest.mark.asyncio
    async def test_render_with_pad(self):
        """Test that --pad flag is passed to D2 CLI when pad is set."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    pad=200,
                )
                call_args = create_mock.call_args[0]
                assert '--pad' in call_args
                assert '200' in call_args

    @pytest.mark.asyncio
    async def test_render_without_pad(self):
        """Test that --pad flag is NOT passed when pad is None."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                )
                call_args = create_mock.call_args[0]
                assert '--pad' not in call_args

    @pytest.mark.asyncio
    async def test_render_with_elk_layout(self):
        """Test that layout engine is passed to D2 CLI."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0
        create_mock = AsyncMock(return_value=mock_proc)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    create_mock,
                ),
            ):
                await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    layout='elk',
                )
                call_args = create_mock.call_args[0]
                assert '--layout' in call_args
                assert 'elk' in call_args

    @pytest.mark.asyncio
    async def test_render_d2_not_installed(self):
        """Test rendering when D2 is not installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                return_value=None,
            ):
                result = await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                )
                assert result.success is False
                assert 'not installed' in result.message.lower()
                # Source file should still be saved
                assert result.source_path is not None

    @pytest.mark.asyncio
    async def test_render_d2_error(self):
        """Test rendering when D2 CLI returns an error."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b'syntax error at line 3'))
        mock_proc.returncode = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    return_value=mock_proc,
                ),
            ):
                result = await render_d2(
                    d2_source='invalid{{{',
                    output_dir=tmpdir,
                )
                assert result.success is False
                assert 'syntax error' in result.message.lower()

    @pytest.mark.asyncio
    async def test_render_timeout(self):
        """Test rendering timeout handling."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    return_value=mock_proc,
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.wait_for',
                    side_effect=asyncio.TimeoutError(),
                ),
            ):
                result = await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    timeout=1,
                )
                assert result.success is False
                assert 'timed out' in result.message.lower()

    @pytest.mark.asyncio
    async def test_render_png_format(self):
        """Test rendering with PNG output format."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b''))
        mock_proc.returncode = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    return_value=mock_proc,
                ),
            ):
                result = await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                    filename='test',
                    output_format='png',
                )
                assert result.success is True
                assert result.image_path.endswith('.png')

    @pytest.mark.asyncio
    async def test_render_with_stderr_warnings(self):
        """Test that stderr warnings are captured on success."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b'', b'warning: unused node "x"'))
        mock_proc.returncode = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.shutil.which',
                    return_value='/usr/local/bin/d2',
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.d2_renderer.asyncio.create_subprocess_exec',
                    return_value=mock_proc,
                ),
            ):
                result = await render_d2(
                    d2_source='a -> b',
                    output_dir=tmpdir,
                )
                assert result.success is True
                assert result.stderr is not None
                assert 'unused node' in result.stderr


class TestInjectGlobalStyles:
    """Tests for _inject_global_styles helper."""

    def test_no_flags_returns_unchanged(self):
        """Test that no flags returns the source unchanged."""
        source = 'a -> b'
        assert _inject_global_styles(source) == source

    def test_shadow_injects_glob(self):
        """Test shadow flag injects **.style.shadow: true."""
        result = _inject_global_styles('a -> b', shadow=True)
        assert result.startswith('**.style.shadow: true')
        assert 'a -> b' in result

    def test_three_d_applies_per_node(self):
        """Test three_d applies style.3d: true to individual compatible nodes."""
        source = 'server: Server {\n}\ndb: Database {\n}\nserver -> db'
        result = _inject_global_styles(source, three_d=True)
        assert 'server.style.3d: true' in result
        assert 'db.style.3d: true' in result
        # No glob (would crash on incompatible shapes)
        assert '**.style.3d' not in result

    def test_three_d_skips_person_shape(self):
        """Test three_d auto-excludes person shapes."""
        source = 'user: User {\n  shape: person\n}\nserver: Server {\n}\nuser -> server'
        result = _inject_global_styles(source, three_d=True)
        assert 'server.style.3d: true' in result
        assert 'user.style.3d: true' not in result

    def test_three_d_epilogue_after_source(self):
        """Test that per-node 3d lines come after the source."""
        source = 'a: Service A {\n}\na -> b'
        result = _inject_global_styles(source, three_d=True)
        source_pos = result.index('a: Service A')
        style_pos = result.index('a.style.3d: true')
        assert style_pos > source_pos

    def test_animated_injects_connection_glob(self):
        """Test animated flag injects connection animated glob."""
        result = _inject_global_styles('a -> b', animated=True)
        assert '(** -> **)[*].style.animated: true' in result
        assert 'a -> b' in result

    def test_all_flags_combined(self):
        """Test all three flags together."""
        source = 'a: A {\n}\nb: B {\n}\na -> b'
        result = _inject_global_styles(source, shadow=True, three_d=True, animated=True)
        assert '**.style.shadow: true' in result
        assert 'a.style.3d: true' in result
        assert '(** -> **)[*].style.animated: true' in result

    def test_preamble_separated_by_blank_line(self):
        """Test that glob preamble is separated from source by blank line."""
        result = _inject_global_styles('a -> b', shadow=True)
        assert '\n\na -> b' in result


class TestFind3dCompatibleNodePaths:
    """Tests for _find_3d_compatible_node_paths helper."""

    def test_excludes_person_shape(self):
        """Test that person shape is excluded."""
        source = 'user: User {\n  shape: person\n}\nserver: Server {\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'user' not in paths
        assert 'server' in paths

    def test_excludes_cloud_shape(self):
        """Test that cloud shape is excluded."""
        source = 'internet: Internet {\n  shape: cloud\n}\napp: App {\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'internet' not in paths
        assert 'app' in paths

    def test_includes_default_rectangles(self):
        """Test that nodes without explicit shape are included (default = rectangle)."""
        source = 'a: Service A {\n}\nb: Service B {\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'a' in paths
        assert 'b' in paths

    def test_nested_nodes(self):
        """Test detection inside nested containers."""
        source = 'vpc: VPC {\n  web: Web {\n  }\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'vpc' in paths
        assert 'vpc.web' in paths

    def test_dot_notation_shape(self):
        """Test shape via dot notation."""
        source = 'user.shape: person\nserver: Server {\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'user' not in paths
        assert 'server' in paths

    def test_mixed_shapes(self):
        """Test mix of compatible and incompatible shapes."""
        source = (
            'user: User {\n  shape: person\n}\n'
            'server: Server {\n}\n'
            'db: Database {\n  shape: cylinder\n}'
        )
        paths = _find_3d_compatible_node_paths(source)
        assert 'user' not in paths
        assert 'db' not in paths
        assert 'server' in paths

    def test_ignores_comments(self):
        """Test that comments are ignored."""
        source = '# shape: person\na: Service A {\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'a' in paths

    def test_skips_d2_keywords(self):
        """Test that D2 keywords like steps/scenarios are not treated as nodes."""
        source = 'a: A {\n}\nsteps: {\n  1: {\n  }\n}'
        paths = _find_3d_compatible_node_paths(source)
        assert 'a' in paths
        assert 'steps' not in paths


class TestResolveFontFamily:
    """Tests for _resolve_font_family font detection."""

    def test_unknown_family_returns_none(self):
        """Test that unknown font family returns None."""
        assert _resolve_font_family('nonexistent-font') is None

    def test_known_family_with_mock_files(self, tmp_path):
        """Test resolution of a known family when TTF files exist."""
        # Create mock TTF files
        (tmp_path / 'AmazonEmber_Rg.ttf').touch()
        (tmp_path / 'AmazonEmber_Bd.ttf').touch()

        with patch(
            'awslabs.aws_diagram_mcp_server.d2_renderer.get_font_search_dirs',
            return_value=[str(tmp_path)],
        ):
            result = _resolve_font_family('amazon-ember')
            assert result is not None
            assert 'regular' in result
            assert 'bold' in result
            assert result['regular'].endswith('AmazonEmber_Rg.ttf')

    def test_partial_variants_returned(self, tmp_path):
        """Test that partial font variants are returned (D2 falls back for missing)."""
        # Exo 2 only has regular + italic (no bold/semibold)
        (tmp_path / 'Exo2-Regular.ttf').touch()

        with patch(
            'awslabs.aws_diagram_mcp_server.d2_renderer.get_font_search_dirs',
            return_value=[str(tmp_path)],
        ):
            result = _resolve_font_family('exo-2')
            assert result is not None
            assert 'regular' in result
            assert 'bold' not in result

    def test_no_files_found_returns_none(self, tmp_path):
        """Test that no matching files returns None."""
        with patch(
            'awslabs.aws_diagram_mcp_server.d2_renderer.get_font_search_dirs',
            return_value=[str(tmp_path)],
        ):
            result = _resolve_font_family('amazon-ember')
            assert result is None

    def test_case_insensitive_family_name(self, tmp_path):
        """Test that family name lookup is case-insensitive."""
        (tmp_path / 'Caveat-Regular.ttf').touch()

        with patch(
            'awslabs.aws_diagram_mcp_server.d2_renderer.get_font_search_dirs',
            return_value=[str(tmp_path)],
        ):
            result = _resolve_font_family('CAVEAT')
            assert result is not None
            assert 'regular' in result

    def test_bundled_fonts_checked_first(self, tmp_path):
        """Test that bundled fonts dir is checked before system dirs."""
        bundled = tmp_path / 'bundled'
        bundled.mkdir()
        (bundled / 'Exo2-Regular.ttf').touch()

        system = tmp_path / 'system'
        system.mkdir()
        (system / 'Exo2-Regular.ttf').touch()

        with (
            patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.BUNDLED_FONTS_DIR',
                str(bundled),
            ),
            patch(
                'awslabs.aws_diagram_mcp_server.d2_renderer.get_font_search_dirs',
                return_value=[str(system)],
            ),
        ):
            result = _resolve_font_family('exo-2')
            assert result is not None
            # Should resolve to bundled dir, not system dir
            assert str(bundled) in result['regular']
