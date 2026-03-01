# State Configuration Files

This directory contains JSON configuration files for all 50 US states. Each state has:

- `{state}_config.json` — Main configuration file with grid exclusions, label adjustments, abbreviations, etc.
- `{state}_abbreviations.csv` — County abbreviation mappings (empty placeholders for most states)

## Customization Status

States listed below with status indicators:

| State | Status | Notes |
|-------|--------|-------|
| Alabama | — | Template only |
| Alaska | — | Template only |
| Arizona | — | Template only |
| Arkansas | — | Template only |
| California | — | Template only |
| Colorado | — | Template only |
| Connecticut | — | Template only |
| Delaware | — | Template only |
| Florida | — | Template only |
| Georgia | — | Template only |
| Hawaii | — | Template only |
| Idaho | — | Template only |
| Illinois | — | Template only |
| Indiana | — | Template only |
| Iowa | — | Template only |
| Kansas | — | Template only |
| Kentucky | — | Template only |
| Louisiana | — | Template only |
| Maine | — | Template only |
| Maryland | — | Template only |
| Massachusetts | — | Template only |
| Michigan | — | Template only |
| Minnesota | — | Template only |
| Mississippi | — | Template only |
| Missouri | — | Template only |
| Montana | — | Template only |
| Nebraska | — | Template only |
| Nevada | — | Template only |
| New Hampshire | — | Template only |
| New Jersey | — | Template only |
| New Mexico | — | Template only |
| New York | — | Template only |
| North Carolina | — | Template only |
| North Dakota | — | Template only |
| Ohio | — | Template only |
| Oklahoma | — | Template only |
| Oregon | — | Template only |
| Pennsylvania | — | Template only |
| Rhode Island | — | Template only |
| South Carolina | — | Template only |
| South Dakota | — | Template only |
| Tennessee | — | Template only |
| Texas | — | Template only |
| Utah | — | Template only |
| Vermont | — | Template only |
| Virginia | — | Template only |
| Washington | — | Template only |
| West Virginia | — | Template only |
| **Wisconsin** | **✓ Customized** | Includes grid exclusions, label adjustments, and county abbreviations with alternate spellings |
| Wyoming | — | Template only |

## Editing a State Configuration

1. Open `{state}_config.json` in your editor
2. Update fields as needed:
   - `exclude_grids`: List of Maidenhead grid squares to hide
   - `label_adjustments`: Grid label offsets to avoid overlaps
   - `county_label_adjustments`: County name offsets to avoid overlaps
   - `county_display_names`: Override display names for counties
   - `custom_abbreviations`: County abbreviations (supports alternate spellings separated by `;`)
3. Add county abbreviations to `{state}_abbreviations.csv` if using a CSV file
4. Run: `python generate_state_map.py --config config/{state}_config.json`

## Format Examples

### Grid label adjustment
```json
"label_adjustments": {
  "EN45": {"x_offset": 25000, "y_offset": 0}
}
```

### County with alternate spellings
```json
"custom_abbreviations": {
  "St. Croix;St Croix;Saint Croix": "STC"
}
```

### CSV abbreviations format
```
County Name,ABR
St. Croix;St Croix;Saint Croix,STC
```
