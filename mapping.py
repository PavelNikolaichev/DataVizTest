from typing import Dict, List, Tuple
import pandas as pd
import folium
from folium import plugins
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import hashlib
from .filter_data import and_filter_subset, filter_subset
from .settings import *


def get_cache_key(address: str) -> str:
    """Generate a cache key for an address."""
    return hashlib.md5(address.lower().strip().encode()).hexdigest()


def geocode_addresses(
    addresses: List[str], progress_callback=None, rate_limit_delay: float = 0
) -> Dict[str, Tuple[float, float]]:
    """
    Geocode a list of addresses using Nominatim (OpenStreetMap).

    Parameters:
    addresses (List[str]): List of address strings to geocode
    progress_callback: Optional callback function for progress updates
    rate_limit_delay (float): Delay between requests to respect rate limits

    Returns:
    Dict[str, Tuple[float, float]]: Dictionary mapping addresses to (lat, lon) coordinates
    """
    global GEOCODE_CACHE

    geolocator = Nominatim(user_agent="DataVizTest_mapping_{}".format(time.time()))
    results = {}

    unique_addresses = list(set(addresses))
    total = len(unique_addresses)

    for i, address in enumerate(unique_addresses):
        if not address or pd.isna(address):
            continue

        # Check cache first
        cache_key = get_cache_key(str(address))
        if cache_key in GEOCODE_CACHE:
            results[address] = GEOCODE_CACHE[cache_key]
            if progress_callback:
                progress_callback(i + 1, total, f"Cached: {address}")
            continue

        try:
            # Add delay to respect rate limits
            if i > 0:
                time.sleep(rate_limit_delay)

            location = geolocator.geocode(str(address), timeout=10)

            if location:
                coords = (location.latitude, location.longitude)
                results[address] = coords
                GEOCODE_CACHE[cache_key] = coords
                if progress_callback:
                    progress_callback(i + 1, total, f"Geocoded: {address}")
            else:
                if progress_callback:
                    progress_callback(i + 1, total, f"Failed: {address}")

        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            if progress_callback:
                progress_callback(i + 1, total, f"Error: {address} - {str(e)}")
            continue
        except Exception as e:
            if progress_callback:
                progress_callback(
                    i + 1, total, f"Unexpected error: {address} - {str(e)}"
                )
            continue

    return results


def create_folium_map(
    df: pd.DataFrame,
    address_column: str,
    value_column: str | None = None,
    grouping_column: str | None = None,
    map_style: str = "OpenStreetMap",
    cluster_markers: bool = True,
    popup_columns: List[str] | None = None,
) -> folium.Map:
    """
    Create an interactive Folium map from geocoded data.

    Parameters:
    df (pd.DataFrame): DataFrame with address and coordinate data
    address_column (str): Column containing addresses
    value_column (str): Optional column for marker sizing/coloring
    grouping_column (str): Optional column for grouping markers
    map_style (str): Base map style
    cluster_markers (bool): Whether to cluster nearby markers
    popup_columns (List[str]): Columns to include in marker popups

    Returns:
    folium.Map: Interactive Folium map
    """
    if popup_columns is None:
        popup_columns = [address_column]

    # Get coordinates for addresses
    addresses = df[address_column].dropna().unique().tolist()
    coords_dict = geocode_addresses(addresses)

    # Filter dataframe to only include successfully geocoded addresses
    df_mapped = df[df[address_column].isin(coords_dict.keys())].copy()

    if df_mapped.empty:
        # Return empty map if no addresses were geocoded
        return folium.Map(location=[0, 0], zoom_start=2)

    # Add coordinate columns
    df_mapped["latitude"] = df_mapped[address_column].map(
        lambda x: coords_dict.get(x, (None, None))[0]
    )
    df_mapped["longitude"] = df_mapped[address_column].map(
        lambda x: coords_dict.get(x, (None, None))[1]
    )

    # Remove rows with missing coordinates
    df_mapped = df_mapped.dropna(subset=["latitude", "longitude"])

    if df_mapped.empty:
        return folium.Map(location=[0, 0], zoom_start=2)

    # Calculate map center
    center_lat = df_mapped["latitude"].mean()
    center_lon = df_mapped["longitude"].mean()

    # Create base map
    tile_options = {
        "OpenStreetMap": None,
        "CartoDB Positron": "CartoDB positron",
        "CartoDB Dark Matter": "CartoDB dark_matter",
        "Stamen Terrain": "Stamen Terrain",
        "Stamen Toner": "Stamen Toner",
    }

    tiles = tile_options.get(map_style, None)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles=tiles)

    # Create marker cluster if requested
    if cluster_markers:
        marker_cluster = plugins.MarkerCluster().add_to(m)
        marker_parent = marker_cluster
    else:
        marker_parent = m

    # Color mapping for groups
    colors = [
        "red",
        "blue",
        "green",
        "purple",
        "orange",
        "darkred",
        "lightred",
        "beige",
        "darkblue",
        "darkgreen",
        "cadetblue",
        "darkpurple",
        "white",
        "pink",
        "lightblue",
        "lightgreen",
        "gray",
        "black",
        "lightgray",
    ]

    if grouping_column and grouping_column in df_mapped.columns:
        unique_groups = df_mapped[grouping_column].unique()
        color_map = {
            group: colors[i % len(colors)] for i, group in enumerate(unique_groups)
        }
    else:
        color_map = {}

    # Add markers
    for idx, row in df_mapped.iterrows():
        lat, lon = row["latitude"], row["longitude"]

        # Create popup content
        popup_content = []
        for col in popup_columns:
            if col in row and pd.notna(row[col]):
                popup_content.append(f"<b>{col}:</b> {row[col]}")

        if value_column and value_column in row and pd.notna(row[value_column]):
            popup_content.append(f"<b>{value_column}:</b> {row[value_column]}")

        popup_html = "<br>".join(popup_content)

        # Determine marker color
        if grouping_column and grouping_column in row:
            color = color_map.get(row[grouping_column], "blue")
        else:
            color = "blue"

        # Determine marker size based on value column
        if (
            value_column
            and value_column in row
            and pd.api.types.is_numeric_dtype(df_mapped[value_column])
        ):
            # Normalize values for marker sizing
            min_val = df_mapped[value_column].min()
            max_val = df_mapped[value_column].max()
            if max_val > min_val:
                normalized_val = (row[value_column] - min_val) / (max_val - min_val)
                radius = 5 + (normalized_val * 15)  # Size between 5 and 20
            else:
                radius = 10

            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=300),
                color="black",
                weight=1,
                fillColor=color,
                fillOpacity=0.7,
            ).add_to(marker_parent)
        else:
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color),
            ).add_to(marker_parent)

    return m


