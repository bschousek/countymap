"""
Maidenhead Grid Square utilities for ham radio mapping.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def latlon_to_maidenhead(lat, lon, precision=4):
    """
    Convert latitude/longitude to Maidenhead grid square locator.
    
    Parameters:
    lat: Latitude in degrees
    lon: Longitude in degrees
    precision: Number of characters (2, 4, 6, or 8)
    
    Returns:
    Maidenhead grid square string (e.g., "EN52")
    """
    # Adjust longitude to 0-360 range
    adj_lon = lon + 180
    adj_lat = lat + 90
    
    # Field (first two characters - letters)
    field_lon = int(adj_lon / 20)
    field_lat = int(adj_lat / 10)
    maidenhead = chr(ord('A') + field_lon) + chr(ord('A') + field_lat)
    
    if precision >= 4:
        # Square (next two characters - digits)
        square_lon = int((adj_lon % 20) / 2)
        square_lat = int((adj_lat % 10) / 1)
        maidenhead += str(square_lon) + str(square_lat)
    
    if precision >= 6:
        # Subsquare (next two characters - letters)
        subsquare_lon = int((adj_lon % 2) * 12)
        subsquare_lat = int((adj_lat % 1) * 24)
        maidenhead += chr(ord('a') + subsquare_lon) + chr(ord('a') + subsquare_lat)
    
    if precision >= 8:
        # Extended square (next two characters - digits)
        ext_lon = int((adj_lon % (1/6)) * 120)
        ext_lat = int((adj_lat % (1/12)) * 240)
        maidenhead += str(ext_lon) + str(ext_lat)
    
    return maidenhead


def maidenhead_to_latlon(grid_square):
    """
    Convert Maidenhead grid square to center lat/lon.
    
    Parameters:
    grid_square: Maidenhead locator string (e.g., "EN52")
    
    Returns:
    Tuple of (latitude, longitude) for grid square center
    """
    grid_square = grid_square.upper()
    
    # Field (first two characters)
    lon = (ord(grid_square[0]) - ord('A')) * 20 - 180
    lat = (ord(grid_square[1]) - ord('A')) * 10 - 90
    
    if len(grid_square) >= 4:
        # Square
        lon += int(grid_square[2]) * 2
        lat += int(grid_square[3]) * 1
        # Center of square
        lon += 1
        lat += 0.5
    else:
        # Center of field
        lon += 10
        lat += 5
    
    if len(grid_square) >= 6:
        # Subsquare
        lon += (ord(grid_square[4].upper()) - ord('A')) * (2/24) + (1/24)
        lat += (ord(grid_square[5].upper()) - ord('A')) * (1/24) + (1/48)
    
    return lat, lon


def get_grid_square_bounds(grid_square):
    """
    Get the bounding box for a Maidenhead grid square.
    
    Parameters:
    grid_square: Maidenhead locator string (e.g., "EN52")
    
    Returns:
    Tuple of (min_lon, min_lat, max_lon, max_lat)
    """
    grid_square = grid_square.upper()
    
    # Field (first two characters)
    min_lon = (ord(grid_square[0]) - ord('A')) * 20 - 180
    min_lat = (ord(grid_square[1]) - ord('A')) * 10 - 90
    
    if len(grid_square) >= 4:
        # Square
        min_lon += int(grid_square[2]) * 2
        min_lat += int(grid_square[3]) * 1
        max_lon = min_lon + 2
        max_lat = min_lat + 1
    else:
        # Field
        max_lon = min_lon + 20
        max_lat = min_lat + 10
    
    if len(grid_square) >= 6:
        # Subsquare
        min_lon += (ord(grid_square[4].upper()) - ord('A')) * (2/24)
        min_lat += (ord(grid_square[5].upper()) - ord('A')) * (1/24)
        max_lon = min_lon + (2/24)
        max_lat = min_lat + (1/24)
    
    return min_lon, min_lat, max_lon, max_lat


def generate_grid_squares_for_bbox(min_lon, min_lat, max_lon, max_lat, precision=4):
    """
    Generate all grid squares that intersect with a bounding box.
    
    Parameters:
    min_lon, min_lat, max_lon, max_lat: Bounding box
    precision: Grid square precision (4 or 6 characters)
    
    Returns:
    List of grid square strings
    """
    grid_squares = []
    
    if precision == 4:
        # Generate 4-character grid squares (fields and squares)
        # Each square is 2 degrees lon x 1 degree lat
        
        # Expand bounds slightly to ensure coverage
        start_lon = np.floor(min_lon / 2) * 2
        end_lon = np.ceil(max_lon / 2) * 2
        start_lat = np.floor(min_lat / 1) * 1
        end_lat = np.ceil(max_lat / 1) * 1
        
        lon = start_lon
        while lon < end_lon:
            lat = start_lat
            while lat < end_lat:
                # Convert to maidenhead
                grid = latlon_to_maidenhead(lat + 0.5, lon + 1, precision=4)
                if grid not in grid_squares:
                    grid_squares.append(grid)
                lat += 1
            lon += 2
    
    return grid_squares


def plot_maidenhead_grid(ax, min_lon, min_lat, max_lon, max_lat, crs_proj, precision=4, 
                         color='red', linewidth=1, alpha=0.5, label_grids=True, land_boundary=None):
    """
    Plot Maidenhead grid squares on a matplotlib axis.
    
    Parameters:
    ax: Matplotlib axis
    min_lon, min_lat, max_lon, max_lat: Bounds in lat/lon (EPSG:4326)
    crs_proj: Target CRS for projection (e.g., 'EPSG:3070')
    precision: Grid square precision (4 or 6)
    color: Grid line color
    linewidth: Grid line width
    alpha: Grid transparency
    label_grids: If True, add grid square labels
    land_boundary: Optional GeoDataFrame geometry to clip grid lines to land
    """
    import geopandas as gpd
    from shapely.geometry import box, Point
    
    # Grids to exclude
    exclude_grids = ['EN32', 'EN33', 'EN37', 'EN47', 'EN57', 'EN67']
    
    # Generate grid squares
    grid_squares = generate_grid_squares_for_bbox(min_lon, min_lat, max_lon, max_lat, precision)
    
    for grid in grid_squares:
        # Skip excluded grids
        if grid.upper() in exclude_grids:
            continue
            
        # Get bounds
        gs_min_lon, gs_min_lat, gs_max_lon, gs_max_lat = get_grid_square_bounds(grid)
        
        # Create rectangle in WGS84
        rect_wgs84 = box(gs_min_lon, gs_min_lat, gs_max_lon, gs_max_lat)
        
        # Convert to target projection
        gdf = gpd.GeoDataFrame({'geometry': [rect_wgs84]}, crs='EPSG:4326')
        gdf = gdf.to_crs(crs_proj)
        
        # Clip to land boundary if provided
        if land_boundary is not None:
            clipped_geom = gdf.geometry.iloc[0].intersection(land_boundary)
            gdf = gpd.GeoDataFrame({'geometry': [clipped_geom]}, crs=crs_proj)
        
        # Plot rectangle boundary
        gdf.boundary.plot(ax=ax, color=color, linewidth=linewidth, alpha=alpha, zorder=10)
        
        # Add label if requested
        if label_grids:
            # Get center point
            center_lat, center_lon = maidenhead_to_latlon(grid)
            center_wgs84 = Point(center_lon, center_lat)
            
            # Convert to target projection
            center_gdf = gpd.GeoDataFrame({'geometry': [center_wgs84]}, crs='EPSG:4326')
            center_gdf = center_gdf.to_crs(crs_proj)
            center_point = center_gdf.geometry.iloc[0]
            
            # Special adjustments for specific grids to avoid county name overlap
            x_offset = 0
            y_offset = 0
            
            if grid.upper() == 'EN45':
                x_offset = 25000  # Nudge right by 25km to avoid Rusk
            elif grid.upper() == 'EN54':
                y_offset = 20000  # Nudge up by 20km to avoid Waupaca
            
            # Add text label
            ax.text(center_point.x + x_offset, center_point.y + y_offset, grid,
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=8,
                   fontweight='bold',
                   color=color,
                   alpha=0.7,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                            edgecolor=color, alpha=0.6),
                   zorder=11)


def plot_maidenhead_grid_with_config(ax, min_lon, min_lat, max_lon, max_lat, crs_proj, config,
                                     precision=4, color='red', line_color=None, linewidth=1, alpha=0.5, label_grids=True):
    """
    Plot Maidenhead grid squares on a matplotlib axis using StateConfig.
    
    Parameters:
    ax: Matplotlib axis
    min_lon, min_lat, max_lon, max_lat: Bounds in lat/lon (EPSG:4326)
    crs_proj: Target CRS for projection (e.g., 'EPSG:3070')
    config: StateConfig object with exclusions and label adjustments
    precision: Grid square precision (4 or 6)
    color: Grid label color
    line_color: Grid line color (if None, uses color parameter)
    linewidth: Grid line width
    alpha: Grid transparency
    label_grids: If True, add grid square labels
    """
    import geopandas as gpd
    from shapely.geometry import box, Point
    
    # If no separate line color specified, use main color
    if line_color is None:
        line_color = color
    
    # Generate grid squares
    grid_squares = generate_grid_squares_for_bbox(min_lon, min_lat, max_lon, max_lat, precision)
    
    for grid in grid_squares:
        # Skip excluded grids from config
        if config.should_exclude_grid(grid):
            continue
            
        # Get bounds
        gs_min_lon, gs_min_lat, gs_max_lon, gs_max_lat = get_grid_square_bounds(grid)
        
        # Create rectangle in WGS84
        rect_wgs84 = box(gs_min_lon, gs_min_lat, gs_max_lon, gs_max_lat)
        
        # Convert to target projection
        gdf = gpd.GeoDataFrame({'geometry': [rect_wgs84]}, crs='EPSG:4326')
        gdf = gdf.to_crs(crs_proj)
        
        # Plot rectangle boundary with line color
        gdf.boundary.plot(ax=ax, color=line_color, linewidth=linewidth, alpha=alpha, zorder=4)
        
        # Add label if requested
        if label_grids:
            # Get center point
            center_lat, center_lon = maidenhead_to_latlon(grid)
            center_wgs84 = Point(center_lon, center_lat)
            
            # Convert to target projection
            center_gdf = gpd.GeoDataFrame({'geometry': [center_wgs84]}, crs='EPSG:4326')
            center_gdf = center_gdf.to_crs(crs_proj)
            center_point = center_gdf.geometry.iloc[0]
            
            # Get label offset from config
            x_offset, y_offset = config.get_label_offset(grid)
            
            # Add text label with main color (not line_color)
            ax.text(center_point.x + x_offset, center_point.y + y_offset, grid,
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=8,
                   fontweight='bold',
                   color=color,
                   alpha=0.7,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                            edgecolor=color, alpha=0.6),
                   zorder=11)


if __name__ == "__main__":
    # Test the functions
    print("Testing Maidenhead Grid Square utilities")
    print("=" * 50)
    
    # Test location: Madison, WI
    lat, lon = 43.0731, -89.4012
    grid = latlon_to_maidenhead(lat, lon, precision=4)
    print(f"\nMadison, WI: ({lat}, {lon})")
    print(f"Grid square: {grid}")
    
    # Convert back
    center_lat, center_lon = maidenhead_to_latlon(grid)
    print(f"Grid center: ({center_lat}, {center_lon})")
    
    # Get bounds
    bounds = get_grid_square_bounds(grid)
    print(f"Grid bounds: {bounds}")
    
    # Test a few more Wisconsin locations
    locations = [
        ("Milwaukee", 43.0389, -87.9065),
        ("Green Bay", 44.5133, -88.0133),
        ("La Crosse", 43.8014, -91.2396)
    ]
    
    print("\n" + "=" * 50)
    print("Wisconsin Cities and their Grid Squares:")
    print("=" * 50)
    
    for city, lat, lon in locations:
        grid = latlon_to_maidenhead(lat, lon, precision=4)
        print(f"{city:15s} ({lat:7.3f}, {lon:8.3f}) -> {grid}")