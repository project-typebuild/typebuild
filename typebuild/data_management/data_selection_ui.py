import streamlit as st
import pandas as pd
import os

def select_data_type():
    """
    Allows user to select the data type (Tabular or Document).
    """
    st.markdown('## Data Selection')
    st.markdown('### Select data type')
    return st.radio('Select data type', ['Tabular', 'Document'], horizontal=True)

def get_all_available_tabular_data():
        """
        Returns a list of all available parquet files.
        """
        data_folder = st.session_state.data_folder
        if os.path.exists(data_folder):
            return [file_name for file_name in os.listdir(data_folder) if file_name.endswith('.parquet')]
        else:
            return []

def select_tabular_file():
    """
    Allows user to select a file for tabular data.
    """
    tabular_files = get_all_available_tabular_data()
    if 'Select file' not in tabular_files:
        tabular_files.insert(0, 'Select file')
    file_path = st.selectbox('Select file', tabular_files)
    # Add data folder path to the file name
    file_name = os.path.join(st.session_state.data_folder, file_path)
    if file_path == 'Select file':
        return None
    return file_name

def select_column(file_name):
    """
    Allows user to select a column from the file.
    """
    df = pd.read_parquet(file_name)
    columns = df.columns.tolist()
    if 'Select Column' not in columns:
        columns.insert(0, 'Select Column')
    input_column = st.selectbox('Select input column', columns)
    if input_column == 'Select Column':
        return None
    return input_column

def interface():
    """
    The UI for data selection.
    """
    data_type = select_data_type()
    if data_type == 'Tabular':        
        file_name = select_tabular_file()
    else:
        file_name = os.path.join(st.session_state.data_folder, 'documents.parquet')
    if not file_name:
        return {}
    input_column = select_column(file_name)
    if not input_column:
        return {}
    # Return a string with file name and column name
    return f"""This data has been selected for analysis:\nSelected File: {file_name}\nSelected Column: {input_column}.\nThe file and column name will be give to the agent for analysis."""
    
