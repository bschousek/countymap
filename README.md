# US State County Map Generator with Maidenhead Grid Squares

Generate professional PDF maps and reference tables for any US state, featuring county boundaries, abbreviations, and Maidenhead grid square overlays for amateur radio use.

## Features

- **Works for Any US State**: Just provide the state FIPS code
- **Maidenhead Grid Overlay**: 4-character ham radio grid squares
- **Configurable**: Customize which grids to show and where labels appear
- **Flexible Abbreviations**: Auto-generate or provide custom county abbreviations, including support for alternate spellings via a single entry
- **Great Lakes Clipping**: Optional shoreline clipping for Great Lakes states
- **Professional Output**: High-resolution maps and organized reference tables

## Quick Start

### File Naming Conventions

To support multiple states in the same folder the script uses a slug derived from the
state name (lowercase, spaces turned to underscores) as a prefix for generated files.
By default the following names are used:

- `<slug>_abbreviations.csv` for the county abbreviations file
- `<slug>_county_map.png` for the temporary map image
- `<slug>_counties.pdf` for the final PDF output

You can override any of these with the `--abbreviations`, `--output` options, or by
passing a full path for the map image when calling `create_county_map`.

### Generate a Map for Wisconsin

```bash
python generate_state_map.py --config wisconsin_config.json
```

### Generate a Map for Any State

```bash
python generate_state_map.py --config your_state_config.json
```

Replace `your_state_config.json` with your state's configuration file.

> **Tip**: You can find US state FIPS codes online (e.g., Wisconsin is 55, California is 06).

## Installation

### Requirements

```bash
pip install geopandas pandas matplotlib reportlab shapely pyproj
```

### Required Data Files

1. **Census County Shapefile** (required):
   - Download: https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip
   - Extract to: `shapefile/tl_2023_us_county.shp`

2. **Natural Earth Lakes** (optional, for Great Lakes states):
   - Download: https://www.naturalearthdata.com/downloads/10m-physical-vectors/
   - Look for "Lakes + Reservoirs"
   - Extract to: `shapefile/ne_10m_lakes.shp`

## Configuration Files

### Creating a Configuration File

Generate a template configuration:

```bash
python state_config.py
```

### Configuration Format

```json
{
  "state_name": "Wisconsin",
  "state_fips": "55",
  "shapefile": "shapefile/tl_2023_us_county.shp",
  "lakes": "shapefile/ne_10m_lakes.shp",
  "abbreviations": "wisconsin_abbreviations.csv",
  "output": "wisconsin_counties.pdf",
  "no_lakes": false,
  "exclude_grids": ["EN32", "EN33", "EN37"],
  "label_adjustments": {
    "EN45": {"x_offset": 25000, "y_offset": 0},
    "EN54": {"x_offset": 0, "y_offset": 20000}
  },
  "custom_abbreviations": {
    "St. Croix;St Croix;Saint Croix": "STC",
    "Fond du Lac": "FON"
  }
}
```

**Fields:**
- `exclude_grids`: List of Maidenhead grid squares to hide
- `label_adjustments`: Move grid labels to avoid overlapping county names
  - `x_offset`: Meters east (positive) or west (negative)
  - `y_offset`: Meters north (positive) or south (negative)
- `custom_abbreviations`: Override auto-generated abbreviations; keys can be a single county name or a semicolon-separated list of alternate spellings (case is ignored).  e.g. ``"St. Croix;St Croix;Saint Croix": "STC"``

### County label adjustments (new)

You can now nudge individual county labels to avoid overlap with Maidenhead grid labels or neighboring counties. Add a `county_label_adjustments` object to your config with per-county offsets (units are projection units — meters when using `EPSG:3857`). Example:

```json
"county_label_adjustments": {
  "Marquette": { "x_offset": 0, "y_offset": 12000 },
  "Green Lake": { "x_offset": 0, "y_offset": -12000 }
}
```

Positive `x_offset` moves the label east, positive `y_offset` moves it north. These values are applied when drawing county labels on the map.

## Command-Line Options

Only a configuration file is required; the state name may be overridden on the command line.

```
python generate_state_map.py --config state_config.json [--state-name "State Name"]
```

All other paths and settings are taken from the JSON configuration (see Configuration Files
section above).  The config may specify shapefile, lakes path, abbreviations file, output
file, and whether to clip lakes.

## Output

Each PDF contains:

1. **Map Page**: 
   - County boundaries (optionally clipped at Great Lakes)
   - County names and abbreviations
   - Maidenhead grid square overlay with labels
   - High-resolution (300 DPI)

2. **Table 1**: Counties sorted by name
   - Columns: County | Abbrev | Grid Square

3. **Table 2**: Counties sorted by abbreviation
   - Columns: Abbrev | County | Grid Square

## Workflow for a New State

1. **Create a configuration file**:
   ```bash
   python state_config.py   # Generate a template, then edit it manually
   ```
   Or copy an existing state config and modify it with your state's FIPS code, name, and any custom settings.

2. **Generate the map**:
   ```bash
   python generate_state_map.py --config your_state_config.json
   ```

3. **Review the PDF** and note:
   - Grid squares that are mostly outside the state (to exclude)
   - Grid labels that overlap county names (to adjust)

4. **Refine the configuration** and regenerate until satisfied

## Troubleshooting

- No counties found: verify FIPS code and shapefile path
- Grid labels overlap county names: use `county_label_adjustments`
- Too many grid squares: add exclusions to `exclude_grids`

## Data Attribution

**County Boundaries**: US Census Bureau TIGER/Line Shapefiles (public domain)
**Lake Boundaries**: Natural Earth (public domain, attribution requested)

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

73!
