from functools import reduce
from typing import Dict, Union
import pandas as pd


def filter_dataframe(dataframe: pd.DataFrame, selection: dict) -> pd.DataFrame:
    filtered_df = dataframe.copy()  # Start with a copy of the original DataFrame

    for attribute, values in selection.items():
        if attribute is categorical_attributes and all(
            isinstance(v, list) for v in values
        ):
            filter_condition = pd.Series(False, index=filtered_df.index)
            for range in values:
                start, end = range

                filter_condition |= (filtered_df[attribute] >= start) & (
                    filtered_df[attribute] <= end
                )
            filtered_df = filtered_df[filter_condition]
        else:
            filtered_df = filtered_df[filtered_df[attribute].isin(values)]

    return filtered_df


def and_filter_subset(
    subset: pd.DataFrame, filter_list: Dict[str, Union[tuple, list, str]] | tuple | list
) -> pd.DataFrame:
    print(f"And filter subset list: {filter_list}")

    if not filter_list:
        return subset
    filter_conditions = [
        (
            subset[column].isin(value)
            if isinstance(value, (list, tuple))
            else subset[column] == value
        )
        for column, value in (
            filter_list.items() if isinstance(filter_list, dict) else filter_list
        )
    ]
    combined_condition = reduce(lambda x, y: x | y, filter_conditions)
    return subset[combined_condition]


def filter_subset(
    subset: pd.DataFrame | None,
    filter_list: Dict[str, Union[tuple, list, str]] | tuple | list,
) -> pd.DataFrame:
    print(f"Filter subset list: {filter_list}")

    if subset is None:
        raise ValueError("The input DataFrame is None.")
    for column, value in (
        filter_list.items() if isinstance(filter_list, dict) else filter_list
    ):
        subset = subset[
            (
                subset[column].isin(value)
                if isinstance(value, (list, tuple))
                else subset[column] == value
            )
        ]
    return subset
