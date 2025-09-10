# DataVizTest - Copilot Instructions

## Repository Summary

DataVizTest is a **data visualization application specifically designed for Google Colab environments**. The project provides an interactive data exploration and visualization tool built primarily around **plotly**, **pandas**, and **ipywidgets**, with specialized support for **IPUMS demographic data**. Originally developed as a Jupyter notebook, it has been refactored into a modular Python package while maintaining its Colab-centric design.

### High-Level Repository Information

- **Size**: 13 Python files, ~3,600 lines of code total
- **Main entry point**: `__init__.py` (1,719 lines - contains primary application logic)
- **Project type**: Interactive data visualization library for Google Colab
- **Languages**: Python 3.12+
- **Frameworks**: 
  - **plotly** 5.15.0 (primary visualization)
  - **pandas** 1.5.3 (data manipulation)
  - **ipywidgets** 7.7.1 (interactive UI components)
  - **geopandas** 0.14.4 (geospatial data)
  - **folium** 0.12.0 (mapping)
  - **matplotlib** 3.7.1 (additional plotting)
- **Target runtime**: Google Colab environment only
- **Data integration**: IPUMS data loader (ipumspy 0.5.1), nl4ds library

## Environment Setup and Dependencies

### Critical Prerequisites
⚠️ **This application REQUIRES Google Colab environment** - it will not run in standard Python environments due to:
1. `from google.colab import output, drive, files` imports
2. `drive.mount("/content/drive")` filesystem integration
3. Google Colab-specific widget management: `output.enable_custom_widget_manager()`

### Installation Process

**In Google Colab (the only supported environment):**

1. **Install dependencies**:
   ```python
   !pip install --quiet ipumspy
   !pip install geopandas
   !pip install --quiet pandas==1.5.3
   !pip install -U folium matplotlib mapclassify
   !pip install pydeck
   !pip install --quiet pyarrow
   !pip install --quiet pydeck
   ```

2. **Mount Google Drive** (automatically handled by the application):
   ```python
   from google.colab import drive
   drive.mount("/content/drive")
   ```

3. **Import and run**:
   ```python
   from DataVizTest import run
   import pandas as pd
   
   # Load your data
   data = pd.read_csv("your_data.csv")
   run(data)
   ```

### Environment Validation
- **Runtime**: Google Colab only
- **Python version**: 3.12+ (tested with 3.12.3)
- **Memory requirements**: Variable based on dataset size
- **Network**: Requires internet for geocoding services (Nominatim)

## Project Architecture and Layout

### Core Application Structure

**Primary entry points:**
- `__init__.py` - Main application logic, widget definitions, data processing workflow
- `__main__.py` - Standalone execution example (minimal usage)

**Key modules:**
- `ui.py` (443 lines) - User interface components and interaction handlers
- `plotting.py` (409 lines) - Visualization functions (scatter, bar, box plots)
- `mapping.py` (356 lines) - Geospatial visualization and geocoding
- `data_processing.py` (339 lines) - Data filtering and transformation
- `ClientStateMachine.py` (36 lines) - Application state management
- `settings.py` (17 lines) - Global configuration variables

**Supporting modules:**
- `describe_data.py` (96 lines) - Statistical summaries and count tables
- `filter_data.py` (68 lines) - DataFrame filtering utilities
- `export_data.py` (39 lines) - Data export functionality
- `widgets/FilterOptionWidget.py` - Custom UI widget for filter management
- `selection.py` (0 lines) - Empty placeholder file
- `geo_functions.py` (1 line) - Minimal placeholder

### Application Workflow
The application follows a state-machine pattern with these states:
1. **State Choosing** - Initial menu selection
2. **Make Selection** - Data filtering and subset creation
3. **Describe Selection** - Statistical analysis display
4. **Plot Selection** - Visualization generation

### Global State Management
Key global variables in `settings.py`:
- `data` - Main DataFrame
- `filtered_df` - Current filtered subset
- `selections` - User-defined filters
- `numerical_attributes`/`categorical_attributes` - Column classifications
- `GEOCODE_CACHE` - Cached geocoding results
- `MAP_SETTINGS` - Default mapping configuration

## Build, Test, and Validation

