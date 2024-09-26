from typing import *
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ipywidgets as widgets
from functools import reduce

from .settings import *

from ipywidgets import interact, widgets, Layout
import pandas as pd

from IPython.display import display, clear_output

from .describe_data import count_table, summary_statistics
from .filter_data import filter_dataframe
from .plotting import render_graph
from .widgets import FilterOptionWidget


def create_ui(df, categorical_attributes):
    search_text = ""
    selected_category = categorical_attributes[0]

    def get_filtered_values(search_text, selected_category):
        if search_text:
            return [
                value
                for value in df[selected_category].unique()
                if search_text.lower() in str(value).lower()
            ]
        else:
            return df[selected_category].unique().tolist()

    value_selection = widgets.SelectMultiple(
        options=sorted(get_filtered_values(search_text, selected_category)),
        value=(),
        description="Values:",
        disabled=False,
        rows=min(5, len(get_filtered_values(search_text, selected_category))),
        layout=Layout(width="70%", height="300px"),
        style={"font-size": "40px"},
    )

    def update_value_selection():
        nonlocal search_text, selected_category
        filtered_values = get_filtered_values(search_text, selected_category)
        value_selection.options = sorted(filtered_values)
        value_selection.rows = min(5, len(filtered_values))
        value_selection.value = ()  # tuple(filtered_values)

    @interact(
        category=widgets.Dropdown(
            options=categorical_attributes,
            value=selected_category,
            description="Variable:",
        ),
        search=widgets.Text(value="", placeholder="Search..."),
    )
    def update(category, search):
        nonlocal search_text, selected_category
        search_text = search
        selected_category = category
        update_value_selection()

    @interact(
        values=value_selection
    )  # widgets.SelectMultiple(options=[], value=(), description='Values:', rows=5, layout=Layout(width='70%', height='300px')))
    # This should be the value selection
    def show_values(values):
        nonlocal selected_category
        # if len(values) != len(df[selected_category].unique()):
        print("Current Selection:", selected_category, values)
        # else:
        #   print("Selecting all(Default)")

    select_all_button = widgets.Button(description="Select All")
    deselect_all_button = widgets.Button(description="Deselect All")
    add_button = widgets.Button(description="Add Selection")
    done_button = widgets.Button(description="Done")

    def select_all(button):
        print("--" * 20)
        global selections
        global df
        selected_attribute = selected_category
        all_values = value_selection.options
        selections[selected_attribute] = list(all_values)
        print(f"All filtered values selected for {selected_attribute}")
        print(f"Current Selection:{selections}")

    def deselect_all(button):
        print("--" * 20)
        global selections
        selected_attribute = selected_category
        if selected_attribute in selections:
            selections.pop(selected_attribute)
            if not selections:
                selections = {}
        print(f"All values deselected for {selected_attribute}")
        print(f"Current Selection:{selections}")

    def add_selection(button):
        global selections
        print("--" * 20)
        selected_attribute = selected_category
        selected_values = list(value_selection.value)
        if not selected_values:
            print("Nothing selected")
            print(f"Current Selection:{selections}")
            return
        if selected_attribute in selections:
            old = selections[selected_attribute]
            changes = [value for value in selected_values if value not in old]
            if changes:
                selections[selected_attribute].extend(changes)
                print(f"Selection added: {selected_attribute} - {changes}")
            else:
                print("Nothing added")
        else:
            print(f"Selection added: {selected_attribute} - {selected_values}")
            selections[selected_attribute] = selected_values
        print(f"Current Selection:{selections}")

    def done(button):
        global selections
        print("Final Selections:")
        print(selections)
        make_selection_menu(df)

    # Set button click actions
    select_all_button.on_click(select_all)
    deselect_all_button.on_click(deselect_all)
    add_button.on_click(add_selection)
    done_button.on_click(done)

    # Display the widgets
    display(select_all_button)
    display(deselect_all_button)
    display(add_button)
    display(done_button)


