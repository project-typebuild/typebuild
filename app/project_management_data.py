"""
This file is about managing the project data.  Currently all
project data is stored as parquet and they are stored in a folder
called 'data' in the root folder of the project.

- Document the project data so that it can be sent to the LLM
- Add CRUD functionality to the project data
"""
import time
import pandas as pd
import streamlit as st
import os
from llm_functions import get_llm_output
from helpers import text_areas

def convert_to_appropriate_dtypes(df, df_res):
    
    """
    Convert the data types of the dataframe columns to the appropriate data types.

    Parameters:
    df (dataframe): The dataframe to be converted.
    df_res (dataframe): The dataframe with the column names and data types.

    Returns:
    A dataframe with the converted data types.
    
    """
    dtype_dict = dict(zip(df_res.column_name, df_res.column_type))
    for index, col in enumerate(dtype_dict):
        dtype = dtype_dict[col]
        if dtype == 'object': 
            pass
        else:
            try:
                df[col] = df[col].astype(dtype)
            except Exception as e:
                st.error(f"Could not convert the column **{col}** to {dtype}.  Got the following error: {e}")    
    return df
    

def get_column_info_for_df(df):
    """
    Given a dataframe, return the column names and data types.

    Parameters:
    parquet_file (str): The path to the parquet file.

    Returns:
    str: A string containing the column names and data types, with one line per column.
    """

    # Read the parquet file using pandas

    # Get the column names and data types
    all_col_infos = []
    for column in df.columns:
        column_info = {}
        column_info['column_name'] = column
        column_info['column_type'] = str(df[column].dtype)
        column_info['column_info'] = ''
        
        all_col_infos.append(column_info)
        
    # Send this to the LLM with two rows of data and ask it to describe the data.
    
    sample_data = df.sample(3).to_dict('records')
    sample_buf = "HERE IS SOME SAMPLE DATA:\n"

    for row in sample_data:
        for col in row:
            value = row[col]
            # If the value is a string, add quotes around it.  Limit the length of the string to 100 characters.
            if isinstance(value, str):
                if len(value) > 100:
                    value = value[:100] + '...'
                value = f"'{value}'"
            sample_buf += f"- {col}: {value}\n"
        sample_buf += '====================\n'

    # Add possible values for categorical columns
    # Assuming catgorical columns have less than 10 categories
    # and they repeat frequently.
    
    for col in df.columns:
        if df[col].nunique() / len(df) < 0.2:
            if df[col].nunique() < 10:
                sample_buf += f"\nPossible values for {col}: {', '.join(df[col].dropna().astype(str).unique().tolist())}\n"

    system_instruction = """You are helping me document the data.  
    Using the examples revise the column info by:
    - Adding a description for each column
    - If the column is a date, add the date format
    - I will provide the initial column type, you need to check if the initial column type is appropriate or suggest the new column type
    - The possible column dtypes are ['object', 'int64', 'datetime64', 'float64']
    - You should strictly return the column information in the same format provided to you.  Include information about possible values, if provided.
    - Don't add any comments
    """

    prompt = f"""Given below is the draft column information.
    Return the revised column information with descriptions and data types.
    {all_col_infos}

    SAMPLE DATA:
    {sample_buf}

    You should strictly return the column information in the same format provided to you
    """
    messages = [
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': prompt},
    ]
    res = get_llm_output(messages, model='gpt-4', max_tokens=2000, temperature=0)
    df_res = pd.DataFrame(eval(res))
    
    return df_res


def get_column_info():
    """
    Loop through all the data files and get the column info for each file.
    """
    project_folder = st.session_state.project_folder
    data_files = os.listdir(project_folder + '/data')
    data_files = [i for i in data_files if i.endswith('.parquet')]
    column_info = {}
    status = st.empty()
    all_col_infos = []
    all_col_info_markdown = ''
    for file in data_files:
        st.info(f"Getting column info for {file}")
        parquet_file_path = project_folder + '/data/' + file
        df = pd.read_parquet(parquet_file_path)  
        df_col_info = get_column_info_for_df(df)
        df_col_info['filename'] = parquet_file_path
        st.dataframe(df_col_info)
        save_data_model(df_col_info, file)
        df = convert_to_appropriate_dtypes(df, df_col_info)
        try:
            df.to_parquet(parquet_file_path, index=False)
        except Exception as e:
            st.error(f"Could not save the file.  Got the following error: {e}")
        
        status.warning("Pausing for 5 secs to avoid rate limit")
        time.sleep(5)
        # put the filename as the first column
        cols = df_col_info.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df_col_info = df_col_info[cols]
        all_col_infos.append(df_col_info)
        column_info = df_col_info.to_markdown(index=False)
        all_col_info_markdown += column_info + '\n\n'
        status.empty()
    # Add column info to the session state
    st.session_state.column_info = all_col_info_markdown

    return None

def save_data_model(data_model_for_file, filename):
    """
    Saves the data model.  If the model already exists, it will be appended to.
    Any old data model for the given filename will be overwritten.
    """
    data_model_file = st.session_state.project_folder + '/data_model.parquet'
    all_dfs = []
    if os.path.exists(data_model_file):
        current_model = pd.read_parquet(data_model_file)
        # Remove information about filename from the current model
        current_model = current_model[current_model.filename != filename]
        all_dfs.append(current_model)

    all_dfs.append(data_model_for_file)
    df_all_col_infos = pd.concat(all_dfs)
    df_all_col_infos.to_parquet(data_model_file, index=False)
    return None


def get_data_model():
    """
    Save the data model to the project folder.
    """
    # Save the column info to the project folder
    project_folder = st.session_state.project_folder
    data_folder = project_folder + '/data'
    
    data_model_file = project_folder + '/data_model.parquet'

    # If the data model file exists, read it
    if os.path.exists(data_model_file):
        df = pd.read_parquet(data_model_file)
        st.dataframe(df)
        st.session_state.column_info = df.to_markdown(index=False)
        generate_col_info = False
    else:
        if not os.path.exists(data_model_file):
            generate_col_info = True

    if st.button("Re-generate column info automatically"):
        generate_col_info = True

    if 'column_info' not in st.session_state or generate_col_info:
        with st.spinner("Generating column info..."):
            get_column_info()
        
    return None