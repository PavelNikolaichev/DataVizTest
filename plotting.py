from typing import *
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display
from .filter_data import and_filter_subset, filter_subset

from .settings import *


def x_y_scatter(
    x: str, y: str, df: pd.DataFrame | None = None, groups: list | None = None
) -> go.Figure:
    """
    Generate a scatter plot with the x-axis and y-axis as numeric variables.

    Parameters:
    x (str): Column name for the x-axis (numeric variable).
    y (str): Column name for the y-axis (numeric variable).
    df (pd.DataFrame): DataFrame containing the data.

    Returns:
    px.scatter: Plotly scatter plot figure.
    """
    if df is None:
        raise ValueError("The input DataFrame is empty.")

    if groups is None:
        groups = []

    if not pd.api.types.is_numeric_dtype(df[x]):
        raise ValueError(f"The x-axis column '{x}' must be numeric.")
    if not pd.api.types.is_numeric_dtype(df[y]):
        raise ValueError(f"The y-axis column '{y}' must be numeric.")

    # TODO: add grouping

    fig = px.scatter(df, x=x, y=y, title=f"Scatter plot of ({y}) by ({x})")
    fig.update_traces(hoverinfo="skip", hovertemplate=None)

    return fig


# fig3 = x_y_scatter(x = "EDSCOR50",y ="INCWAGE",df = data)
# fig3.show()


