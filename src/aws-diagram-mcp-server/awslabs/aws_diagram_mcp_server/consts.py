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

"""Constants for the aws-diagram-mcp-server."""

import os


# AWS Architecture Icons download URL
AWS_ICONS_URL = (
    'https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/'
    'architecture/approved/architecture-icons/'
    'Icon-package_01302026.31b40d126ed27079b708594940ad577a86150582.zip'
)

# Default cache directory for icons
DEFAULT_ICONS_CACHE_DIR = os.path.join(
    os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')),
    'aws-diagram-mcp-server',
    'icons',
)

# Environment variable override for icons directory
ICONS_DIR_ENV_VAR = 'AWS_DIAGRAM_ICONS_DIR'

# Icon manifest filename (used to detect if icons are already extracted)
ICONS_MANIFEST_FILE = '.manifest.json'

# Icon glob pattern within the extracted archive
# Targets 64px Architecture Service Icons SVGs
ICON_GLOB_PATTERN = '**/Arch_*/64/*.svg'

# D2 theme catalog: ID -> (name, color palette description)
# Complete list from `d2 themes` CLI output
D2_THEME_CATALOG: dict[int, tuple[str, str]] = {
    # Light themes
    0: (
        'Neutral Default',
        'White bg, dark grey nodes, blue connections. Professional and minimal.',
    ),
    1: (
        'Neutral Grey',
        'Light grey bg, medium grey nodes, muted blue connections. Soft corporate.',
    ),
    3: ('Flagship Terrastruct', 'White bg, teal/cyan nodes and connections. D2 brand look.'),
    4: ('Cool Classics', 'White bg, navy blue nodes, slate connections. Traditional enterprise.'),
    5: (
        'Mixed Berry Blue',
        'White bg, purple/indigo nodes, violet connections. Modern and vibrant.',
    ),
    6: ('Grape Soda', 'White bg, deep purple nodes, magenta/plum accents. Bold and expressive.'),
    7: ('Aubergine', 'White bg, dark eggplant/wine nodes, burgundy connections. Rich and formal.'),
    8: ('Colorblind Clear', 'White bg, high-contrast orange/blue palette. Accessible design.'),
    # Warm light themes
    100: (
        'Vanilla Nitro Cola',
        'Cream bg, brown/amber nodes, warm gold connections. Vintage feel.',
    ),
    101: (
        'Orange Creamsicle',
        'White bg, bright orange nodes, coral/peach connections. Warm and friendly.',
    ),
    102: (
        'Shirley Temple',
        'White bg, pink/rose nodes, cherry red connections. Playful and bright.',
    ),
    103: (
        'Earth Tones',
        'White bg, olive/forest green nodes, brown connections. Natural and grounded.',
    ),
    104: ('Everglade Green', 'White bg, deep green nodes, teal connections. Fresh and organic.'),
    105: (
        'Buttered Toast',
        'Warm white bg, golden/amber nodes, honey connections. Warm and inviting.',
    ),
    # Dark themes
    200: (
        'Dark Mauve',
        'Dark purple bg, light lavender nodes, soft pink connections. Elegant dark mode.',
    ),
    201: (
        'Dark Flagship Terrastruct',
        'Dark navy bg, bright teal nodes, cyan connections. D2 dark mode.',
    ),
    # Special themes
    300: (
        'Terminal',
        'Black bg, green monospace text and connections. Classic terminal aesthetic.',
    ),
    301: (
        'Terminal Grayscale',
        'Black bg, white/grey monospace text. Retro terminal without color.',
    ),
    302: ('Origami', 'White bg, paper-fold style, soft pastel nodes. Artistic and minimal.'),
    303: ('C4', 'C4 model conventions: blue person shapes, blue containers, grey systems.'),
}

# Build a compact theme description string for tool tooltips
_light = ', '.join(f'{tid}={name}' for tid, (name, _) in D2_THEME_CATALOG.items() if tid < 100)
_warm = ', '.join(
    f'{tid}={name}' for tid, (name, _) in D2_THEME_CATALOG.items() if 100 <= tid < 200
)
_dark = ', '.join(
    f'{tid}={name}' for tid, (name, _) in D2_THEME_CATALOG.items() if 200 <= tid < 300
)
_special = ', '.join(f'{tid}={name}' for tid, (name, _) in D2_THEME_CATALOG.items() if tid >= 300)
THEME_TOOLTIP = (
    'D2 theme ID. 20 built-in themes:\n'
    f'LIGHT: {_light}\n'
    f'WARM: {_warm}\n'
    f'DARK: {_dark}\n'
    f'SPECIAL: {_special}\n'
    'None for default (0=Neutral Default).'
)

# Default values
DEFAULT_OUTPUT_FORMAT = 'svg'
DEFAULT_LAYOUT_ENGINE = 'dagre'
DEFAULT_TIMEOUT = 60
DEFAULT_THEME = 0

# Limits
MAX_D2_SOURCE_SIZE = 512_000  # 500KB
MAX_TIMEOUT = 300
MIN_TIMEOUT = 1

# Output subdirectory name
OUTPUT_SUBDIRECTORY = 'generated-diagrams'
