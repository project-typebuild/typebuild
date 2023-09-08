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
    df = df.fillna('')
    for index, col in enumerate(dtype_dict):
        dtype = dtype_dict[col]
        if dtype == 'object': 
            pass
        else:
            df[col] = df[col].astype(dtype)
    
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
    
    sample_data = df.head(3).to_dict('records')
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


    system_instruction = """You are helping me document the data.  
    Using the examples revise the column info by:
    - Adding a description for each column
    - If the column is a date, add the date format
    - I will provide the initial column type, you need to check if the initial column type is appropriate or suggest the new column type
    - The possible column dtypes are ['object', 'int64', 'datetime64', 'float64']
    - You should strictly return the column information in the same format provided to you.
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
        st.dataframe(df_col_info)
        try:
            df = convert_to_appropriate_dtypes(df, df_col_info)
            df.to_parquet(parquet_file_path, index=False)
        except:
            pass
        status.warning("Pausing for 15 secs to avoid rate limit")
        time.sleep(15)
        df_col_info['filename'] = parquet_file_path
        # put the filename as the first column
        cols = df_col_info.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df_col_info = df_col_info[cols]
        all_col_infos.append(df_col_info)
        column_info = df_col_info.to_markdown(index=False)
        all_col_info_markdown += column_info + '\n\n'
        status.empty()
    df_all_col_infos = pd.concat(all_col_infos)
    df_all_col_infos.to_parquet(project_folder + '/data_model.parquet', index=False)
    # Add column info to the session state
    st.session_state.column_info = all_col_info_markdown

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
        generate_col_info = False
    else:
        if not os.path.exists(data_model_file):
            generate_col_info = True

    if 'column_info' not in st.session_state and generate_col_info:
        get_column_info()

    if st.button("Generate column info automatically"):
        generate_col_info = True    
        
    return None