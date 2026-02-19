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

"""AWS icon package management: download, extract, cache, index, and lookup.

Downloads the official AWS Architecture Icons package from d1.awsstatic.com
on first use, extracts SVG files, and provides search/lookup functionality
for use in D2 diagrams via icon: properties.
"""

import glob
import json
import os
import re
import zipfile
from awslabs.aws_diagram_mcp_server.consts import (
    AWS_ICONS_URL,
    DEFAULT_ICONS_CACHE_DIR,
    ICONS_DIR_ENV_VAR,
    ICONS_MANIFEST_FILE,
)
from awslabs.aws_diagram_mcp_server.models import AwsIcon
from loguru import logger
from urllib.request import urlretrieve


def _get_icons_dir() -> str:
    """Get the icons cache directory path.

    Returns:
        Path to the icons directory, from env var or default.
    """
    return os.environ.get(ICONS_DIR_ENV_VAR, DEFAULT_ICONS_CACHE_DIR)


def _download_and_extract_icons(icons_dir: str) -> None:
    """Download and extract the AWS icon package.

    Args:
        icons_dir: Directory to extract icons into.
    """
    os.makedirs(icons_dir, exist_ok=True)
    zip_path = os.path.join(icons_dir, 'aws-icons.zip')

    logger.info(f'Downloading AWS icons from {AWS_ICONS_URL}')
    urlretrieve(AWS_ICONS_URL, zip_path)

    logger.info(f'Extracting icons to {icons_dir}')
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(icons_dir)

    # Clean up zip file
    os.remove(zip_path)

    # Write manifest
    manifest = {'url': AWS_ICONS_URL, 'extracted': True}
    manifest_path = os.path.join(icons_dir, ICONS_MANIFEST_FILE)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f)

    logger.info('AWS icons extracted successfully')


def ensure_icons_available() -> str:
    """Ensure AWS icons are downloaded and extracted.

    Downloads the official AWS Architecture Icons package on first call,
    extracts to the cache directory, and returns the icons root path.

    Returns:
        Path to the icons root directory.

    Raises:
        RuntimeError: If icon download or extraction fails.
    """
    icons_dir = _get_icons_dir()
    manifest_path = os.path.join(icons_dir, ICONS_MANIFEST_FILE)

    if os.path.exists(manifest_path):
        logger.debug(f'AWS icons already available at {icons_dir}')
        return icons_dir

    try:
        _download_and_extract_icons(icons_dir)
    except Exception as e:
        raise RuntimeError(f'Failed to download/extract AWS icons: {e}') from e

    return icons_dir


def build_icon_index(icons_dir: str) -> dict[str, list[AwsIcon]]:
    """Build an index of AWS icons organized by category.

    Scans the extracted icon directory for Architecture Service Icons (64px SVGs)
    and organizes them by AWS service category.

    Args:
        icons_dir: Root directory of extracted icons.

    Returns:
        Dictionary mapping category names to lists of AwsIcon objects.
    """
    index: dict[str, list[AwsIcon]] = {}

    # Find all 64px architecture service icon SVGs
    # Pattern: .../Architecture-Service-Icons_*/Arch_*/64/Arch_*.svg
    # Also try: .../Arch_*/64/*.svg for different archive structures
    patterns = [
        os.path.join(icons_dir, '**', 'Arch_*', '64', '*.svg'),
        os.path.join(icons_dir, '**', 'Arch-*', '64', '*.svg'),
    ]

    svg_files: list[str] = []
    for pattern in patterns:
        svg_files.extend(glob.glob(pattern, recursive=True))

    # Deduplicate
    svg_files = list(set(svg_files))

    for svg_path in sorted(svg_files):
        abs_path = os.path.abspath(svg_path)
        filename = os.path.basename(svg_path)
        name = os.path.splitext(filename)[0]

        # Extract category from parent directory name
        # e.g., .../Arch_Compute/64/Arch_Amazon-EC2_64.svg -> "Compute"
        parent_dir = os.path.basename(os.path.dirname(os.path.dirname(svg_path)))
        category = _extract_category(parent_dir)

        # Create human-readable label from filename
        label = _make_label(name)

        icon = AwsIcon(
            name=name,
            label=label,
            path=abs_path,
            category=category,
        )

        if category not in index:
            index[category] = []
        index[category].append(icon)

    return index


