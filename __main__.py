import numpy as np
import pandas as pd

import ui

from . import data_processing
from . import plotting
from . import selection

if __name__ == "__main__":
    # That's just example how it can be used.
    data = pd.DataFrame()

    numerical_attributes = (
        data.select_dtypes(include=[np.number]).columns.sort_values().tolist()
    )
    categorical_attributes = (
        data.select_dtypes(exclude=[np.number]).columns.sort_values().tolist()
    )

    options_list = data.columns.sort_values().tolist()
    option_value_dictionary = {}
    for attribute in data.columns:
        options_list.append(attribute)
        option_values = data[attribute].unique()

        try:
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
        except Exception as error:
            option_value_dictionary[attribute] = tuple(option_values)

    ui.create_ui(options_list, option_value_dictionary)
