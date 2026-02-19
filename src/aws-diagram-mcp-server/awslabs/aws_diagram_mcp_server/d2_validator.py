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

"""Lightweight D2 source validation.

D2 is declarative (not executable code), so validation is minimal compared
to the previous Python code scanning. No AST analysis or bandit scanning needed.
"""

import re
from awslabs.aws_diagram_mcp_server.consts import MAX_D2_SOURCE_SIZE
from awslabs.aws_diagram_mcp_server.models import D2ValidationResult


# Pattern matching D2 node declarations or connections
# Matches: `a -> b`, `a: label`, `a.b`, `a -- b`, `a <-> b`, or standalone identifiers
_D2_STRUCTURE_PATTERN = re.compile(
    r'^\s*[a-zA-Z_][a-zA-Z0-9_\-]*'  # identifier start
    r'(?:\s*(?:->|<->|--|:|\.))',  # followed by connection/label/access operator
    re.MULTILINE,
)


def validate_d2_source(source: str) -> D2ValidationResult:
    """Validate D2 source code before rendering.

    Performs lightweight checks:
    - Non-empty check
    - Size limit enforcement
    - Basic structure check (must contain node declarations or connections)

    Args:
        source: D2 DSL source code string.

    Returns:
        D2ValidationResult with validation status and any error messages.
    """
    errors: list[str] = []

    # Check non-empty
    stripped = source.strip()
    if not stripped:
        errors.append('D2 source is empty')
        return D2ValidationResult(valid=False, errors=errors)

    # Check size limit
    size = len(source.encode('utf-8'))
    if size > MAX_D2_SOURCE_SIZE:
        errors.append(
            f'D2 source exceeds maximum size of {MAX_D2_SOURCE_SIZE} bytes (got {size} bytes)'
        )
        return D2ValidationResult(valid=False, errors=errors)

    # Check for basic D2 structure
    # Filter out comments and empty lines for analysis
    content_lines = []
    for line in stripped.split('\n'):
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith('#'):
            content_lines.append(line_stripped)

    if not content_lines:
        errors.append('D2 source contains only comments or empty lines')
        return D2ValidationResult(valid=False, errors=errors)

    # Check that at least one line looks like a D2 declaration
    if not _D2_STRUCTURE_PATTERN.search(stripped):
        errors.append(
            'D2 source does not contain any recognizable declarations. '
            'Expected node definitions (e.g., "a: Label") or connections (e.g., "a -> b").'
        )
        return D2ValidationResult(valid=False, errors=errors)

    return D2ValidationResult(valid=True, errors=[])
