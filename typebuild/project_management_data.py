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
from plugins.llms import get_llm_output
from helpers import text_areas
from plugins.data_widgets import display_editable_data

def convert_to_appropriate_dtypes(df, data_model):
    
    """
    Convert the data types of the dataframe columns to the appropriate data types.

    Parameters:
    df (dataframe): The dataframe to be converted.
    data_model (dataframe): The dataframe with the column names and data types.

    Returns:
    A dataframe with the converted data types.
    
    """
    dtype_dict = dict(zip(data_model.column_name, data_model.column_type))
    for index, col in enumerate(dtype_dict):
        dtype = dtype_dict[col]
        if dtype == 'object': 
            pass
        elif 'date' in dtype:
            df[col] = pd.to_datetime(df[col], errors='coerce')
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
    
    if len(df) > 2:
        sample_data = df.sample(3).to_dict('records')
    else:
        sample_data = df.to_dict('records')
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
        try:
            if df[col].nunique() / len(df) < 0.2:
                if df[col].nunique() < 10:
                    sample_buf += f"\nPossible values for {col}: {', '.join(df[col].dropna().astype(str).unique().tolist())}\n"
        except:
            # If the column is not a string, this will fail
            pass

    system_instruction = """You are helping me document the data.  
    Using the examples revise the column info by:
    - Adding a detailed description for each column
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
    # if there are any missing values, fill them with object
    df_res.column_type = df_res.column_type.fillna('object')
    # There are some additional columns created by the LLM. we need the three columns we are interested in
    df_res = df_res[['column_name', 'column_type', 'column_info']]    
    return df_res


def get_column_info(data_model, new_files_only=True):
    """
    Loop through all the data files and get the column info for each file.
    """
    # Get the list of files in data model

    project_folder = st.session_state.project_folder
    data_files = os.listdir(project_folder + '/data')
    data_files = [i for i in data_files if i.endswith('.parquet')]
    if new_files_only:
        # Get the list of files that have already been processed
        if data_model is None:
            processed_files = []
        else:
            processed_files = data_model.file_name.unique().tolist()
        data_files = [i for i in data_files if i not in processed_files]
    column_info = {}
    status = st.empty()
    all_col_infos = []
    all_col_info_markdown = ''
    for file in data_files:
        st.info(f"Getting column info for {file}")
        parquet_file_path = project_folder + '/data/' + file
        df = pd.read_parquet(parquet_file_path)  
        df_col_info = get_column_info_for_df(df)
        df_col_info['file_name'] = parquet_file_path
        # st.dataframe(df_col_info)
        save_data_model(df_col_info, file)
        df = convert_to_appropriate_dtypes(df, df_col_info)
        try:
            df.to_parquet(parquet_file_path, index=False)
        except Exception as e:
            st.error(f"Could not save the file.  Got the following error: {e}")
        
        status.warning("Pausing for 5 secs to avoid rate limit")
        time.sleep(5)
        # put the file_name as the first column
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

def save_data_model(data_model_for_file, file_name):
    """
    Saves the data model.  If the model already exists, it will be appended to.
    Any old data model for the given file_name will be overwritten.
    """
    data_model_file = st.session_state.project_folder + '/data_model.parquet'
    all_dfs = []
    if os.path.exists(data_model_file):
        current_model = pd.read_parquet(data_model_file)
        # Remove information about file_name from the current model
        current_model = current_model[current_model.file_name != file_name]
        all_dfs.append(current_model)

    all_dfs.append(data_model_for_file)
    df_all_col_infos = pd.concat(all_dfs)
    df_all_col_infos.to_parquet(data_model_file, index=False)
    return None


def get_data_model():
    """
    Save the data model to the project folder.
    """
    generate_for_new_files_only = True
    # Save the column info to the project folder
    project_folder = st.session_state.project_folder
    
    data_folder = project_folder + '/data'
    
    data_model_file = project_folder + '/data_model.parquet'

    # Get a list of parquet data files
    data_files = os.listdir(data_folder)
    data_files = [i for i in data_files if i.endswith('.parquet')]
    # Add data folder path to the file names
    data_files = [data_folder + '/' + i for i in data_files]
    # See which files have already been processed
    processed_files = []
    files_to_process = data_files
    # If the data model file exists, read it
    if os.path.exists(data_model_file):
        data_model_df = pd.read_parquet(data_model_file)
        st.session_state.column_info = data_model_df.to_markdown(index=False)
        generate_col_info = False
        processed_files = data_model_df.file_name.unique().tolist()
        files_to_process = [i for i in data_files if i not in processed_files]
        update_colum_types_for_table(data_model_df, data_model_file)

    else:
        data_model_df = None
        if not os.path.exists(data_model_file):
            generate_col_info = True

    # It the data model does not have information about all the files, generate the column info
    if files_to_process:
        generate_col_info = True
        

    if data_files:
        if st.checkbox(
            "🚨 Re-generate column info automatically 🚨",
            help="The LLM will recreate column definitions.  Use this only if the table needs major changes.",
            ):
                st.warning("Use this only if the table needs major changes")
                if st.button("Confirm regeneration"):
                    generate_col_info = True
                    generate_for_new_files_only = False

        if 'column_info' not in st.session_state or generate_col_info:
            with st.spinner("Studying the data to understand it..."):
                get_column_info(data_model=data_model_df, new_files_only=generate_for_new_files_only)
                st.success("Done studying the data.  You can start using it now")
                time.sleep(3)
                st.rerun()
    return None

def update_colum_types_for_table(data_model, data_model_file):
    """
    Looks at the data model and converts
    the selected files
    """
    st.subheader("Does this look right?")
    info = """Take a look at the column_info and see if it looks right.  Getting it right will help us a lot when we work with the data."""
    st.info(info)
    # Get the list of files
    files = data_model.file_name.unique().tolist()
    # Get the list of files that have been selected

    selected_files = st.multiselect(
        "Filter files", 
        files,
        help="You can filter the file(s) you wish to examine now."
        )

    if not selected_files:
        display_editable_data(data_model, data_model_file)
    else:
        display_editable_data(data_model[data_model.file_name.isin(selected_files)], data_model_file)
        if st.button("Update the column types"):
            for file in selected_files:
                df = pd.read_parquet(file)
                df = convert_to_appropriate_dtypes(df, data_model[data_model.file_name == file])
                df.to_parquet(file, index=False)
            st.success("Updated the column types")
    return None