"""
DataVizTest - Data Visualization Tool
"""

# Basic imports for the module
import os
import sys
from warnings import simplefilter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display, clear_output

# Colab-specific imports
from google.colab import output, drive
from nl4ds.chatipums import *
from nl4ds.eda_functions import *

# Local module imports
from .settings import *
from .ClientStateMachine import ClientStateMachine
from .ui import main_menu

# Mount Google Drive for Colab environment
drive.mount("/content/drive")

# Enable custom widget manager for Colab
output.enable_custom_widget_manager()

# Configure matplotlib and pandas display settings
plt.rcParams["figure.dpi"] = 120
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


def run(_data: pd.DataFrame):
    """
    Main entry point for the data visualization tool.
    
    Args:
        _data: A pandas DataFrame to visualize
    """
    if not isinstance(_data, pd.DataFrame):
        raise ValueError(
            "You must initialize global variable `data`. It must be a pandas DataFrame instance"
        )

    # Initialize global variables
    global filtered_df, selections, numerical_attributes, categorical_attributes, csm, data, options_list, option_value_dictionary
    
    data = _data
    filtered_df = None
    selections = {}

    # Initialize state machine
    csm = ClientStateMachine()
    
    # Determine data types for columns
    numerical_attributes = (
        data.select_dtypes(include=[np.number]).columns.sort_values().tolist()
    )
    categorical_attributes = (
        data.select_dtypes(exclude=[np.number]).columns.sort_values().tolist()
    )

    # Create options list and value dictionary for UI components
    options_list = data.columns.sort_values().tolist()
    option_value_dictionary = {}
    
    for attribute in data.columns:
        option_values = data[attribute].unique()

        try:
            # Handle NaN values
            if float("nan") or np.nan or pd.NA in option_values:
                option_values = option_values[~pd.isna(option_values)]
                nan_ind = np.where(option_values == "nan")[0]
                if nan_ind.size > 0:
                    option_values = np.delete(option_values, nan_ind[0])
                option_value_dictionary[attribute] = tuple(["nan"]) + tuple(
                    sorted(option_values)
                )
            else:
                option_value_dictionary[attribute] = tuple(sorted(option_values))
        except Exception as _:
            option_value_dictionary[attribute] = tuple(option_values)

    # Reset selections and start the main menu
    filtered_df = None
    selections = {}

    clear_output()
    main_menu(data)


# Export important symbols
__all__ = ['run']