def _extract_category(dir_name: str) -> str:
    """Extract category name from directory name.

    Handles patterns like 'Arch_Compute', 'Arch_Machine-Learning', 'Arch-Category_Name'.

    Args:
        dir_name: Directory name to extract category from.

    Returns:
        Human-readable category name.
    """
    # Remove Arch_ or Arch- prefix
    cleaned = re.sub(r'^Arch[_-]', '', dir_name)
    # Replace hyphens and underscores with spaces for readability
    return cleaned.replace('-', ' ').replace('_', ' ').strip()


def _make_label(name: str) -> str:
    """Create a human-readable label from an icon filename.

    Handles patterns like 'Arch_Amazon-EC2_64' -> 'Amazon EC2'.

    Args:
        name: Icon filename without extension.

    Returns:
        Human-readable label.
    """
    # Remove Arch_ prefix and _64 suffix (or other size suffixes)
    cleaned = re.sub(r'^Arch[_-]', '', name)
    cleaned = re.sub(r'_\d+$', '', cleaned)
    # Replace hyphens with spaces, but keep adjacent to capital letters
    cleaned = cleaned.replace('_', ' ').replace('-', ' ')
    # Clean up extra spaces
    return ' '.join(cleaned.split())


def find_icons(
    index: dict[str, list[AwsIcon]],
    search: str | None = None,
    category: str | None = None,
) -> dict[str, list[AwsIcon]]:
    """Search for icons by name or category.

    Args:
        index: Icon index from build_icon_index().
        search: Case-insensitive search term for icon names/labels.
        category: Case-insensitive category filter.

    Returns:
        Filtered icon index matching the search criteria.
    """
    result: dict[str, list[AwsIcon]] = {}

    for cat_name, icons in index.items():
        # Filter by category if specified
        if category and category.lower() not in cat_name.lower():
            continue

        if search:
            # Filter by search term in name or label
            search_lower = search.lower()
            matched = [
                icon
                for icon in icons
                if search_lower in icon.name.lower() or search_lower in icon.label.lower()
            ]
            if matched:
                result[cat_name] = matched
        else:
            result[cat_name] = icons

    return result


def resolve_icon_placeholders(d2_source: str, index: dict[str, list[AwsIcon]]) -> str:
    """Replace ${ICON:Name} placeholders in D2 source with absolute SVG paths.

    Scans D2 source for patterns like ${ICON:Amazon-EC2} and replaces them with
    the absolute path to the matching SVG icon file.

    Args:
        d2_source: D2 source code with icon placeholders.
        index: Icon index from build_icon_index().

    Returns:
        D2 source with placeholders replaced by absolute SVG paths.
    """
    # Build a flat lookup: lowercase name/label -> path
    flat_lookup: dict[str, str] = {}
    for icons in index.values():
        for icon in icons:
            # Index by various name forms for flexible matching
            flat_lookup[icon.name.lower()] = icon.path
            flat_lookup[icon.label.lower()] = icon.path
            # Also index without Arch_ prefix and _64 suffix
            short_name = re.sub(r'^Arch[_-]', '', icon.name)
            short_name = re.sub(r'_\d+$', '', short_name)
            flat_lookup[short_name.lower()] = icon.path

    def _replace_placeholder(match: re.Match) -> str:
        icon_name = match.group(1)
        path = flat_lookup.get(icon_name.lower())
        if path:
            return path
        # Try with hyphens replaced by spaces
        path = flat_lookup.get(icon_name.lower().replace('-', ' '))
        if path:
            return path
        logger.warning(f'Icon not found for placeholder: ${{ICON:{icon_name}}}')
        return ''  # Remove placeholder to prevent D2 compile error

    result = re.sub(r'\$\{ICON:([^}]+)\}', _replace_placeholder, d2_source)

    # Remove lines where icon: has no value (placeholder was stripped)
    # e.g., "    icon: " becomes invalid D2 — remove the entire line
    result = re.sub(r'^[ \t]*icon:\s*$', '', result, flags=re.MULTILINE)

    return result
