import os
import pandas as pd
from google.colab import files
from __init__ import *


def download_excel(table: pd.DataFrame):
    """
    Download the table as an Excel file

    Parameters
    table (pd.DataFrame): The table to be downloaded
    """
    table.to_excel("Frequency Table.xlsx", index=True)
    files.download("Frequency Table.xlsx")


def save_and_download_dataframes(dataframes: list[pd.DataFrame], folder_name="output"):
    """
    Save and download the dataframes as Excel files

    Parameters
    dataframes (list[pd.DataFrame]): The dataframes to be saved
    folder_name (str): The name of the folder where the Excel files will be saved
    """
    # Create the folder if it doesn't exist
    os.makedirs(folder_name, exist_ok=True)

    for i, df in enumerate(dataframes):
        file_path = os.path.join(folder_name, f"data_{i + 1}.xlsx")
        df.to_excel(file_path, index=True)
        print(f"Table {i + 1} saved to: {file_path}")

    # Create a zip file containing all Excel files
    zip_path = f"{folder_name}.zip"
    os.system(f"zip -r {zip_path} {folder_name}")

    # Download the zip file
    files.download(zip_path)
