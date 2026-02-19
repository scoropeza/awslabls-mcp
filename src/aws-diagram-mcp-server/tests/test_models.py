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

"""Tests for D2-based Pydantic models."""

import pytest
from awslabs.aws_diagram_mcp_server.models import (
    AwsIcon,
    AwsIconsResponse,
    D2RenderResult,
    D2ValidationResult,
    D2VersionInfo,
    DiagramExample,
    DiagramExampleResponse,
    DiagramGenerateResponse,
)


class TestD2VersionInfo:
    """Tests for D2VersionInfo model."""

    def test_create_version_info(self):
        """Test creating a version info instance."""
        info = D2VersionInfo(version='0.6.9', path='/usr/local/bin/d2')
        assert info.version == '0.6.9'
        assert info.path == '/usr/local/bin/d2'

    def test_version_info_requires_fields(self):
        """Test that version and path are required."""
        with pytest.raises(Exception):
            D2VersionInfo()


class TestD2RenderResult:
    """Tests for D2RenderResult model."""

    def test_success_result(self):
        """Test creating a successful render result."""
        result = D2RenderResult(
            success=True,
            image_path='/tmp/out.svg',
            source_path='/tmp/out.d2',
            message='Rendered successfully',
        )
        assert result.success is True
        assert result.image_path == '/tmp/out.svg'
        assert result.source_path == '/tmp/out.d2'
        assert result.stderr is None

    def test_error_result(self):
        """Test creating an error render result."""
        result = D2RenderResult(
            success=False,
            stderr='syntax error at line 5',
            message='D2 rendering failed',
        )
        assert result.success is False
        assert result.image_path is None
        assert result.source_path is None
        assert result.stderr == 'syntax error at line 5'

    def test_result_with_stderr_warnings(self):
        """Test result with warnings in stderr."""
        result = D2RenderResult(
            success=True,
            image_path='/tmp/out.svg',
            source_path='/tmp/out.d2',
            stderr='warning: unused node',
            message='Rendered with warnings',
        )
        assert result.success is True
        assert result.stderr == 'warning: unused node'


class TestDiagramGenerateResponse:
    """Tests for DiagramGenerateResponse model."""

    def test_success_response(self):
        """Test successful response."""
        resp = DiagramGenerateResponse(
            status='success',
            image_path='/tmp/diagram.svg',
            source_path='/tmp/diagram.d2',
            message='Diagram generated',
        )
        assert resp.status == 'success'
        assert resp.image_path == '/tmp/diagram.svg'
        assert resp.source_path == '/tmp/diagram.d2'

    def test_error_response(self):
        """Test error response."""
        resp = DiagramGenerateResponse(
            status='error',
            message='D2 not installed',
        )
        assert resp.status == 'error'
        assert resp.image_path is None
        assert resp.source_path is None

    def test_status_literal_values(self):
        """Test that status only accepts 'success' or 'error'."""
        with pytest.raises(Exception):
            DiagramGenerateResponse(status='unknown', message='test')


class TestDiagramExample:
    """Tests for DiagramExample model."""

    def test_basic_example(self):
        """Test creating a basic example."""
        ex = DiagramExample(
            title='Three-Tier Web',
            description='Classic three-tier architecture',
            d2_source='elb -> ec2 -> rds',
            category='aws',
        )
        assert ex.title == 'Three-Tier Web'
        assert ex.uses_animation is False

    def test_animation_example(self):
        """Test creating an example with animation."""
        ex = DiagramExample(
            title='Request Flow',
            description='Animated request flow',
            d2_source='steps: { step1: { a -> b } }',
            category='animation',
            uses_animation=True,
        )
        assert ex.uses_animation is True


class TestDiagramExampleResponse:
    """Tests for DiagramExampleResponse model."""

    def test_example_response(self):
        """Test creating example response with multiple examples."""
        examples = {
            'three_tier': DiagramExample(
                title='Three-Tier',
                description='Three-tier web',
                d2_source='a -> b -> c',
                category='aws',
            ),
        }
        resp = DiagramExampleResponse(examples=examples)
        assert 'three_tier' in resp.examples
        assert resp.examples['three_tier'].category == 'aws'


class TestAwsIcon:
    """Tests for AwsIcon model."""

    def test_create_icon(self):
        """Test creating an icon instance."""
        icon = AwsIcon(
            name='Arch_Amazon-EC2_64',
            label='Amazon EC2',
            path='/cache/icons/Compute/64/Arch_Amazon-EC2_64.svg',
            category='Compute',
        )
        assert icon.name == 'Arch_Amazon-EC2_64'
        assert icon.label == 'Amazon EC2'
        assert icon.category == 'Compute'


class TestAwsIconsResponse:
    """Tests for AwsIconsResponse model."""

    def test_icons_response(self):
        """Test creating icons response."""
        resp = AwsIconsResponse(
            categories={
                'Compute': [
                    AwsIcon(
                        name='Arch_Amazon-EC2_64',
                        label='Amazon EC2',
                        path='/cache/icons/Compute/64/Arch_Amazon-EC2_64.svg',
                        category='Compute',
                    ),
                ],
            },
            total_count=1,
            filtered=False,
        )
        assert resp.total_count == 1
        assert len(resp.categories['Compute']) == 1

    def test_filtered_response(self):
        """Test filtered icons response."""
        resp = AwsIconsResponse(
            categories={},
            total_count=0,
            filtered=True,
        )
        assert resp.filtered is True
        assert resp.total_count == 0


class TestD2ValidationResult:
    """Tests for D2ValidationResult model."""

    def test_valid_result(self):
        """Test valid validation result."""
        result = D2ValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []

    def test_invalid_result_with_errors(self):
        """Test invalid result with error messages."""
        result = D2ValidationResult(
            valid=False,
            errors=['D2 source is empty', 'Missing declarations'],
        )
        assert result.valid is False
        assert len(result.errors) == 2
