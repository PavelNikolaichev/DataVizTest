import itertools
import os
import sys
from functools import reduce
from warnings import simplefilter

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from IPython.display import display, clear_output
from ipywidgets import (
    interact,
    widgets,
    Layout,
    VBox,
    HBox,
)

from google.colab import output, drive, files
from ui import make_selection_menu

drive.mount("/content/drive")

plt.rcParams["figure.dpi"] = 120

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


selections = {}


def numeric_selections(df: pd.DataFrame):
    # Sample DataFrame
    # df = trial
    # selections = {}

    temp_range_holder = None

    def create_attribute_dropdown():
        return widgets.Dropdown(
            options=numerical_attributes,
            value=numerical_attributes[0],
            description="Variable:",
        )

    def create_value_slider(attribute):
        min_value, max_value = df[attribute].min(), df[attribute].max()
        step_size = max(1, (max_value - min_value) // 20)

        return widgets.IntRangeSlider(
            value=[min_value, max_value],
            min=min_value,
            max=max_value,
            step=step_size,
            description="Range:",
        )

    def display_current_value(value):
        global temp_range_holder
        temp_range_holder = value

    def display_slider_value(attribute):
        value_slider = create_value_slider(attribute)
        widgets.interact(
            display_current_value,
            attribute=widgets.fixed(attribute),
            value=value_slider,
        )

    def update_and_display(attribute):
        display_slider_value(attribute)

    attribute_dropdown = create_attribute_dropdown()
    range_show = widgets.interactive(update_and_display, attribute=attribute_dropdown)
    display(range_show)

    def add_selection(button):
        global selections, temp_range_holder
        print("--" * 20)
        selected_attribute, selected_values = (
            attribute_dropdown.value,
            temp_range_holder,
        )
        # print(f"[DEBUG]: type of selected_values: {type(selected_values)}")

        if selected_attribute in selections:
            if isinstance(selected_values, list):
                print(
                    f"Selection added A RANGE(Closed Inteval): {selected_attribute} - {list(selected_values)}"
                )
                selections[selected_attribute].append(list(selected_values))
            else:
                start, end = selected_values
                values = selections[selected_attribute]

                values.extend(
                    [
                        item
                        for item in df[selected_attribute].unique()
                        if start <= item <= end and item not in values
                    ]
                )
                selections[selected_attribute] = sorted(values)
                # values = list(tuple(values))
                print(f"Selection updated: {selected_attribute} - {values}")
        else:
            if isinstance(selected_values, list):
                print(
                    f"Selection added A RANGE(Closed Inteval): {selected_attribute} - {list(selected_values)}"
                )
                selections[selected_attribute] = [list(selected_values)]
            else:
                start, end = selected_values

                selections[selected_attribute] = sorted(
                    [
                        item
                        for item in df[selected_attribute].unique()
                        if start <= item <= end
                    ]
                )

                print(
                    f"Selection added: {selected_attribute} - {selections[selected_attribute]}"
                )

        print(f"Current Selection:{selections}")

    def clear(button):
        print("--" * 20)
        global selections

        selected_attribute = attribute_dropdown.value
        selections.pop(selected_attribute, None)

        print(f"All values cleared for {selected_attribute}")
        print(f"Current Selection:{selections}")

    def finish(button):
        global selections

        print("--" * 20)

        print("Final Selections:", selections)
        make_selection_menu(df)

    add_button = widgets.Button(description="Add Selection")
    clear_button = widgets.Button(description="Clear Variable")
    finish_button = widgets.Button(description="Done")

    add_button.on_click(add_selection)
    clear_button.on_click(clear)
    finish_button.on_click(finish)

    display(add_button, clear_button, finish_button)


def categorical_selections(df: pd.DataFrame, categorical_attributes=None):
    global selections

    if categorical_attributes is None:
        categorical_attributes = df.select_dtypes(exclude=[np.number]).columns.tolist()

    temp_multiselection_holder = None

    def create_attribute_dropdown():
        return widgets.Dropdown(
            options=categorical_attributes,
            value=categorical_attributes[0],
            description="Variable:",
            disabled=False,
        )

    def create_value_selection(attribute):
        unique_values = sorted(df[attribute].unique())

        return widgets.SelectMultiple(
            options=unique_values,
            value=(),
            description=f"{attribute} Values:",
            disabled=False,
            rows=min(5, len(unique_values)),
            layout=Layout(width="70%", height="400px"),
            style={"font-size": "40px"},
        )

    def display_current_value(attribute, values):
        print(f"Current {attribute} values: {list(values)}")

        global temp_multiselection_holder
        temp_multiselection_holder = values

    def update_and_display(attribute):
        value_selection = create_value_selection(attribute)
        widgets.interact(
            display_current_value,
            attribute=widgets.fixed(attribute),
            values=value_selection,
        )

    attribute_dropdown = create_attribute_dropdown()
    range_show = widgets.interactive(update_and_display, attribute=attribute_dropdown)

    display(range_show)

    def select_all(button):
        print("--" * 20)

        selected_attribute = attribute_dropdown.value
        selections[selected_attribute] = list(
            create_value_selection(selected_attribute).options
        )

        print(f"All values selected for {selected_attribute}")
        print(f"Current Selection:{selections}")

    def deselect_all(button):
        print("--" * 20)
        selected_attribute = attribute_dropdown.value
        selections.pop(selected_attribute, None)
        # if selections is None:
        #     selections = {}

        print(f"All values deselected for {selected_attribute}")
        print(f"Current Selection:{selections}")

    def add_selection(button):
        global selections, temp_multiselection_holder
        print("--" * 20)
        selected_attribute, selected_values = attribute_dropdown.value, list(
            temp_multiselection_holder
        )

        if not selected_values:
            print("Nothing selected")
            print(f"Current Selection:{selections}")
            return

        if selected_attribute in selections:
            changes = [
                value
                for value in selected_values
                if value not in selections[selected_attribute]
            ]
            selections[selected_attribute].extend()

            print(f"Selection added: {selected_attribute} - {changes}")
        else:
            print(f"Selection added: {selected_attribute} - {selected_values}")
            selections[selected_attribute] = selected_values
        print(f"Current Selection:{selections}")

    def finish(button):
        # global selections
        print("--" * 20)
        print("Final Selections:", selections)
        make_selection_menu(df)

    # Create buttons
    select_all_button = widgets.Button(description="Select All")
    deselect_all_button = widgets.Button(description="Deselect All")
    add_button = widgets.Button(description="Add Selection")
    finish_button = widgets.Button(description="Done")

    select_all_button.on_click(select_all)
    deselect_all_button.on_click(deselect_all)
    add_button.on_click(add_selection)
    finish_button.on_click(finish)

    display(select_all_button, deselect_all_button, add_button, finish_button)


def delete_selections(df: pd.DataFrame):
    global selections
    delete_columns = []

    print(
        "Current Selection:",
        *(f"{attribute}: {value}" for attribute, value in selections.items()),
        sep="\n",
    )

    checkboxes = [
        widgets.Checkbox(description=str(key), value=False) for key in selections
    ]

    def handle_checkbox_change(change):
        global delete_columns

        selected_options = [
            checkbox.description for checkbox in checkboxes if checkbox.value
        ]

        print(f"Selected Options: {selected_options}")

        delete_columns = selected_options

    for checkbox in checkboxes:
        checkbox.observe(handle_checkbox_change, names="value")

    display(*checkboxes)

    def delete(button):
        global delete_columns
        if not delete_columns:
            print("Nothing chosen")
            return

        for attribute in delete_columns:
            print("Delete: ", attribute)
            print("Its values are: ", selections[attribute])
            selections.pop(attribute)

        print("--" * 20)
        print(f"After delete, The remaining :")
        for attribute, value in selections.items():
            print(f"{attribute}: {value}")

        make_selection_menu(df)

    def cancel(button):
        print("Cancelled deletion")

        make_selection_menu(df)

    delete_button = widgets.Button(description="Delete")
    delete_button.on_click(delete)
    cancel_button = widgets.Button(description="Cancel")
    cancel_button.on_click(cancel)

    display(delete_button, cancel_button)
