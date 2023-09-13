"""
A set of functions to help with data management, display, and analysis
"""
import inspect
import re
import altair as alt
import streamlit as st

import os
import file_management as fm
from glob import glob
import re
import time
import pandas as pd
import pyarrow as pa
import numpy as np


def date_or_string(df, column_name):
    """
    Given a dataframe and a column name, check if the column contains dates or strings.
    Returns 'date' if the column contains dates, 'string' otherwise.
    """
    # convert the column to datetime format
    df = df[[column_name]].copy()
    df[column_name] = pd.to_datetime(df[column_name], errors='coerce')

    # check if the column contains all null values
    if df[column_name].isnull().all():
        return 'string'
    else:
        return 'date'

def get_data_config(df):
    """Generate a config for the data table.
    that will be used by streamlit data editor.
    Data editor displays datetime, numbers and
    boolean correctly by default.  
    
    This function creates config for columns with dates
    that are 'object' type.  It also creates config for
    strings with low cardinality to be returned as select boxes.

    Args:
        df (dataframe): Any dataframe that needs to be displayed in the data editor

    Returns:
        dict: dictionary of columns that need to be displayed as select boxes
    """

    # Loop through the columns to identify the datatypes
    # and add config
    config = {}
    for col in df.columns:
        # Check if the column is an object
        if df[col].dtype == 'object':
            # Check if it's a date or string
            if date_or_string(df, col) == 'date':
                df[col] = pd.to_datetime(df[col])
                config[col] = st.column_config.DateColumn(col)
            else:
                # If cardinality is less than 20%, make it a select box
                if df[col].nunique() / len(df) < 0.2:
                    options = df[col].unique().tolist()
                    config[col] = st.column_config.SelectboxColumn(col, options=options)
    return config

def get_modified_columns_and_rows(orig, new):
    """
    Gets the columns and rows with modified values in two DataFrames.

    Args:
        orig: The first DataFrame.
        new: The second DataFrame.

    Returns:
        A list of the columns with modified values.
        A list of the rows with modified values.
    """

    modified_columns = []
    modified_rows = []

    for col in orig.columns:
        if not orig[col].equals(new[col]):
            modified_columns.append(col)

    for i in range(len(orig)):
        row = orig.iloc[i]
        try:
            row2 = new.iloc[i]
            if not row.equals(row2):
                modified_rows.append(i)
        except IndexError:
            pass

    return modified_columns, modified_rows


def update_data_to_file(df, edited_df, file_name, filtered_df):
    """
    If there are updates to the data, and the user wishes to
    save the updates, this function will save the updates to the file
    filtered_df, edited_df and df have the same index.

    Args:
        df (dataframe): The original dataframe that was read from the file.
        edited_df (dataframe): The dataframe that the user edited.
        file_name (string): The name of the file that the data was read from.
        filtered_df (dataframe): The dataframe that was filtered by the user.

    Returns:
        None: The data is saved to file.    
    """
    has_edits = False
    # Check if the data has been edited
    modified_columns, modified_rows = get_modified_columns_and_rows(df, edited_df)
    if len(modified_columns) > 0 or len(modified_rows) > 0:
        has_edits = True

    # This updates existing rows in df that have been edited in edited_df
    df.update(edited_df)

    # If there are new rows, add them to the dataframe
    # Get the index of the new rows
    new_rows = edited_df[~edited_df.index.isin(df.index)]
    
    if not new_rows.empty:
        # Add the new rows to the dataframe
        df = pd.concat([df, new_rows])
        has_edits = True

    # Remove deleted rows that were in filtered_df but not in edited_df
    # Filtered df is the one that the user saw.
    deleted_rows = filtered_df[~filtered_df.index.isin(edited_df.index)].index.tolist()
    if len(deleted_rows) > 0:
        st.warning(f"{len(deleted_rows)} rows will be deleted")
        df = df[~df.index.isin(deleted_rows)]
        has_edits = True

    # If there are edits, save the data
    if has_edits:
        if st.button("Update the data"):
            # view.to_csv(file_name, index=False)
            # If the file is a parquet file, save as parquet
            if file_name.endswith('.parquet'):
                df.to_parquet(file_name, index=False)
                st.success("Data saved")    

            # If the file is a csv file, save as csv
            elif file_name.endswith('.csv'):
                df.to_csv(file_name, index=False)
                st.success("Data saved")
            else:
                file_type = os.path.splitext(file_name)[1]
                st.warning(f"You are trying to save a file with an unknown extension {file_type}")

    return None


def display_editable_data(df, file_name, filtered_df=None):
    """
    Given a dataframe, display it in a table that can be edited.
    Returns the edited dataframe.  This assumes that the columns have the 
    correct datatypes.

    Args:
        df (dataframe): All the rows that were read from the file originally.
        file_name (string): The name of the file that the data was read from.
        filtered_df (dataframe, optional): Filtered dataframe that we may want to display to the user.
            Defaults to None.  If the user edits filtered data, the edits will be applied to the original dataframe.
    """
    # The config tells the data editor how to display the data
    config = get_data_config(df)
    
    # If the data has been filtered, display the filtered data
    # Otherwise, display the original data
    if filtered_df is None:
        filtered_df = df
    
    # Display the data
    edited_df = st.data_editor(filtered_df, column_config=config, num_rows='dynamic')

    # Save the data to file if there are changes
    update_data_to_file(df, edited_df, file_name, filtered_df)
    return None   
