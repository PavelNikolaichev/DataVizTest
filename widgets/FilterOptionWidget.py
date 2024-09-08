import ipywidgets as widgets


class FilterOptionWidget(widgets.HBox):
    def __init__(self, filter_data=None, parent=None, grouping_list=None):
        super().__init__()

        self.parent = parent
        self.filter_data = filter_data if filter_data else []
        self.grouping_list = grouping_list if grouping_list else []

        filter_info = widgets.Label(value=str(self.filter_data))

        delete_button = widgets.Button(icon="times", button_style="danger")
        delete_button.on_click(self.on_delete_button_clicked)

        self.children = (
            widgets.Box(
                [delete_button, filter_info],
                layout=widgets.Layout(
                    border="2px solid #888", padding="10px", border_radius="10px"
                ),
            ),
        )

        self.parent.children = self.parent.children + (self,)

    def on_delete_button_clicked(self, button):
        self.close()

    def close(self):
        self.remove_grouping()
        self.update_ui()

    def remove_grouping(self):
        try:
            grouping_variable, grouping_values = self.filter_data
            self.grouping_list.remove((grouping_variable, grouping_values))
        except ValueError:
            print(f"Error: Grouping {self.filter_data} not found in grouping list.")

    def update_ui(self):
        self.parent.children = [
            child for child in self.parent.children if child is not self
        ]
