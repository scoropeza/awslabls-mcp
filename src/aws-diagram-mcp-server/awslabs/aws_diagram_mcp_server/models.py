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

"""Pydantic models for the aws-diagram-mcp-server (D2-based)."""

from pydantic import BaseModel, Field
from typing import Literal


# --- D2 Renderer Models ---


class D2VersionInfo(BaseModel):
    """Information about the installed D2 binary."""

    version: str = Field(..., description='D2 version string')
    path: str = Field(..., description='Path to the D2 binary')


class D2RenderResult(BaseModel):
    """Result of a D2 render operation."""

    success: bool = Field(..., description='Whether rendering succeeded')
    image_path: str | None = Field(None, description='Path to the generated image file')
    source_path: str | None = Field(None, description='Path to the saved .d2 source file')
    stderr: str | None = Field(None, description='D2 stderr output (errors/warnings)')
    message: str = Field(..., description='Human-readable result message')


# --- Tool Request/Response Models ---


class DiagramGenerateResponse(BaseModel):
    """Response from the generate-diagram tool."""

    status: Literal['success', 'error']
    image_path: str | None = Field(None, description='Path to the generated image file')
    source_path: str | None = Field(None, description='Path to the saved .d2 source file')
    message: str = Field(..., description='Human-readable status message')


class DiagramExample(BaseModel):
    """A single D2 diagram example."""

    title: str = Field(..., description='Example title')
    description: str = Field(..., description='What this example demonstrates')
    d2_source: str = Field(..., description='D2 DSL source code')
    category: str = Field(..., description='Example category')
    uses_animation: bool = Field(False, description='Whether this example uses D2 animation steps')


class DiagramExampleResponse(BaseModel):
    """Response from the get-diagram-examples tool."""

    examples: dict[str, DiagramExample] = Field(
        ..., description='Map of example name to example details'
    )


class AwsIcon(BaseModel):
    """A single AWS architecture icon."""

    name: str = Field(..., description='Icon filename without extension')
    label: str = Field(..., description='Human-readable label')
    path: str = Field(..., description='Absolute path to the SVG file')
    category: str = Field(..., description='AWS service category')


class AwsIconsResponse(BaseModel):
    """Response from the list-aws-icons tool."""

    categories: dict[str, list[AwsIcon]] = Field(
        ..., description='Icons organized by AWS category'
    )
    total_count: int = Field(..., description='Total number of icons found')
    filtered: bool = Field(False, description='Whether results are filtered')


# --- Validator Models ---


class D2ValidationResult(BaseModel):
    """Result of D2 source validation."""

    valid: bool = Field(..., description='Whether the D2 source is valid')
    errors: list[str] = Field(default_factory=list, description='Validation error messages')
