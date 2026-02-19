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

"""Tests for AWS icon management module."""

import json
import os
import pytest
import tempfile
from awslabs.aws_diagram_mcp_server.icons import (
    _extract_category,
    _make_label,
    build_icon_index,
    ensure_icons_available,
    find_icons,
    resolve_icon_placeholders,
)
from awslabs.aws_diagram_mcp_server.models import AwsIcon
from unittest.mock import patch


class TestExtractCategory:
    """Tests for _extract_category helper."""

    def test_arch_underscore_prefix(self):
        """Test extracting category from Arch_ prefix."""
        assert _extract_category('Arch_Compute') == 'Compute'

    def test_arch_hyphen_prefix(self):
        """Test extracting category from Arch- prefix."""
        assert _extract_category('Arch-Compute') == 'Compute'

    def test_multi_word_category(self):
        """Test extracting multi-word category."""
        result = _extract_category('Arch_Machine-Learning')
        assert result == 'Machine Learning'

    def test_no_prefix(self):
        """Test directory without Arch prefix."""
        assert _extract_category('Compute') == 'Compute'


class TestMakeLabel:
    """Tests for _make_label helper."""

    def test_standard_icon_name(self):
        """Test label from standard icon name."""
        assert _make_label('Arch_Amazon-EC2_64') == 'Amazon EC2'

    def test_long_name(self):
        """Test label from longer icon name."""
        assert _make_label('Arch_AWS-Lambda_64') == 'AWS Lambda'

    def test_no_prefix(self):
        """Test label without Arch prefix."""
        assert _make_label('Amazon-S3_64') == 'Amazon S3'


class TestBuildIconIndex:
    """Tests for build_icon_index function."""

    def test_build_index_from_directory(self):
        """Test building index from a mock directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock directory structure
            compute_dir = os.path.join(tmpdir, 'Arch_Compute', '64')
            os.makedirs(compute_dir)

            # Create mock SVG files
            svg1 = os.path.join(compute_dir, 'Arch_Amazon-EC2_64.svg')
            svg2 = os.path.join(compute_dir, 'Arch_AWS-Lambda_64.svg')
            for svg in [svg1, svg2]:
                with open(svg, 'w') as f:
                    f.write('<svg></svg>')

            index = build_icon_index(tmpdir)
            assert len(index) > 0

            # Find the category that contains our icons
            found_ec2 = False
            found_lambda = False
            for icons in index.values():
                for icon in icons:
                    if 'EC2' in icon.name:
                        found_ec2 = True
                    if 'Lambda' in icon.name:
                        found_lambda = True

            assert found_ec2
            assert found_lambda

    def test_build_index_empty_directory(self):
        """Test building index from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index = build_icon_index(tmpdir)
            assert len(index) == 0


class TestFindIcons:
    """Tests for find_icons function."""

    @pytest.fixture
    def sample_index(self):
        """Create a sample icon index for testing."""
        return {
            'Compute': [
                AwsIcon(
                    name='Arch_Amazon-EC2_64',
                    label='Amazon EC2',
                    path='/icons/Compute/64/Arch_Amazon-EC2_64.svg',
                    category='Compute',
                ),
                AwsIcon(
                    name='Arch_AWS-Lambda_64',
                    label='AWS Lambda',
                    path='/icons/Compute/64/Arch_AWS-Lambda_64.svg',
                    category='Compute',
                ),
            ],
            'Database': [
                AwsIcon(
                    name='Arch_Amazon-RDS_64',
                    label='Amazon RDS',
                    path='/icons/Database/64/Arch_Amazon-RDS_64.svg',
                    category='Database',
                ),
                AwsIcon(
                    name='Arch_Amazon-DynamoDB_64',
                    label='Amazon DynamoDB',
                    path='/icons/Database/64/Arch_Amazon-DynamoDB_64.svg',
                    category='Database',
                ),
            ],
        }

    def test_search_by_name(self, sample_index):
        """Test searching icons by name."""
        result = find_icons(sample_index, search='EC2')
        assert 'Compute' in result
        assert len(result['Compute']) == 1
        assert result['Compute'][0].name == 'Arch_Amazon-EC2_64'

    def test_search_by_label(self, sample_index):
        """Test searching icons by label."""
        result = find_icons(sample_index, search='Lambda')
        assert 'Compute' in result
        assert len(result['Compute']) == 1

    def test_search_case_insensitive(self, sample_index):
        """Test that search is case-insensitive."""
        result = find_icons(sample_index, search='lambda')
        assert 'Compute' in result

    def test_filter_by_category(self, sample_index):
        """Test filtering by category."""
        result = find_icons(sample_index, category='Database')
        assert 'Database' in result
        assert 'Compute' not in result
        assert len(result['Database']) == 2

    def test_filter_category_case_insensitive(self, sample_index):
        """Test that category filter is case-insensitive."""
        result = find_icons(sample_index, category='database')
        assert 'Database' in result

    def test_no_filters(self, sample_index):
        """Test that no filters returns everything."""
        result = find_icons(sample_index)
        assert len(result) == 2
        assert 'Compute' in result
        assert 'Database' in result

    def test_search_no_results(self, sample_index):
        """Test search with no matching results."""
        result = find_icons(sample_index, search='NonExistent')
        assert len(result) == 0

    def test_combined_filters(self, sample_index):
        """Test search with both category and search term."""
        result = find_icons(sample_index, search='Amazon', category='Database')
        assert 'Database' in result
        assert len(result['Database']) == 2  # Both RDS and DynamoDB match


