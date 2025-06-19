data = None
df = None
filtered_df = None
selections = {}
numerical_attributes = []
categorical_attributes = []
options_list = []
option_value_dictionary = {}
csm = None

GEOCODE_CACHE = {}  # Cache for geocoded addresses to avoid repeated API calls
MAP_SETTINGS = {
    "default_style": "OpenStreetMap",
    "default_cluster": True,
    "rate_limit_delay": 1.0,  # Delay between geocoding requests
    "max_markers": 1000,  # Maximum number of markers to display
}