def x_stacked(x: str, df: pd.DataFrame | None = None) -> go.Figure:
    if df is None:
        raise ValueError("The input DataFrame is None.")
    proportions = df[x].value_counts(normalize=True).reset_index()
    proportions.columns = [x, "Proportion"]
    proportions["Proportion"] *= 100

    fig = go.Figure(
        data=[
            go.Bar(
                x=proportions[x],
                y=proportions["Proportion"],
                text=proportions["Proportion"],
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title=f"Stacked Bar Plot of ({x}) Proportions",
        xaxis_title=x,
        yaxis_title="Proportion (%)",
        barmode="stack",
    )

    return fig


def plot_generic_data(
    plot_func,
    x: str,
    y: str,
    df: pd.DataFrame,
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str = "sum",
) -> go.Figure:
    if groups is None:
        groups = []

    def get_grouped_data(subset: pd.DataFrame) -> pd.Series:
        if grouping_type == "count":
            return subset.groupby(x)[x].count()
        elif y not in numerical_attributes:
            if grouping_type in ("sum", "cluster sum"):
                return subset.groupby(x)[y].size()
            elif grouping_type in ("avg", "cluster avg"):
                grouped_data = subset.groupby(x)[y].agg(["count", "nunique"])
                return grouped_data["count"] / grouped_data["nunique"]
        elif grouping_type in ("sum", "cluster sum"):
            return subset.groupby(x)[y].sum()
        elif grouping_type in ("avg", "cluster avg"):
            return subset.groupby(x)[y].mean()

        return pd.Series()

    fig = go.Figure()
    fig.update_layout(
        xaxis_title=x, yaxis_title=y, title=f"{grouping_type} of {y} by {x}"
    )

    if not groups:
        grouped_data = get_grouped_data(df)
        plot_func(grouped_data, fig)
    else:
        if grouping_type in ["sum", "avg"]:
            subset = and_filter_subset(df, groups)
            grouped_data = get_grouped_data(subset)
            plot_func(grouped_data, fig, group_name=f"{grouping_type} of {y} by {x}")
        else:
            for column, values in groups:
                subset = filter_subset(df, {column: values})
                grouped_data = get_grouped_data(subset)
                plot_func(grouped_data, fig, group_name=f"{column}={values}")

    return fig


def plot_line_data(
    x: str,
    y: str,
    df: pd.DataFrame,
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str = "sum",
) -> go.Figure:
    def line_plot(data, fig, group_name=None):
        fig.add_trace(
            go.Scatter(x=data.index, y=data.values, mode="lines", name=group_name)
        )

    return plot_generic_data(line_plot, x, y, df, groups, grouping_type)


def plot_area_data(
    x: str,
    y: str,
    df: pd.DataFrame,
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str = "sum",
) -> go.Figure:
    def area_plot(data, fig, group_name=None):
        fig.add_trace(
            go.Scatter(x=data.index, y=data.values, fill="tozeroy", name=group_name)
        )

    return plot_generic_data(area_plot, x, y, df, groups, grouping_type)


def plot_clustered_bar_data(
    x: str,
    y: str,
    df: pd.DataFrame,
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str = "sum",
) -> go.Figure:
    labels = dict(index=x, value=f"{grouping_type} of {y} by {x}", barmode="group")

    def get_grouped_data(subset):
        if grouping_type == "count":
            return subset.groupby(x)[x].count()
        else:
            if y not in numerical_attributes:
                if grouping_type in ("sum", "cluster sum"):
                    return subset.groupby(x)[y].size()
                elif grouping_type in ("avg", "cluster avg"):
                    grouped_data = subset.groupby(x)[y].agg(["count", "nunique"])
                    return grouped_data["count"] / grouped_data["nunique"]
            if grouping_type in ("sum", "cluster sum"):
                return subset.groupby(x)[y].sum()
            elif grouping_type in ("avg", "cluster avg"):
                return subset.groupby(x)[y].mean()

    fig = px.bar()
    fig.update_layout(
        xaxis_title=x, yaxis_title=y, title=labels["value"], barmode="group"
    )

    if len(groups) == 0:
        grouped_data = get_grouped_data(df)
        print(grouped_data)
        fig = px.bar(grouped_data, title=labels["value"], labels=labels)
    else:
        if grouping_type in ["sum", "avg"]:
            subset = and_filter_subset(df, groups)
            grouped_data = get_grouped_data(subset)
            print(grouped_data)
            fig = px.bar(grouped_data, title=labels["value"], labels=labels)
        else:
            for column, values in groups:
                subset = filter_subset(df, [(column, values)])
                grouped_data = get_grouped_data(subset)

                fig.add_bar(
                    x=grouped_data.index,
                    y=grouped_data.values,
                    name=f"{column}={values}",
                )

    return fig


def plot_clustered_percentage_bar_data(
    x: str,
    y: str,
    df: pd.DataFrame,
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str = "sum",
) -> go.Figure:
    labels = dict(index=x, value=f"Percentage of {y} by {x}", barmode="group")

    if groups is None:
        groups = []

    def get_grouped_data(subset):
        if grouping_type == "count":
            return (
                subset.groupby(x)[x].value_counts(normalize=True).unstack(fill_value=0)
                * 100
            )
        else:
            return (
                subset.groupby(x)[y].value_counts(normalize=True).unstack(fill_value=0)
                * 100
            )

    fig = px.bar()
    fig.update_layout(
        xaxis_title=x,
        yaxis_title=f"Percentage of {y}",
        title=labels["value"],
        barmode="relative" if grouping_type in ["sum", "avg"] else "overlay",
    )

    if len(groups) == 0:
        grouped_data = get_grouped_data(df)
        fig = px.bar(grouped_data, title=labels["value"], labels=labels)
    else:
        if grouping_type in ["sum", "avg"]:
            subset = and_filter_subset(df, groups)
            grouped_data = get_grouped_data(subset)

            fig = px.bar(grouped_data, title=labels["value"], labels=labels)
        else:
            for column, values in groups:
                subset = filter_subset(df, [(column, values)])
                grouped_data = get_grouped_data(subset)

                fig.add_bar(
                    x=grouped_data.index,
                    y=grouped_data.values.flatten(),
                    name=f"{column}={values}",
                )

    return fig


def x_y_boxplot(
    x: str, y: str, df: pd.DataFrame, groups=None, grouping_type="sum"
) -> go.Figure:
    """
    Generate a boxplot with the x-axis as a categorical variable and y-axis as a numeric variable.

    Parameters:
    x (str): Column name for the x-axis (categorical variable).
    y (str): Column name for the y-axis (numeric variable).
    df (pd.DataFrame): DataFrame containing the data.
    groups (list): List of additional groupings (optional).
    grouping_type (str): Type of grouping to apply (default is "sum").

    Returns:
    fig: Plotly Figure object.
    """
    if groups is None:
        groups = []

    if not pd.api.types.is_numeric_dtype(df[y]):
        raise ValueError(f"The y-axis column '{y}' must be numeric.")

    fig = px.box(df, x=x, y=y, title=f"Boxplot of ({y}) by ({x})")
    return fig


def x_boxplot(
    x: str, df: pd.DataFrame, groups: list | None = None, grouping_type="sum"
) -> go.Figure:
    """
    Generate a boxplot with the x-axis as a categorical variable.

    Parameters:
    x (str): Column name for the y-axis (categorical variable).
    df (pd.DataFrame): DataFrame containing the data.
    groups (list): List of tuples for additional groupings (optional).
    grouping_type (str): Type of grouping to apply (default is "sum").

    Returns:
    go.Figure: Plotly Figure object.
    """
    if groups is None:
        groups = []

    print(f"grouping type: {grouping_type}")
    if len(groups) > 0:
        fig = go.Figure()

        for column, values in groups:
            subset = filter_subset(df, [(column, values)])
            fig.add_trace(
                go.Box(y=subset[x], name=f"Boxplot of ({x}) for {column}={values}")
            )
            fig.update_xaxes(showticklabels=False)
            fig.update_layout(yaxis_title=x, title=f"Boxplot of {x} by groups")
    else:
        fig = px.box(df, y=x, title=f"Boxplot of ({x})")

    return fig


def x_y_stacked(x: str, y: str, df: pd.DataFrame | None) -> go.Figure:
    """
    Generate a stacked bar plot with the x-axis as a categorical variable
    and y-axis as a categorical variable showing proportions.

    :param x: Column name for the x-axis (categorical variable).
    :param y: Column name for the y-axis (categorical variable).
    :param df: DataFrame containing the data.

    :return: px.Bar instance
    """
    if df is None:
        raise ValueError("The input DataFrame is empty.")

    if not isinstance(df[x], pd.CategoricalDtype):
        raise ValueError(f"The x-axis column '{x}' must be categorical.")
    if not isinstance(df[y], pd.CategoricalDtype):
        raise ValueError(f"The y-axis column '{y}' must be categorical.")

    counts = df.groupby([x, y]).size().unstack(fill_value=0)

    # Normalize the counts to get proportions
    proportions = counts.div(counts.sum(axis=1), axis=0) * 100
    # Reshape the DataFrame for Plotly
    proportions.reset_index(inplace=True)
    proportions_melted = pd.melt(
        proportions, id_vars=[x], var_name=y, value_name="Percentage"
    )

    # Plot using Plotly Express
    fig = px.bar(
        proportions_melted,
        x=x,
        y="Percentage",
        color=y,  # Color represents the stacked bars
        barmode="stack",
        labels={"Percentage": "Proportion (%)"},
        title=f"Stacked Bar Plot of ({y}) Proportions for different ({x})",
        hover_name=y,
        hover_data={"Percentage": ":.2f%"},
    )

    return fig


def render_graph(
    data: pd.DataFrame,
    kind: str,
    x_axis: str = "YEAR",
    y_axis: str = "Count",
    groups: List[Tuple[str, list]] | None = None,
    grouping_type: str | None = None,
    year_range: Tuple[int, int] | None = None,
    top_k: int = 0,
    filter_list: Dict[str, Union[list, tuple, str]] | None = None,
) -> go.Figure:
    if filter_list is None:
        filter_list = {}
    if groups is None:
        groups = []
    subset = data
    if filter_list:
        subset = filter_subset(subset, filter_list)
    if year_range:
        subset = subset[
            subset["YEAR"].between(year_range[0], year_range[1], inclusive="both")
        ]

    plot_func_map = {
        "line": plot_line_data,
        "area": plot_area_data,
        "scatter": lambda x, y, df, groups, *args: x_y_scatter(
            x=x, y=y, df=df, groups=groups
        ),
        "box": lambda x, y, df, groups, *args: x_boxplot(x=x, df=subset, groups=groups),
        "grouped bar": plot_clustered_bar_data,
        "stacked bar": plot_clustered_percentage_bar_data,
    }

    fig = plot_func_map.get(kind, lambda *args: None)(
        x_axis, y_axis, subset, groups, grouping_type
    )

    if fig:
        fig.update_layout(legend=dict(orientation="h"))

    return fig


def x_y_boxplot(x: str, y: str, df=None, groups=None, grouping_type="sum") -> go.Figure:
    """
    Generate a boxplot with the x-axis as a categorical variable and y-axis as a numeric variable.

    Parameters:
    x (str): Column name for the x-axis (categorical variable).
    y (str): Column name for the y-axis (numeric variable).
    df (pd.DataFrame): DataFrame containing the data.
    groups (list): List of additional groupings (optional).
    grouping_type (str): Type of grouping to apply (default is "sum").

    Returns:
    fig: Plotly Figure object.
    """
    if groups is None:
        groups = []

    if not pd.api.types.is_numeric_dtype(df[y]):
        raise ValueError(f"The y-axis column '{y}' must be numeric.")

    fig = px.box(df, x=x, y=y, title=f"Boxplot of ({y}) by ({x})")
    return fig


def x_boxplot(
    x: str, df: pd.DataFrame, groups: list = None, grouping_type="sum"
) -> go.Figure:
    """
    Generate a boxplot with the x-axis as a categorical variable.

    Parameters:
    x (str): Column name for the y-axis (categorical variable).
    df (pd.DataFrame): DataFrame containing the data.
    groups (list): List of tuples for additional groupings (optional).
    grouping_type (str): Type of grouping to apply (default is "sum").

    Returns:
    go.Figure: Plotly Figure object.
    """
    if groups is None:
        groups = []

    print(f"grouping type: {grouping_type}")
    if len(groups) > 0:
        fig = go.Figure()

        for column, values in groups:
            subset = filter_subset(df, [(column, values)])
            fig.add_trace(
                go.Box(y=subset[x], name=f"Boxplot of ({x}) for {column}={values}")
            )
            fig.update_xaxes(showticklabels=False)
            fig.update_layout(yaxis_title=x, title=f"Boxplot of {x} by groups")
    else:
        fig = px.box(df, y=x, title=f"Boxplot of ({x})")

    return fig


def x_y_stacked(x: str, y: str, df: pd.DataFrame) -> go.Figure:
    """
    Generate a stacked bar plot with the x-axis as a categorical variable
    and y-axis as a categorical variable showing proportions.

    :param x: Column name for the x-axis (categorical variable).
    :param y: Column name for the y-axis (categorical variable).
    :param df: DataFrame containing the data.

    :return: px.Bar instance
    """
    if df is None:
        raise ValueError("The input DataFrame is empty.")

    if not isinstance(df[x], pd.CategoricalDtype):
        raise ValueError(f"The x-axis column '{x}' must be categorical.")
    if not isinstance(df[y], pd.CategoricalDtype):
        raise ValueError(f"The y-axis column '{y}' must be categorical.")

    counts = df.groupby([x, y]).size().unstack(fill_value=0)

    # Normalize the counts to get proportions
    proportions = counts.div(counts.sum(axis=1), axis=0) * 100
    # Reshape the DataFrame for Plotly
    proportions.reset_index(inplace=True)
    proportions_melted = pd.melt(
        proportions, id_vars=[x], var_name=y, value_name="Percentage"
    )

    # Plot using Plotly Express
    fig = px.bar(
        proportions_melted,
        x=x,
        y="Percentage",
        color=y,  # Color represents the stacked bars
        barmode="stack",
        labels={"Percentage": "Proportion (%)"},
        title=f"Stacked Bar Plot of ({y}) Proportions for different ({x})",
        hover_name=y,
        hover_data={"Percentage": ":.2f%"},
    )

    return fig


def plotting(data, filter_list):
    """Main plotting interface function."""
    from .settings import options_list, option_value_dictionary, numerical_attributes
    from .widgets import FilterOptionWidget
    
    global grouping_list

    output_widget = widgets.Output()
    style = {"description_width": "initial"}
    grouping_list = []
    group_filter_container = widgets.VBox()

    plot_type = widgets.Dropdown(
        options=["line", "box", "area", "scatter", "stacked bar", "grouped bar", "map"],
        value="line",
        description="Plot type:",
    )

    x_axis = widgets.Dropdown(options=options_list, description="X-Axis:", style=style)
    y_axis = widgets.Dropdown(options=options_list, description="Y-Axis:", style=style)

    map_style = widgets.Dropdown(
        options=[
            "OpenStreetMap",
            "CartoDB Positron",
            "CartoDB Dark Matter",
            "Stamen Terrain",
            "Stamen Toner",
        ],
        value="OpenStreetMap",
        description="Map style:",
        style=style,
        layout=widgets.Layout(visibility="hidden"),
    )

    cluster_markers = widgets.Checkbox(
        value=True,
        description="Cluster markers",
        style=style,
        layout=widgets.Layout(visibility="hidden"),
    )

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

    def update_output(result):
        with output_widget:
            output_widget.clear_output(wait=True)
            # Handle different result types
            if hasattr(result, "show"):  # Plotly figure
                result.show()
            elif hasattr(result, "_repr_html_"):  # Folium map
                display(result)
            else:
                print("Unable to display result")

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

        if t_plot_type == "map":
            # For maps, X-axis should be address/location columns (usually text/categorical)
            x_axis.description = "Address column:"
            y_axis.description = "Value column (optional):"
            # Show map-specific controls
            map_style.layout.visibility = "visible"
            cluster_markers.layout.visibility = "visible"
        else:
            x_axis.description = "X-Axis:"
            y_axis.description = "Y-Axis:"
            # Hide map-specific controls
            map_style.layout.visibility = "hidden"
            cluster_markers.layout.visibility = "hidden"

        y_axis.layout.visibility = (
            "hidden" if t_plot_type in ("box", "map") else "visible"
        )
        grouping_layout.layout.visibility = (
            "visible"
            if t_plot_type
            in ("box", "area", "line", "grouped bar", "stacked bar", "map")
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

    def make_plot_handler(x):
        result = render_graph(
            data,
            plot_type.value,
            x_axis.value,
            y_axis.value,
            grouping_list,
            grouping_type.value,
            filter_list=filter_list,
            map_style=map_style.value,  # Pass map style
            cluster_markers=cluster_markers.value,  # Pass clustering option
        )
        update_output(result)

    make_plot_button.on_click(make_plot_handler)

    done_button = widgets.Button(description="Done", button_style="warning")
    from .ui import main_menu
    done_button.on_click(lambda x: main_menu(data))

    selection_layout = widgets.HBox([widgets.Text("Selection")])
    plotting_layout = widgets.VBox(
        [
            widgets.HBox([plot_type, make_plot_button]),
            widgets.HBox([x_axis]),
            widgets.HBox([y_axis, done_button]),
            widgets.HBox([map_style, cluster_markers]),
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


# Initialize grouping_list as a module-level variable
grouping_list = []