class TestEnsureIconsAvailable:
    """Tests for ensure_icons_available function."""

    def test_icons_already_cached(self):
        """Test that cached icons are detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest file
            manifest_path = os.path.join(tmpdir, '.manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump({'url': 'test', 'extracted': True}, f)

            with patch(
                'awslabs.aws_diagram_mcp_server.icons._get_icons_dir',
                return_value=tmpdir,
            ):
                result = ensure_icons_available()
                assert result == tmpdir

    def test_icons_download_on_first_call(self):
        """Test that icons are downloaded when not cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            icons_dir = os.path.join(tmpdir, 'icons')

            with (
                patch(
                    'awslabs.aws_diagram_mcp_server.icons._get_icons_dir',
                    return_value=icons_dir,
                ),
                patch(
                    'awslabs.aws_diagram_mcp_server.icons._download_and_extract_icons',
                ) as mock_download,
            ):
                ensure_icons_available()
                mock_download.assert_called_once_with(icons_dir)


class TestResolveIconPlaceholders:
    """Tests for resolve_icon_placeholders function."""

    @pytest.fixture
    def sample_index(self):
        """Create a sample icon index."""
        return {
            'Compute': [
                AwsIcon(
                    name='Arch_Amazon-EC2_64',
                    label='Amazon EC2',
                    path='/icons/Arch_Amazon-EC2_64.svg',
                    category='Compute',
                ),
            ],
            'Database': [
                AwsIcon(
                    name='Arch_Amazon-RDS_64',
                    label='Amazon RDS',
                    path='/icons/Arch_Amazon-RDS_64.svg',
                    category='Database',
                ),
            ],
        }

    def test_replace_placeholder(self, sample_index):
        """Test basic placeholder replacement."""
        source = 'ec2.icon: ${ICON:Amazon-EC2}'
        result = resolve_icon_placeholders(source, sample_index)
        assert '/icons/Arch_Amazon-EC2_64.svg' in result
        assert '${ICON:' not in result

    def test_replace_multiple_placeholders(self, sample_index):
        """Test replacing multiple placeholders."""
        source = 'ec2.icon: ${ICON:Amazon-EC2}\nrds.icon: ${ICON:Amazon-RDS}'
        result = resolve_icon_placeholders(source, sample_index)
        assert '${ICON:' not in result
        assert '/icons/Arch_Amazon-EC2_64.svg' in result
        assert '/icons/Arch_Amazon-RDS_64.svg' in result

    def test_unknown_placeholder_preserved(self, sample_index):
        """Test that unknown placeholders are preserved."""
        source = 'x.icon: ${ICON:NonExistent}'
        result = resolve_icon_placeholders(source, sample_index)
        assert '${ICON:NonExistent}' in result

    def test_no_placeholders(self, sample_index):
        """Test source without placeholders is unchanged."""
        source = 'a -> b -> c'
        result = resolve_icon_placeholders(source, sample_index)
        assert result == source
