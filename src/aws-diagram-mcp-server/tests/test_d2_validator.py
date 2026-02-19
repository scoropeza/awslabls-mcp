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

"""Tests for D2 source validator."""

from awslabs.aws_diagram_mcp_server.d2_validator import validate_d2_source


class TestValidateD2Source:
    """Tests for the validate_d2_source function."""

    def test_valid_connection(self):
        """Test valid D2 source with a connection."""
        result = validate_d2_source('a -> b')
        assert result.valid is True
        assert result.errors == []

    def test_valid_labeled_node(self):
        """Test valid D2 source with labeled nodes."""
        result = validate_d2_source('server: Web Server')
        assert result.valid is True

    def test_valid_bidirectional(self):
        """Test valid D2 source with bidirectional connection."""
        result = validate_d2_source('a <-> b')
        assert result.valid is True

    def test_valid_nested_access(self):
        """Test valid D2 source with dot-access nested nodes."""
        result = validate_d2_source('vpc.subnet.ec2: Instance')
        assert result.valid is True

    def test_valid_complex_diagram(self):
        """Test valid D2 source with multiple declarations."""
        source = """
        elb: Load Balancer
        ec2: Web Server
        rds: Database

        elb -> ec2 -> rds
        """
        result = validate_d2_source(source)
        assert result.valid is True

    def test_valid_with_comments(self):
        """Test valid D2 source with comments."""
        source = """
        # This is a comment
        a -> b: connection
        """
        result = validate_d2_source(source)
        assert result.valid is True

    def test_valid_double_dash_connection(self):
        """Test valid D2 source with double-dash connection."""
        result = validate_d2_source('a -- b')
        assert result.valid is True

    def test_empty_string(self):
        """Test that empty string is rejected."""
        result = validate_d2_source('')
        assert result.valid is False
        assert any('empty' in e.lower() for e in result.errors)

    def test_whitespace_only(self):
        """Test that whitespace-only string is rejected."""
        result = validate_d2_source('   \n\n  \t  ')
        assert result.valid is False
        assert any('empty' in e.lower() for e in result.errors)

    def test_comments_only(self):
        """Test that comments-only source is rejected."""
        source = """
        # Just a comment
        # Another comment
        """
        result = validate_d2_source(source)
        assert result.valid is False
        assert any('comments' in e.lower() or 'empty' in e.lower() for e in result.errors)

    def test_oversized_source(self):
        """Test that oversized source is rejected."""
        source = 'a -> b\n' * 100_000  # Well over 500KB
        result = validate_d2_source(source)
        assert result.valid is False
        assert any('size' in e.lower() or 'exceeds' in e.lower() for e in result.errors)

    def test_no_declarations(self):
        """Test source with no recognizable D2 declarations."""
        result = validate_d2_source('just some random text here')
        assert result.valid is False
        assert any(
            'declarations' in e.lower() or 'recognizable' in e.lower() for e in result.errors
        )
