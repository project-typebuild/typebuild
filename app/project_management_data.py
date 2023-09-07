"""
This file is about managing the project data.  Currently all
project data is stored as parquet and they are stored in a folder
called 'data' in the root folder of the project.

- Document the project data so that it can be sent to the LLM
- Add CRUD functionality to the project data
"""
import pandas as pd
import streamlit as st
import os
from llm_functions import get_llm_output
from helpers import text_areas


def get_column_info_for_df(df):
    """
    Given a dataframe, return the column names and data types.

    Parameters:
    parquet_file (str): The path to the parquet file.

    Returns:
    A dataframe with the column names and data types and column info.
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
    sample_data = df.head(2).to_markdown(index=False)

    system_instruction = """You are helping me document the data.  
    Using the examples revise the column info by:
    - Adding a description for each column
    - If the column is a date, add the date format
    - You should strictly return the column information in the same format provided to you
    """

    prompt = f"""Given below is the draft column information.
    Return the revised column information with descriptions and data types.
    {all_col_infos}

    SAMPLE DATA:
    {sample_data}

    You should strictly return the column information in the same format provided to you
    """
    messages = [
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': prompt},
    ]
    res = get_llm_output(messages, model='gpt-3.5-turbo-16k', max_tokens=2000, temperature=0)
    eval_res = eval(res)
    df = pd.DataFrame(eval_res)

    return df


def get_column_info():
    """
    Loop through all the data files and get the column info for each file.
    """
    project_folder = st.session_state.project_folder
    data_files = os.listdir(project_folder + '/data')
    data_files = [i for i in data_files if i.endswith('.parquet')]
    column_info = {}
    for file in data_files:
        df = pd.read_parquet(project_folder + '/data/' + file)
        df_col_info = get_column_info_for_df(df)
        df_col_info['filename'] = file
        # put the filename as the first column
        cols = df_col_info.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df_col_info = df_col_info[cols]
        column_info = df_col_info.to_markdown(index=False)
    # Add column info to the session state
    st.session_state.column_info = column_info

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
    
    if st.button("Generate column info automatically"):
        generate_col_info = True
    

    if 'column_info' not in st.session_state and generate_col_info:
        get_column_info()
    
    # if generate_col_info:
    if 'column_info' in st.session_state:
        st.header('Column info')
        buf = 'INFORMATION ABOUT THE PROJECT DATA FILE(S)'
        for file in st.session_state.column_info:
            # Add file path first
            file_path = os.path.join(data_folder, file)
            buf += f'\n\nFile path: {file_path}'
            # Add column info
            llm_res = st.session_state.column_info[file]
            # Get the column info from triple backticks
            info = llm_res.split('```')
            if len(info) > 0:
                info = info[1]
                # Split lines and add bullets
                info = '\n\n'.join(['- ' + line for line in info.split('\n') if line.strip() != ''])
            buf += '\n\n' + info
        copy_info = """You can copy the column info and paste it in the data model text area.  
        Please verify the column info and make edits, if necessary."""
        st.code(buf)

    return None