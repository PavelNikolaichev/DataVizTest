import itertools
import pandas as pd
from IPython.display import display, clear_output
import ipywidgets as widgets

from .export_data import download_excel
from __init__ import *


def count_table(filtered_df: pd.DataFrame, selections: dict):
    columns = selections.keys()
    count_tables = []

    def create_count_table(pair):
        count_table = filtered_df.groupby(list(pair)).size().unstack(fill_value=0)
        count_table["Total"] = count_table.sum(axis=1)
        count_table.loc["Total"] = count_table.sum(axis=0)
        count_table.at["Total", "Total"] = count_table.values.sum()

        count_table = count_table.astype(int)

        for attribute, values in selections.items():
            if not values or attribute not in pair:
                continue

            for value_range in values:
                if type(value_range) in (tuple, list):
                    start, end = value_range
                    for value in range(start, end + 1):
                        if value not in count_table.index:
                            count_table.loc[value] = "NaN"
                        if value not in count_table.columns:
                            count_table[value] = "NaN"
                else:
                    value = value_range
                    if value not in count_table.index:
                        count_table.loc[value] = "NaN"
                    if value not in count_table.columns:
                        count_table[value] = "NaN"

        return count_table

    if len(columns) > 1:
        # Display subsets of DataFrame for each combination of columns
        for pair in itertools.combinations(columns, 2):
            count_table = create_count_table(pair)
            display(count_table)
            count_tables.append(count_table)

        download_button = widgets.Button(description="Download")
        # download_button.on_click(lambda x: save_and_download_dataframes(count_tables))
        download_button.on_click(lambda x: download_excel(count_table))
        display(download_button)
    elif len(columns) == 1:
        for column, values in selections.items():
            value_counts_table = filtered_df[column].value_counts().reset_index()
            value_counts_table.columns = [column, "Count"]

            for value in values:
                if value not in value_counts_table[column].values:
                    value_counts_table = value_counts_table.append(
                        {column: value, "Count": "NaN"}, ignore_index=True
                    )

            download_button = widgets.Button(description="Download Table")
            download_button.on_click(lambda x: download_excel(value_counts_table))

            display(value_counts_table, download_button)
    else:
        print("Nothing selected")


def head_exception(df: pd.DataFrame):
    try:
        first_k_lines = int(input("How many lines do you want to check? "))
        display(df.head(int(first_k_lines)))
    except ValueError:
        print("Invalid number")
    except Exception as e:
        print("An error occurred:", e)
    finally:
        print("--" * 20)


def summary_statistics(df: pd.DataFrame):
    print("Numeric Attribtues are:")
    print(numerical_attributes)

    print("--" * 20)
    print("Summary statistics:")

    pd.options.display.float_format = "{:,.0f}".format

    summary_df = df[numerical_attributes].describe().transpose()

    display(summary_df)