### No Traditional Build System
This project does **not** use conventional build tools (setup.py, pyproject.toml, Makefile) as it's designed as a Colab-native library.

### Testing Infrastructure
**No formal test suite exists**. Validation should be done through:

1. **Import testing**:
   ```python
   # Will fail outside Colab
   from DataVizTest import run
   ```

2. **Basic functionality test**:
   ```python
   import pandas as pd
   data = pd.DataFrame({'x': [1,2,3], 'y': [4,5,6]})
   run(data)  # Should display interactive UI
   ```

3. **Module import verification**:
   ```python
   from DataVizTest.plotting import x_y_scatter
   from DataVizTest.mapping import geocode_addresses
   from DataVizTest.filter_data import filter_dataframe
   ```

### Manual Validation Steps
1. **Data loading**: Test with sample CSV/Excel files
2. **Widget interaction**: Verify dropdown menus, sliders, and buttons respond
3. **Visualization rendering**: Confirm plotly charts display correctly
4. **Geocoding**: Test address geocoding with sample data
5. **Export functionality**: Verify Excel download works

### Known Limitations and Workarounds
- **Non-Colab environments**: Application will fail immediately with import errors
- **Large datasets**: May hit Colab memory limits (no specific threshold documented)
- **Geocoding rate limits**: Built-in delays for Nominatim API (1.0s default)
- **Widget display**: Requires `output.enable_custom_widget_manager()` in Colab

## Development Guidelines

### Code Style and Standards
- **No formal linting** configuration present (no .flake8, .pylintrc, etc.)
- **No pre-commit hooks** or GitHub workflows configured
- **Import style**: Mix of absolute and relative imports (inconsistent)
- **Documentation**: Minimal docstrings, primarily in mapping.py and plotting.py

### Making Changes

**High-impact files** (change carefully):
- `__init__.py` - Core application logic
- `ui.py` - Main interface components
- `settings.py` - Global state variables

**Safe modification files**:
- Individual visualization functions in `plotting.py`
- Utility functions in `data_processing.py`
- Widget components in `widgets/`

### Common Development Tasks

**Adding new visualizations**:
1. Create function in `plotting.py` following existing patterns
2. Add UI controls in `ui.py`
3. Update state machine transitions if needed

**Adding new data sources**:
1. Extend data loading in `__init__.py`
2. Update data processing pipeline in `data_processing.py`
3. Modify global state in `settings.py` if needed

**Modifying UI components**:
1. Edit widget definitions in `ui.py`
2. Test widget interactions in Colab environment
3. Update callback functions as needed

### File Dependencies Map
```
__init__.py
├── settings.py (global state)
├── ui.py (main interface)
├── plotting.py (visualizations)
├── mapping.py (geospatial)
├── data_processing.py (data handling)
├── ClientStateMachine.py (state management)
└── widgets/FilterOptionWidget.py (custom UI)
```

### Configuration Files
- `requirements.txt` - Dependency specification (15 packages)
- `.gitignore` - Standard Python exclusions plus VSCode settings

## Key Facts for Efficient Development

### Architecture Patterns
- **Monolithic design**: Most logic concentrated in `__init__.py`
- **Global state**: Heavy reliance on module-level variables
- **Widget-based UI**: ipywidgets for all user interactions
- **Functional style**: 156 functions across 13 files, minimal OOP

### Data Flow
1. Data loaded via `run(dataframe)` function
2. Global variables initialized (attributes classified)
3. Interactive UI displayed via `main_menu()`
4. User selections stored in global `selections` dict
5. Filtered data generated on-demand
6. Visualizations created with plotly/folium

### Integration Points
- **IPUMS integration**: `nl4ds.chatipums` and `ipumspy` for demographic data
- **Google Drive**: Mounted at `/content/drive` for data access
- **Geocoding**: Nominatim (OpenStreetMap) for address conversion
- **Export**: Google Colab's `files.download()` for data export

## Trust These Instructions

These instructions provide comprehensive coverage of the DataVizTest repository structure, dependencies, and development patterns. **Trust this documentation** and only perform additional searches if:
- Information appears outdated or contradictory
- You need specific implementation details not covered
- You encounter errors not explained in the limitations section

The repository analysis is complete and accurate as of the documentation date.