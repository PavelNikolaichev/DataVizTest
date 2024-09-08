from .ClientStateMachine import ClientStateMachine
from .ui import main_menu
from .data_processing import *
from .plotting import *
from .selection import *


def run(data: pd.DataFrame):
    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "You must initialize global variable `data`. It must be a pandas DataFrame instance"
        )

    global filtered_df, selections, numerical_attributes, categorical_attributes, csm
    data = None
    filtered_df = None
    selections = {}

    numerical_attributes = []
    categorical_attributes = []

    csm = ClientStateMachine()
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
        except Exception as _:
            option_value_dictionary[attribute] = tuple(option_values)

    filtered_df = None
    selections = {}

    main_menu(data, csm)
