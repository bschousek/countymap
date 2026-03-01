"""
Create a PDF with county map and tables for any US state.
Configurable grid exclusions, label adjustments, and abbreviations.
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import os
import sys
import argparse
import maidenhead
import state_config


def load_state_counties(shapefile_path, state_fips):
    """
    Load counties for a specific state from Census Bureau shapefile.
    
    Parameters:
    shapefile_path: Path to the county shapefile
    state_fips: State FIPS code (e.g., "55" for Wisconsin)
    
    Returns:
    GeoDataFrame with state counties including Maidenhead grid squares
    """
    # Read the shapefile
    counties = gpd.read_file(shapefile_path)
    
    # Filter for the specific state
    state_counties = counties[counties['STATEFP'] == state_fips].copy()
    
    if len(state_counties) == 0:
        raise ValueError(f"No counties found for FIPS code {state_fips}")
    
    # Use appropriate projection based on state location
    # For now, use WGS84 Web Mercator, but this can be customized per state
    state_counties = state_counties.to_crs('EPSG:3857')
    
    # Calculate centroids for labels
    state_counties['centroid'] = state_counties.geometry.centroid
    
    # Convert centroids back to lat/lon for Maidenhead calculation
    centroids_wgs84 = state_counties.copy()
    centroids_wgs84['geometry'] = state_counties['centroid']
    centroids_wgs84 = centroids_wgs84.to_crs('EPSG:4326')
    
    # Calculate Maidenhead grid squares
    state_counties['grid_square'] = centroids_wgs84.apply(
        lambda row: maidenhead.latlon_to_maidenhead(
            row.geometry.y, row.geometry.x, precision=4
        ), axis=1
    )
    
    return state_counties


def create_county_map(state_counties, config, output_path='county_map.png', show_land_only=True, 
                     lakes_shapefile=None, target_crs='EPSG:3857'):
    """
    Create a map of state counties with labels and Maidenhead grid.
    
    Parameters:
    state_counties: GeoDataFrame with state counties
    config: StateConfig object with state-specific settings
    output_path: Path to save the map image
    show_land_only: If True, subtract Great Lakes from counties
    lakes_shapefile: Path to Natural Earth lakes shapefile
    target_crs: Target CRS for the map projection
    
    Returns:
    Path to the saved image
    """
    import os
    
    # Create figure with good size
    fig, ax = plt.subplots(1, 1, figsize=(14, 16))
    
    counties_for_labels = state_counties
    
    if show_land_only and lakes_shapefile and os.path.exists(lakes_shapefile):
        try:
            print("   Loading Natural Earth lakes shapefile...")
            lakes = gpd.read_file(lakes_shapefile)
            lakes = lakes.to_crs(target_crs)
            
            # Filter for Great Lakes
            great_lakes = lakes[lakes['name'].isin(['Lake Superior', 'Lake Michigan', 
                                                     'Lake Huron', 'Lake Erie', 'Lake Ontario'])].copy()
            
            if len(great_lakes) > 0:
                print(f"   Found {len(great_lakes)} Great Lakes")
                
                # Dissolve lakes into one geometry
                lakes_union = great_lakes.unary_union
                
                # Subtract lakes from counties
                counties_clipped = state_counties.copy()
                counties_clipped['geometry'] = state_counties.geometry.difference(lakes_union)
                
                print("   Counties clipped at Great Lakes shoreline")
                
                counties_for_labels = counties_clipped
                
                # Plot
                ax.set_facecolor('white')
                counties_clipped.plot(ax=ax, facecolor='lightyellow', edgecolor='black', linewidth=0.8)
            else:
                state_counties.plot(ax=ax, facecolor='lightyellow', edgecolor='black', linewidth=0.8)
                
        except Exception as e:
            print(f"   Warning: Could not load lakes shapefile: {e}")
            state_counties.plot(ax=ax, facecolor='lightyellow', edgecolor='black', linewidth=0.8)
    else:
        state_counties.plot(ax=ax, facecolor='lightyellow', edgecolor='black', linewidth=0.8)
    
    # Add labels for each county
    for idx, row in counties_for_labels.iterrows():
        # Get centroid coordinates
        centroid = row['centroid']
        county_name = row['NAME']

        # Use configured display name when available
        display_name = config.get_county_display_name(county_name)

        # Get abbreviation from config using display name (so custom abbrevs match display)
        abbrev = config.get_abbreviation(display_name)

        # Create label: "Display Name\n(ABBR)"
        label = f"{display_name}\n({abbrev})"
        
        # Add text label at centroid
        # zorder=6 puts it in front of grid lines (zorder=4) but behind grid labels (zorder=11)
        # alpha=0.9 makes it 10% transparent so grid lines show through slightly
        # Apply any county-specific label offset (units = projection units, e.g., meters)
        x_off, y_off = (0, 0)
        try:
            x_off, y_off = config.get_county_label_offset(county_name)
        except Exception:
            x_off, y_off = (0, 0)

        ax.text(centroid.x + x_off, centroid.y + y_off, label, 
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=7,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='gray', alpha=0.9),
                zorder=6)
    
    # Add Maidenhead grid overlay
    print("   Adding Maidenhead grid overlay...")
    
    # Get bounds in WGS84 for grid generation
    bounds_wgs84 = counties_for_labels.to_crs('EPSG:4326').total_bounds
    min_lon, min_lat, max_lon, max_lat = bounds_wgs84
    
    # Plot the grid with state-specific configuration
    # Use lighter lines but keep labels at normal color
    maidenhead.plot_maidenhead_grid_with_config(
        ax, min_lon, min_lat, max_lon, max_lat, 
        crs_proj=target_crs,
        config=config,
        precision=4,
        color='red',
        line_color='#FF9999',  # Lighter red for grid lines
        linewidth=1.5,
        alpha=0.6,
        label_grids=True
    )
    
    print("   Maidenhead grid added")
    
    # Remove axes
    ax.set_axis_off()
    
    # Set title
    state_name = config.state_name or f"State FIPS {config.state_fips}"
    plt.title(f'{state_name} Counties with Abbreviations and Maidenhead Grid Squares', 
              fontsize=18, fontweight='bold', pad=20)
    
    # Adjust layout to minimize whitespace
    plt.tight_layout(pad=0.5)
    
    # Save figure with white background
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def create_pdf(map_image_path, state_counties, config, output_pdf='state_counties.pdf'):
    """
    Create a PDF with the county map and two tables.
    
    Parameters:
    map_image_path: Path to the county map image
    state_counties: GeoDataFrame with state counties
    config: StateConfig object
    output_pdf: Path for the output PDF
    """
    # Create PDF document
    doc = SimpleDocTemplate(output_pdf, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    # Container for PDF elements
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Add title
    state_name = config.state_name or f"State FIPS {config.state_fips}"
    story.append(Paragraph(f"{state_name} Counties Reference Guide", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Add map - calculate size to maintain aspect ratio
    from PIL import Image as PILImage
    img_obj = PILImage.open(map_image_path)
    img_width, img_height = img_obj.size
    aspect_ratio = img_height / img_width
    
    # Use full page width, adjust height to maintain aspect ratio
    target_width = 7*inch
    target_height = target_width * aspect_ratio
    
    # If too tall, scale down
    max_height = 8.5*inch  # Reduced to leave room for attribution
    if target_height > max_height:
        target_height = max_height
        target_width = target_height / aspect_ratio
    
    img = Image(map_image_path, width=target_width, height=target_height)
    story.append(img)
    
    # Add attribution on map page
    story.append(Spacer(1, 0.2*inch))
    
    attribution_style = ParagraphStyle(
        'Attribution',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(
        "Data Sources: County boundaries from US Census Bureau TIGER/Line Shapefiles. "
        "Lake boundaries from Natural Earth (naturalearthdata.com). "
        "Public domain data.",
        attribution_style
    ))
    
    # Page break
    story.append(PageBreak())
    
    # Build county data with grid squares
    county_grid_data = []
    for idx, row in state_counties.iterrows():
        county_name = row['NAME']
        grid = row['grid_square']
        display_name = config.get_county_display_name(county_name)
        abbrev = config.get_abbreviation(display_name)
        county_grid_data.append((display_name, abbrev, grid))
    
    num_counties = len(county_grid_data)
    
    # Determine optimal layout based on number of counties
    # Goal: fit each table on one page (max 2 pages total)
    # Letter page can fit ~35 rows comfortably with current styling
    MAX_ROWS_PER_PAGE = 35
    
    if num_counties <= MAX_ROWS_PER_PAGE:
        # Single column layout - fits on one page
        num_columns = 1
        rows_per_col = num_counties
    elif num_counties <= MAX_ROWS_PER_PAGE * 2:
        # Two column layout - fits on one page
        num_columns = 2
        rows_per_col = (num_counties + 1) // 2
    elif num_counties <= MAX_ROWS_PER_PAGE * 3:
        # Three column layout - fits on one page
        num_columns = 3
        rows_per_col = (num_counties + 2) // 3
    else:
        # Four column layout for states with many counties
        num_columns = 4
        rows_per_col = (num_counties + 3) // 4
    
    # Calculate column widths based on number of columns
    # Reduce widths slightly to prevent overflow
    # Table 1: County (wide) | Abbrev (narrow) | Grid (narrow)
    if num_columns == 1:
        table1_col_widths = [2.8*inch, 0.6*inch, 0.6*inch]
        table2_col_widths = [0.6*inch, 2.8*inch, 0.6*inch]
    elif num_columns == 2:
        table1_col_widths = [1.7*inch, 0.45*inch, 0.45*inch, 0.15*inch, 
                            1.7*inch, 0.45*inch, 0.45*inch]
        table2_col_widths = [0.45*inch, 1.7*inch, 0.45*inch, 0.15*inch,
                            0.45*inch, 1.7*inch, 0.45*inch]
    elif num_columns == 3:
        table1_col_widths = [1.3*inch, 0.35*inch, 0.35*inch, 0.1*inch,
                            1.3*inch, 0.35*inch, 0.35*inch, 0.1*inch,
                            1.3*inch, 0.35*inch, 0.35*inch]
        table2_col_widths = [0.35*inch, 1.3*inch, 0.35*inch, 0.1*inch,
                            0.35*inch, 1.3*inch, 0.35*inch, 0.1*inch,
                            0.35*inch, 1.3*inch, 0.35*inch]
    else:  # 4 columns
        table1_col_widths = [1.0*inch, 0.3*inch, 0.3*inch, 0.08*inch,
                            1.0*inch, 0.3*inch, 0.3*inch, 0.08*inch,
                            1.0*inch, 0.3*inch, 0.3*inch, 0.08*inch,
                            1.0*inch, 0.3*inch, 0.3*inch]
        table2_col_widths = [0.3*inch, 1.0*inch, 0.3*inch, 0.08*inch,
                            0.3*inch, 1.0*inch, 0.3*inch, 0.08*inch,
                            0.3*inch, 1.0*inch, 0.3*inch, 0.08*inch,
                            0.3*inch, 1.0*inch, 0.3*inch]
    
    # ==================== Table 1: Sorted by County Name ====================
    story.append(Paragraph("Counties Sorted Alphabetically by Name", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    sorted_by_name = sorted(county_grid_data, key=lambda x: x[0])
    
    # Build header row
    header_row = []
    for i in range(num_columns):
        header_row.extend(['County', 'Abbrev', 'Grid'])
        if i < num_columns - 1:
            header_row.append('')  # Spacer
    table1_data = [header_row]
    
    # Build data rows
    for i in range(rows_per_col):
        row = []
        for col in range(num_columns):
            idx = col * rows_per_col + i
            if idx < num_counties:
                county, abbrev, grid = sorted_by_name[idx]
                # Wrap county name in Paragraph for word wrapping
                county_para = Paragraph(county, styles['Normal'])
                row.extend([county_para, abbrev, grid])
            else:
                row.extend(['', '', ''])
            
            if col < num_columns - 1:
                row.append('')  # Spacer
        
        table1_data.append(row)
    
    table1 = Table(table1_data, colWidths=table1_col_widths)
    
    # Build style commands dynamically based on number of columns
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Add alignment and grid for each column group
    for col in range(num_columns):
        base_col = col * 4  # Each group is 4 columns wide (3 data + 1 spacer)
        # County column - left align
        style_commands.append(('ALIGN', (base_col, 1), (base_col, -1), 'LEFT'))
        # Abbrev and Grid columns - center align
        style_commands.append(('ALIGN', (base_col + 1, 1), (base_col + 2, -1), 'CENTER'))
        # Grid lines for this column group
        if col < num_columns - 1:
            style_commands.append(('GRID', (base_col, 0), (base_col + 2, -1), 0.5, colors.grey))
        else:
            # Last column - no spacer after it
            last_col = base_col + 2
            style_commands.append(('GRID', (base_col, 0), (last_col, -1), 0.5, colors.grey))
    
    table1.setStyle(TableStyle(style_commands))
    story.append(table1)
    story.append(PageBreak())
    
    # ==================== Table 2: Sorted by Abbreviation ====================
    story.append(Paragraph("Counties Sorted Alphabetically by Abbreviation", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    sorted_by_abbrev = sorted(county_grid_data, key=lambda x: x[1])
    
    # Build header row
    header_row = []
    for i in range(num_columns):
        header_row.extend(['Abbrev', 'County', 'Grid'])
        if i < num_columns - 1:
            header_row.append('')  # Spacer
    table2_data = [header_row]
    
    # Build data rows
    for i in range(rows_per_col):
        row = []
        for col in range(num_columns):
            idx = col * rows_per_col + i
            if idx < num_counties:
                county, abbrev, grid = sorted_by_abbrev[idx]
                # Wrap county name in Paragraph for word wrapping
                county_para = Paragraph(county, styles['Normal'])
                row.extend([abbrev, county_para, grid])
            else:
                row.extend(['', '', ''])
            
            if col < num_columns - 1:
                row.append('')  # Spacer
        
        table2_data.append(row)
    
    table2 = Table(table2_data, colWidths=table2_col_widths)
    
    # Build style commands for table 2
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Add alignment and grid for each column group
    for col in range(num_columns):
        base_col = col * 4  # Each group is 4 columns wide
        # Abbrev and Grid columns - center align
        style_commands.append(('ALIGN', (base_col, 1), (base_col, -1), 'CENTER'))
        style_commands.append(('ALIGN', (base_col + 2, 1), (base_col + 2, -1), 'CENTER'))
        # County column - left align
        style_commands.append(('ALIGN', (base_col + 1, 1), (base_col + 1, -1), 'LEFT'))
        # Grid lines for this column group
        if col < num_columns - 1:
            style_commands.append(('GRID', (base_col, 0), (base_col + 2, -1), 0.5, colors.grey))
        else:
            # Last column - no spacer after it
            last_col = base_col + 2
            style_commands.append(('GRID', (base_col, 0), (last_col, -1), 0.5, colors.grey))
    
    table2.setStyle(TableStyle(style_commands))
    story.append(table2)
    
    # Build PDF with custom page template for copyright footer
    def add_page_footer(canvas, doc):
        """Add copyright footer to each page"""
        canvas.saveState()
        footer_text = "Copyright 2026 Brian Schousek KB9TBB"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(letter[0] / 2, 0.5*inch, footer_text)
        canvas.restoreState()
    
    doc.build(story, onFirstPage=add_page_footer, onLaterPages=add_page_footer)
    
    print(f"\nPDF created successfully: {output_pdf}")


def main():
    """
    Main function with command-line argument support.
    """
    parser = argparse.ArgumentParser(
        description='Generate county map PDF for any US state; most settings come from a JSON config.'
    )
    parser.add_argument('--state-name', help='State name (e.g., Wisconsin)')
    parser.add_argument('--config', help='Path to state configuration JSON file', required=True)
    
    args = parser.parse_args()
    
    print("=" * 80)
    # once configuration is loaded below we will print the FIPS
    print("County Map Generator")
    print("=" * 80)

    # Load configuration (required)
    config = state_config.StateConfig(config_file=args.config)

    # Allow --state-name to override config state name
    if args.state_name:
        config.state_name = args.state_name

    print(f"Configuration loaded for state FIPS {config.state_fips} ({config.state_name})")

    # slug based on final state name
    state_slug = (config.state_name or f"state_{config.state_fips}").lower().replace(' ', '_')

    # determine file paths from config or defaults
    shapefile = config.shapefile or 'shapefile/tl_2023_us_county.shp'
    lakes_file = config.lakes or 'shapefile/ne_10m_lakes.shp'
    abbrev_path = config.abbreviations or f"{state_slug}_abbreviations.csv"
    output_pdf = config.output or f"{state_slug}_counties.pdf"
    map_image_default = f"{state_slug}_county_map.png"
    show_lakes = not config.no_lakes

    # load abbreviations if file exists
    if abbrev_path and os.path.exists(abbrev_path):
        print(f"\nLoading custom abbreviations from: {abbrev_path}")
        config.load_abbreviations_csv(abbrev_path)
    
    # Load state counties
    print(f"\nStep 1: Loading counties for FIPS {config.state_fips}...")
    state_counties = load_state_counties(shapefile, config.state_fips)
    print(f"   Loaded {len(state_counties)} counties")
    
    # Create map
    print("\nStep 2: Creating county map with labels and Maidenhead grid...")
    map_path = create_county_map(
        state_counties, config,
        output_path=os.path.join('output', map_image_default),
        show_land_only=show_lakes,
        lakes_shapefile=lakes_file if show_lakes else None
    )
    print(f"   Map saved to: {map_path}")
    
    # Create PDF
    print("\nStep 3: Generating PDF with map and tables...")
    create_pdf(map_path, state_counties, config, output_pdf)
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)
    print(f"\nOutput file: {output_pdf}")
    print("\nThe PDF contains:")
    print("  - Page 1: County map with names, abbreviations, and Maidenhead grid")
    print("  - Page 2: Table sorted alphabetically by county name")
    print("  - Page 3: Table sorted alphabetically by abbreviation")
    
    # Suggest creating a config template if you want to start fresh
    config_suggestion = f"{state_slug}_config.json"
    print(f"\nTip: Create a configuration file to customize grid exclusions and label positions:")
    print(f"  python state_config.py --create {config_suggestion} --state-name '{config.state_name or 'Your State'}' --state-fips {config.state_fips}")


if __name__ == "__main__":
    main()