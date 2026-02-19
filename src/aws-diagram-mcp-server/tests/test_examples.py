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

"""Tests for D2 example templates."""

from awslabs.aws_diagram_mcp_server.examples import (
    get_available_categories,
    get_examples,
)


class TestGetExamples:
    """Tests for get_examples function."""

    def test_get_all_examples(self):
        """Test getting all examples."""
        examples = get_examples()
        assert len(examples) > 0

    def test_get_all_with_explicit_all(self):
        """Test getting all examples with category='all'."""
        examples = get_examples('all')
        all_examples = get_examples()
        assert len(examples) == len(all_examples)

    def test_get_aws_examples(self):
        """Test filtering by 'aws' category."""
        examples = get_examples('aws')
        assert len(examples) > 0
        for ex in examples.values():
            assert ex.category == 'aws'

    def test_get_genai_examples(self):
        """Test filtering by 'genai' category."""
        examples = get_examples('genai')
        assert len(examples) > 0
        for ex in examples.values():
            assert ex.category == 'genai'

    def test_get_animation_examples(self):
        """Test filtering by 'animation' category."""
        examples = get_examples('animation')
        assert len(examples) > 0
        for ex in examples.values():
            assert ex.uses_animation is True

    def test_case_insensitive_category(self):
        """Test that category filter is case-insensitive."""
        upper = get_examples('AWS')
        lower = get_examples('aws')
        assert len(upper) == len(lower)

    def test_nonexistent_category_returns_empty(self):
        """Test that non-existent category returns empty dict."""
        examples = get_examples('nonexistent')
        assert len(examples) == 0

    def test_examples_have_required_fields(self):
        """Test that all examples have required fields populated."""
        examples = get_examples()
        for name, ex in examples.items():
            assert ex.title, f'Example {name} missing title'
            assert ex.description, f'Example {name} missing description'
            assert ex.d2_source.strip(), f'Example {name} has empty d2_source'
            assert ex.category, f'Example {name} missing category'

    def test_examples_d2_source_has_content(self):
        """Test that D2 source has actual diagram content."""
        examples = get_examples()
        for name, ex in examples.items():
            source = ex.d2_source.strip()
            # Each example should have connections or declarations
            has_arrow = '->' in source
            has_colon = ':' in source
            has_steps = 'steps' in source
            assert has_arrow or has_colon or has_steps, (
                f'Example {name} has no recognizable D2 content'
            )


class TestGetAvailableCategories:
    """Tests for get_available_categories function."""

    def test_categories_not_empty(self):
        """Test that categories list is not empty."""
        categories = get_available_categories()
        assert len(categories) > 0

    def test_expected_categories_present(self):
        """Test that key categories are present."""
        categories = get_available_categories()
        assert 'aws' in categories
        assert 'genai' in categories
        assert 'animation' in categories
        assert 'serverless' in categories

    def test_categories_sorted(self):
        """Test that categories are sorted."""
        categories = get_available_categories()
        assert categories == sorted(categories)
