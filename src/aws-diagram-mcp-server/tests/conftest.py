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

"""Shared test fixtures for aws-diagram-mcp-server tests."""

import os
import pytest
import tempfile
from awslabs.aws_diagram_mcp_server.models import AwsIcon
from unittest.mock import AsyncMock, patch


@pytest.fixture
def temp_workspace_dir():
    """Create a temporary workspace directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_d2_source():
    """Simple valid D2 source for testing."""
    return 'a: Service A\nb: Service B\na -> b: request'


@pytest.fixture
def sample_d2_with_icons():
    """D2 source with icon placeholders."""
    return """ec2: EC2 Instance {
  icon: ${ICON:Amazon-EC2}
}
rds: RDS Database {
  icon: ${ICON:Amazon-RDS}
}
ec2 -> rds: query
"""


@pytest.fixture
def sample_icon_index():
    """Sample icon index for testing."""
    return {
        'Compute': [
            AwsIcon(
                name='Arch_Amazon-EC2_64',
                label='Amazon EC2',
                path='/icons/Arch_Amazon-EC2_64.svg',
                category='Compute',
            ),
            AwsIcon(
                name='Arch_AWS-Lambda_64',
                label='AWS Lambda',
                path='/icons/Arch_AWS-Lambda_64.svg',
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


@pytest.fixture
def mock_d2_success():
    """Mock a successful D2 CLI execution."""
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b'', b''))
    mock_proc.returncode = 0

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
        yield mock_proc


@pytest.fixture
def mock_icons_available(sample_icon_index, tmp_path):
    """Mock icon availability for server-level tests."""
    # Create a mock icons directory with manifest
    icons_dir = str(tmp_path / 'icons')
    os.makedirs(icons_dir, exist_ok=True)

    with (
        patch(
            'awslabs.aws_diagram_mcp_server.server.ensure_icons_available',
            return_value=icons_dir,
        ),
        patch(
            'awslabs.aws_diagram_mcp_server.server.build_icon_index',
            return_value=sample_icon_index,
        ),
    ):
        yield sample_icon_index