def plotting(data, filter_list):
    global grouping_list

    output_widget = widgets.Output()
    style = {"description_width": "initial"}
    grouping_list = []
    group_filter_container = widgets.VBox()

    plot_type = widgets.Dropdown(
        options=["line", "box", "area", "scatter", "stacked bar", "grouped bar"],
        value="line",
        description="Plot type:",
    )

    x_axis = widgets.Dropdown(options=options_list, description="X-Axis:", style=style)
    y_axis = widgets.Dropdown(options=options_list, description="Y-Axis:", style=style)

    if plot_type.value in ("box", "stacked bar"):
        y_axis.layout.visibility = "hidden"

    grouping_variable = widgets.Dropdown(
        options=options_list, description="Group variable:", style=style
    )
    grouping_variable_options = option_value_dictionary

    grouping_variable_values = widgets.SelectMultiple(
        options=[],
        description="Values:",
        style=style,
    )
    grouping_variable_values.layout.height = "200px"
    grouping_variable_values.layout.width = "60%"

    grouping_type = widgets.Dropdown(
        options=["sum", "avg", "cluster sum", "cluster avg", "count"],
        description="Y-axis functions:",
        style=style,
    )

    def update_output(fig):
        with output_widget:
            output_widget.clear_output(wait=True)
            fig.show()

    def update_grouping_options(change):
        selected_option = change.new
        if selected_option in grouping_variable_options:
            second_options = grouping_variable_options[selected_option]
            grouping_variable_values.options = second_options

    grouping_variable.observe(update_grouping_options, names=["value"])

    def grouping_interaction(button):
        grouping_list.append((grouping_variable.value, grouping_variable_values.value))
        filter_widget = FilterOptionWidget(
            filter_data=(grouping_variable.value, grouping_variable_values.value),
            parent=group_filter_container,
            grouping_list=grouping_list,
        )

    group_button = widgets.Button(
        description="Group", button_style="success", style=style
    )
    group_button.on_click(grouping_interaction)

    def update_plot_type(change):
        t_plot_type = change.new

        if t_plot_type == "box":
            x_axis.options = numerical_attributes
        elif change.old == "box":
            x_axis.options = options_list

        if t_plot_type == "scatter":
            y_axis.options = numerical_attributes
        elif change.old == "scatter":
            y_axis.options = options_list

        y_axis.layout.visibility = "hidden" if t_plot_type == "box" else "visible"
        grouping_layout.layout.visibility = (
            "visible"
            if t_plot_type in ("box", "area", "line", "grouped bar", "stacked bar")
            else "hidden"
        )

        if grouping_layout.layout.visibility == "hidden":
            grouping_variable_values.value = []
            for widget in group_filter_container.children:
                widget.close()

        grouping_type.layout.visibility = (
            "hidden" if t_plot_type == "box" else "visible"
        )

    plot_type.observe(update_plot_type, names=["value"])

    make_plot_button = widgets.Button(
        description="Make plot", button_style="info", style=style
    )
    make_plot_button.on_click(
        lambda x: update_output(
            render_graph(
                data,
                plot_type.value,
                x_axis.value,
                y_axis.value,
                grouping_list,
                grouping_type.value,
                filter_list=filter_list,
            )
        )
    )

    done_button = widgets.Button(description="Done", button_style="warning")
    done_button.on_click(lambda x: main_menu(data))

    selection_layout = widgets.HBox([widgets.Text("Selection")])
    plotting_layout = widgets.VBox(
        [
            widgets.HBox([plot_type, make_plot_button]),
            widgets.HBox([x_axis]),
            widgets.HBox([y_axis, done_button]),
        ]
    )
    grouping_layout = widgets.VBox(
        [
            widgets.HBox([grouping_variable, group_button]),
            widgets.HBox([grouping_variable_values, grouping_type]),
            group_filter_container,
        ]
    )

    Layout = widgets.VBox(
        [
            selection_layout,
            plotting_layout,
            grouping_layout,
            widgets.HBox([output_widget]),
        ]
    )
    display(Layout)


