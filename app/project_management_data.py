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



def get_column_info(df):
    """
    Given a dataframe, return the column names and data types.

    Parameters:
    parquet_file (str): The path to the parquet file.

    Returns:
    str: A string containing the column names and data types, with one line per column.
    """
    # Read the parquet file using pandas

    # Get the column names and data types
    column_info = ''
    for column in df.columns:
        column_info += f'{column} ({df[column].dtype}),\n'

    column_info = column_info[:-2]  # remove the last comma and newline

    # Send this to the LLM with two rows of data and ask it to describe the data.
    sample_data = df.head(2).to_markdown(index=False)

    system_instruction = """You are helping me document the data.  
    Using the examples revise the column info by:
    - Adding a description for each column
    - If the column is a date, add the date format

    Return the column info within triple backticks.    
    """

    prompt = f"""Given below is the draft column information.
    Return the revised column information with descriptions and data types.
    {column_info}

    SAMPLE DATA:
    {sample_data}
    
    Revised column information within triple backticks:
    """
    messages = [
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': prompt},
    ]
    res = get_llm_output(messages)

    # Add column info to the session state
    st.session_state.column_info = res
    return None

