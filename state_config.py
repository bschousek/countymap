"""
State-specific configuration for county map generation.
Allows customization of grid squares to exclude, label adjustments, and abbreviations.
"""

import json
import os


# Default county abbreviations (3-letter codes based on common patterns)
# These are used if no custom abbreviation file is provided
DEFAULT_ABBREVIATIONS = {
    # Common abbreviation patterns:
    # - First 3 letters for short names
    # - First 3 consonants for names with vowels
    # - Unique codes to avoid conflicts
}


def generate_default_abbreviation(county_name):
    """
    Generate a default 3-letter abbreviation for a county.
    
    Parameters:
    county_name: Full county name
    
    Returns:
    3-letter abbreviation
    """
    # Remove common suffixes and clean
    name = county_name.replace(' County', '').replace(' Parish', '').strip()
    
    # Handle special cases
    if ' ' in name:
        # Multi-word names: take first letters of each word
        parts = name.split()
        if len(parts) == 2:
            abbrev = parts[0][0] + parts[1][:2]
        elif len(parts) == 3:
            abbrev = parts[0][0] + parts[1][0] + parts[2][0]
        else:
            abbrev = name[:3]
    else:
        # Single word: take first 3 letters
        abbrev = name[:3]
    
    return abbrev.upper()


class StateConfig:
    """
    Configuration class for state-specific map settings.
    """
    
    def __init__(self, state_name=None, state_fips=None, config_file=None):
        """
        Initialize state configuration.
        
        Parameters:
        state_name: Name of the state (e.g., "Wisconsin")
        state_fips: FIPS code of the state (e.g., "55")
        config_file: Optional path to JSON config file
        """
        self.state_name = state_name
        self.state_fips = state_fips
        
        # Default settings
        self.exclude_grids = []
        self.label_adjustments = {}
        # Per-county label adjustments (keys are county names)
        self.county_label_adjustments = {}
        # Optional per-county display name overrides
        self.county_display_names = {}
        self.custom_abbreviations = {}
        # Path settings and other options stored here for convenience
        self.shapefile = None
        self.lakes = None
        self.abbreviations = None
        self.output = None
        self.no_lakes = False
        
        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file):
        """
        Load configuration from JSON file.
        
        Expected format:
        {
            "state_name": "Wisconsin",
            "state_fips": "55",
            "exclude_grids": ["EN32", "EN33", "EN37", "EN47", "EN57", "EN67"],
            "label_adjustments": {
                "EN45": {"x_offset": 25000, "y_offset": 0},
                "EN54": {"x_offset": 0, "y_offset": 20000}
            },
            "custom_abbreviations": {
                "St. Croix": "STC",
                "Fond du Lac": "FON"
            }
        }
        """
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.state_name = config.get('state_name', self.state_name)
        self.state_fips = config.get('state_fips', self.state_fips)
        self.exclude_grids = [g.upper() for g in config.get('exclude_grids', [])]
        self.label_adjustments = config.get('label_adjustments', {})
        self.county_label_adjustments = config.get('county_label_adjustments', {})
        self.county_display_names = config.get('county_display_names', {})
        # normalize any custom abbreviation keys from the JSON config
        raw = config.get('custom_abbreviations', {})
        self.custom_abbreviations = {}
        for k, v in raw.items():
            # allow multiple spellings separated by semicolons
            for name in [n.strip() for n in k.split(';') if n.strip()]:
                self.custom_abbreviations[name.lower()] = v
        # additional settings
        self.shapefile = config.get('shapefile')
        self.lakes = config.get('lakes')
        self.abbreviations = config.get('abbreviations')
        self.output = config.get('output')
        self.no_lakes = config.get('no_lakes', False)
    
    def save_config(self, config_file):
        """
        Save current configuration to JSON file.
        """
        config = {
            'state_name': self.state_name,
            'state_fips': self.state_fips,
            'exclude_grids': self.exclude_grids,
            'label_adjustments': self.label_adjustments,
            'county_label_adjustments': self.county_label_adjustments,
            'county_display_names': self.county_display_names,
            'custom_abbreviations': self.custom_abbreviations,
            'shapefile': self.shapefile,
            'lakes': self.lakes,
            'abbreviations': self.abbreviations,
            'output': self.output,
            'no_lakes': self.no_lakes
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def add_grid_exclusion(self, grid_square):
        """Add a grid square to the exclusion list."""
        grid_square = grid_square.upper()
        if grid_square not in self.exclude_grids:
            self.exclude_grids.append(grid_square)
    
    def add_label_adjustment(self, grid_square, x_offset=0, y_offset=0):
        """
        Add a label position adjustment for a grid square.
        
        Parameters:
        grid_square: Grid square code (e.g., "EN45")
        x_offset: Horizontal offset in meters (positive = east)
        y_offset: Vertical offset in meters (positive = north)
        """
        grid_square = grid_square.upper()
        self.label_adjustments[grid_square] = {
            'x_offset': x_offset,
            'y_offset': y_offset
        }

    def add_county_label_adjustment(self, county_name, x_offset=0, y_offset=0):
        """
        Add a label position adjustment for a county name.

        Parameters:
        county_name: Exact county name as appears in shapefile (e.g., "Marquette")
        x_offset: Horizontal offset in meters (positive = east)
        y_offset: Vertical offset in meters (positive = north)
        """
        self.county_label_adjustments[county_name] = {
            'x_offset': x_offset,
            'y_offset': y_offset
        }
    
    def get_label_offset(self, grid_square):
        """
        Get label offset for a grid square.
        
        Returns:
        Tuple of (x_offset, y_offset)
        """
        grid_square = grid_square.upper()
        adj = self.label_adjustments.get(grid_square, {})
        return adj.get('x_offset', 0), adj.get('y_offset', 0)

    def get_county_label_offset(self, county_name):
        """
        Get label offset for a county name.

        Returns:
        Tuple of (x_offset, y_offset)
        """
        adj = self.county_label_adjustments.get(county_name, {})
        return adj.get('x_offset', 0), adj.get('y_offset', 0)

    def add_county_display_name(self, county_name, display_name):
        """
        Add or override the display name for a county.
        """
        self.county_display_names[county_name] = display_name

    def get_county_display_name(self, county_name):
        """
        Return the configured display name for a county, or the original name if none provided.
        """
        return self.county_display_names.get(county_name, county_name)
    
    def should_exclude_grid(self, grid_square):
        """Check if a grid square should be excluded."""
        return grid_square.upper() in self.exclude_grids
    
    def get_abbreviation(self, county_name):
        """
        Get abbreviation for a county.

        The lookup is case‑insensitive and honours any alternate spellings
        that were registered via the abbreviations CSV.  When the CSV
        contains multiple names for a row (separated by semicolons) each
        variant will be added to the custom-abbreviations map so that any of
        those spellings return the same abbreviation.
        
        If no custom abbreviation is found, a default 3‑letter code is
        generated.
        """
        key = county_name.strip().lower()
        if key in self.custom_abbreviations:
            return self.custom_abbreviations[key]
        else:
            return generate_default_abbreviation(county_name)
    
    def load_abbreviations_csv(self, csv_file):
        """
        Load abbreviations from a CSV file.

        The first column may contain one or more county names separated by
        semicolons.  Each spelling will map to the same abbreviation, which
        makes it easy to handle alternate names such as
        ``St Croix;St. Croix;Saint Croix``.  Matching is case-insensitive
        and leading/trailing whitespace is stripped.

        Format: county_name[,alias1;alias2...],abbreviation (no headers)
        """
        import pandas as pd
        df = pd.read_csv(csv_file, header=None, names=['County', 'Abbreviation'])
        df['County'] = df['County'].astype(str).str.strip()
        df['Abbreviation'] = df['Abbreviation'].astype(str).str.strip()
        
        for _, row in df.iterrows():
            names = [n.strip() for n in row['County'].split(';') if n.strip()]
            for name in names:
                # store in lowercase for case-insensitive lookup
                self.custom_abbreviations[name.lower()] = row['Abbreviation']


# Predefined configurations for common states
WISCONSIN_CONFIG = StateConfig(state_name="Wisconsin", state_fips="55")
WISCONSIN_CONFIG.exclude_grids = ['EN32', 'EN33', 'EN37', 'EN47', 'EN57', 'EN67']
WISCONSIN_CONFIG.add_label_adjustment('EN45', x_offset=25000, y_offset=0)
WISCONSIN_CONFIG.add_label_adjustment('EN54', x_offset=0, y_offset=20000)
# County-specific nudges to avoid label overlaps
# Marquette: nudge up; Green Lake: nudge down (values in meters)
WISCONSIN_CONFIG.add_county_label_adjustment('Marquette', x_offset=0, y_offset=12000)
WISCONSIN_CONFIG.add_county_label_adjustment('Green Lake', x_offset=0, y_offset=-12000)


def create_config_template(state_name, state_fips, output_file):
    """
    Create a template configuration file for a state.
    
    Parameters:
    state_name: Name of the state
    state_fips: FIPS code
    output_file: Path to save the template
    """
    template = {
        "state_name": state_name,
        "state_fips": state_fips,
        "shapefile": "shapefile/tl_2023_us_county.shp",
        "lakes": "shapefile/ne_10m_lakes.shp",
        "abbreviations": "<state>_abbreviations.csv",
        "output": "<state>_counties.pdf",
        "no_lakes": False,
        "label_adjustments": {
            "# Grid square code": {
                "x_offset": 0,
                "y_offset": 0,
                "# comment": "Positive x = east, positive y = north, units in meters"
            }
        },
        "county_display_names": {
            "# County Name": "Display Name",
            "# Example": "St. Croix"
        },
        "county_label_adjustments": {
            "# County Name": {
                "x_offset": 0,
                "y_offset": 0,
                "# comment": "Positive x = east, positive y = north, units in meters"
            }
        },
        "custom_abbreviations": {
            "# County Name or semicolon-separated list of alternate spellings": "ABR",
            "# Example": "St. Croix;St Croix;Saint Croix: STC"
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"Created template configuration: {output_file}")
    print("Edit this file to customize grid exclusions, label positions, and abbreviations.")


if __name__ == "__main__":
    # Example: Create a configuration template for Minnesota
    create_config_template("Minnesota", "27", "minnesota_config.json")
    
    # Example: Load Wisconsin config
    wi_config = WISCONSIN_CONFIG
    print(f"\nWisconsin Configuration:")
    print(f"  State: {wi_config.state_name}")
    print(f"  FIPS: {wi_config.state_fips}")
    print(f"  Excluded grids: {wi_config.exclude_grids}")
    print(f"  Label adjustments: {wi_config.label_adjustments}")