def main_menu(df: pd.DataFrame):
    global csm
    global selections

    csm.set_state("State Choosing")
    print("--" * 20)
    print("This is the main menu, you have the following three things you can do.")
    print("This is the selection you have made:")
    for attribute, value in selections.items():
        print(f"{attribute}: {value}")

    def selection_mode(button):
        global selections
        try:
            chosen = dropdown.value
            if chosen == "1":
                make_selection_menu(df)
            elif chosen == "2":
                desdcribe_selection_menu(df)
            elif chosen == "3":
                plotting(df, selections)
                # somewhere you input the ploting, you can use filtered_df as "df"
            elif chosen == "4":
                selections = {}
                main_menu(df)
        except:
            main_menu(df)

    # Dropdown options
    state_options = {
        "Make Selection": "1",
        "Describe Selection": "2",
        "Plot Selection": "3",
        "Clear selections": "4",
    }

    # Create dropdown widgets
    dropdown = widgets.Dropdown(options=state_options, description="Select mode:")

    # Create buttons
    finish_button = widgets.Button(description="Choose")

    # Set button click actions
    finish_button.on_click(selection_mode)

    # Display the dropdown and buttons
    display(dropdown, finish_button)


def make_selection_menu(df: pd.DataFrame):
    global csm
    csm.set_state("Make Selection")
    print("--" * 20)
    print("You can modify the subset you want to check in this section.")
    print("Current Selections:")
    for attribute, value in selections.items():
        print(f"{attribute}: {value}")

    def selection_mode(button):
        try:
            chosen = dropdown.value
            if chosen == "1":
                numeric_selections(df)
            elif chosen == "2":
                # categorical_selections(df)
                # categorical_selections_with_search(df)
                create_ui(df, categorical_attributes)
            elif chosen == "3":
                delete_selections(df)
            elif chosen == "4":
                main_menu(df)
        except:
            make_selection_menu(df)

    # Dropdown options
    state_options = {
        "Numeric Variables": "1",
        "Categorical Variables": "2",
        "Delete Selections": "3",
        "Main Menu": "4",
    }

    # Create dropdown widget
    dropdown = widgets.Dropdown(options=state_options, description="Select mode:")

    # Create buttons
    finish_button = widgets.Button(description="Choose")

    # Set button click actions
    finish_button.on_click(selection_mode)

    # Display the dropdown and buttons
    display(dropdown, finish_button)


def desdcribe_selection_menu(df: pd.DataFrame):
    global csm
    csm.set_state("Describe Selection")
    print("--" * 20)
    print(
        "Filtering the dateframe using the following selection, and you can check the filtered dataframe."
    )
    print("Selections:")

    for attribute, value in selections.items():
        print(f"{attribute}: {value}")
    global filtered_df
    filtered_df = filter_dataframe(df, selections)

    def selection_mode(button):
        global filtered_df
        global selections

        if filtered_df is None:
            filtered_df = filter_dataframe(df, selections)
        # try:
        chosen = dropdown.value
        if chosen == "1":
            display(filtered_df.head(10))
            desdcribe_selection_menu(df)
        elif chosen == "2":
            summary_statistics(filtered_df)
            desdcribe_selection_menu(df)
        elif chosen == "3":
            count_table(filtered_df, selections)
            desdcribe_selection_menu(df)
        elif chosen == "4":
            main_menu(df)
        elif chosen == "5":
            filtered_df = None
            selections = {}
            main_menu(df)
        # except:
        #  print("Something wrong, try again.")
        #  desdcribe_selection_menu(df)

    # Dropdown options
    state_options = {
        "First 10 Lines": "1",
        "Summary statistics": "2",
        "Frequency Table": "3",
        "Keep Dataframe": "4",
        "Discard Dataframe": "5",
    }

    # Create dropdown widget
    dropdown = widgets.Dropdown(options=state_options, description="Select mode:")

    # Create buttons
    finish_button = widgets.Button(description="Choose")

    # Set button click actions
    finish_button.on_click(selection_mode)

    # Display the dropdown and buttons
    display(dropdown, finish_button)