def plot_map_data(
    address_col: str,
    value_col: str | None = None,
    df: pd.DataFrame | None = None,
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str = "sum",
    map_style: str = "OpenStreetMap",
    cluster_markers: bool = True,
) -> folium.Map:
    """
    Create a map plot following the same pattern as other plotting functions.

    Parameters:
    address_col (str): Column containing addresses to plot
    value_col (str): Optional column for marker values
    df (pd.DataFrame): DataFrame containing the data
    groups (List[Tuple[str, list]]): Optional grouping filters
    grouping_type (str): Type of grouping aggregation
    map_style (str): Base map style
    cluster_markers (bool): Whether to cluster markers

    Returns:
    folium.Map: Interactive map visualization
    """
    if df is None:
        raise ValueError("DataFrame cannot be None")

    if groups is None:
        groups = []

    # Apply filters if groups are specified
    if groups:
        if grouping_type in ["sum", "avg"]:
            subset = and_filter_subset(df, groups)
        else:
            # For cluster grouping, we'll handle this differently
            subset = df.copy()
    else:
        subset = df.copy()

    # Determine grouping column for map visualization
    grouping_column = None
    if groups and grouping_type in ["cluster sum", "cluster avg"]:
        # Use the first grouping column for map coloring
        grouping_column = groups[0][0] if groups else None

    # Create popup columns list
    popup_columns = [address_col]
    if value_col and value_col != address_col:
        popup_columns.append(value_col)

    # Add grouping columns to popup
    for group_col, _ in groups:
        if group_col not in popup_columns:
            popup_columns.append(group_col)

    # Create the map
    map_obj = create_folium_map(
        df=subset,
        address_column=address_col,
        value_column=value_col,
        grouping_column=grouping_column,
        map_style=map_style,
        cluster_markers=cluster_markers,
        popup_columns=popup_columns,
    )

    return map_obj


def plot_choropleth_data(
    df: pd.DataFrame,
    location_col: str,
    value_col: str,
    geojson_data: dict | None = None,
) -> go.Figure:
    """
    Create a choropleth map using Plotly for aggregated geographic data.

    Parameters:
    df (pd.DataFrame): DataFrame with location and value data
    location_col (str): Column containing location identifiers
    value_col (str): Column containing values for coloring
    geojson_data (dict): Optional GeoJSON data for boundaries

    Returns:
    go.Figure: Plotly choropleth figure
    """
    # This is a placeholder for choropleth functionality
    # Implementation would depend on available geographic boundary data

    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=geojson_data,
            locations=df[location_col],
            z=df[value_col],
            colorscale="Viridis",
            text=df[location_col],
            hovertemplate="<b>%{text}</b><br>"
            + f"{value_col}: %{df[value_col]}<extra></extra>",
            marker_opacity=0.7,
            marker_line_width=1,
        )
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(center=dict(lat=0, lon=0), zoom=1),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    return fig
