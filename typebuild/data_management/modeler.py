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
from extractors import Extractors
from glob import glob

class DataModeler:
    """
    A class that represents a data modeler.

    The DataModeler class provides methods to retrieve column information from a dataframe.

    Methods:
    - __init__: Initializes a DataModeler object.
    - get_column_info_for_df: Retrieves the column names and data types from a dataframe.
    """

    def __init__(self):
        pass

    def get_column_info_for_df(self, df):
        """
        Given a dataframe, return the column names and data types.

        Parameters:
        df (pandas.DataFrame): The dataframe for which to retrieve column information.

        Returns:
        pandas.DataFrame: A dataframe containing the column names, data types, and column information.
        The dataframe has the following columns:
        - column_name: The name of the column.
        - column_type: The data type of the column.
        - column_info: Additional information about the column.
        """
        all_col_infos = self._get_column_names_and_types(df)
        sample_buf = self._get_sample_data(df)

        sample_buf += self._get_possible_values(df)

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
        extractor = Extractors()
        res = get_llm_output(messages, model='gpt-3.5-turbo', max_tokens=2000, temperature=0)
        list_of_dicts = extractor.extract_list_of_dicts_from_string(res)
        df_data_model = pd.DataFrame(list_of_dicts)
        df_data_model.column_type = df_data_model.column_type.fillna('object')
        df_data_model = df_data_model[['column_name', 'column_type', 'column_info']]    
        return df_data_model


    def _get_column_names_and_types(self, df):
        """
        Retrieve the column names and data types from a dataframe.

        Parameters:
        df (pandas.DataFrame): The dataframe for which to retrieve column information.

        Returns:
        list: A list of dictionaries containing the column names, data types, and empty column information.
        Each dictionary has the following keys:
        - column_name: The name of the column.
        - column_type: The data type of the column.
        - column_info: An empty string.
        """
        all_col_infos = []
        for column in df.columns:
            column_info = {}
            column_info['column_name'] = column
            column_info['column_type'] = str(df[column].dtype)
            column_info['column_info'] = ''
            all_col_infos.append(column_info)
        return all_col_infos


    def _get_sample_data(self, df):
        """
        Retrieve sample data from a dataframe.

        Parameters:
        df (pandas.DataFrame): The dataframe from which to retrieve sample data.

        Returns:
        str: A string containing the sample data.
        The sample data is formatted as follows:
        - Each row is represented as a bullet point.
        - Each column name and its corresponding value are displayed.
        - If the value is a string longer than 100 characters, it is truncated and followed by '...'.
        - Each row is separated by a line of equal signs.
        """
        if len(df) > 2:
            sample_data = df.sample(3).to_dict('records')
        else:
            sample_data = df.to_dict('records')
        sample_buf = "HERE IS SOME SAMPLE DATA:\n"
        for row in sample_data:
            for col in row:
                value = row[col]
                if isinstance(value, str):
                    if len(value) > 100:
                        value = value[:100] + '...'
                    value = f"'{value}'"
                sample_buf += f"- {col}: {value}\n"
            sample_buf += '====================\n'
        return sample_buf


    def _get_possible_values(self, df):
        """
        Retrieve possible values for each column in a dataframe.

        Parameters:
        df (pandas.DataFrame): The dataframe for which to retrieve possible values.

        Returns:
        str: A string containing the possible values for each column.
        The possible values are displayed as follows:
        - Each column name is followed by a colon and a space.
        - The possible values for the column are displayed, separated by commas.
        - Only columns with a unique value ratio less than 0.2 and less than 10 unique values are considered.
        """
        sample_buf = ""
        for col in df.columns:
            try:
                if df[col].nunique() / len(df) < 0.2:
                    if df[col].nunique() < 10:
                        sample_buf += f"\nPossible values for {col}: {', '.join(df[col].dropna().astype(str).unique().tolist())}\n"
            except:
                pass
        return sample_buf


    def convert_to_appropriate_dtypes(self, df, data_model):
        
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
                    pass  
        return df

    def save_data_model(self, df_data_model, file_path):

        """
        Save the data model.

        Parameters:
        df_data_model (dataframe): The dataframe with the column names, data types, and column information.
        file_path (str): The path to the file to which to save the dataframe.

        Returns:
        None
        """
        data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
        # Add file_path to the df
        df_data_model['file_name'] = file_path
        all_dfs = []
        if os.path.exists(data_model_file):
            current_model = pd.read_parquet(data_model_file)
            all_dfs.append(current_model)

        all_dfs.append(df_data_model)
        df_all_col_infos = pd.concat(all_dfs)
        df_all_col_infos = df_all_col_infos.drop_duplicates(subset=['file_name', 'column_name'], keep='last')
        df_all_col_infos.to_parquet(data_model_file, index=False)
        return None

    def save_dataframe(self, df, file_path):
        """
        Save the dataframe.

        Parameters:
        df (dataframe): The dataframe to be saved.
        file_path (str): The path to the file to which to save the dataframe.

        Returns:
        None
        """
        folder_name = os.path.dirname(file_path)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        df.to_parquet(file_path, index=False)
        return None

    def get_data_model(self, df=None, file_path=None):
        """
        Creates a data model for the given dataframe and saves it. Also updates the dataframe with the appropriate data types and saves it.

        Parameters:
            df (pandas.DataFrame): The dataframe for which to generate the data model.
            file_name (str): The name of the file to save the dataframe.

        Returns:
            df_data_model (pandas.DataFrame): The dataframe with the column names, data types, and column information. (Data Model)
        """

        data_model_file_name = os.path.join(st.session_state.project_folder, 'data_model.parquet')
        if os.path.exists(data_model_file_name):
            df_data_model = pd.read_parquet(data_model_file_name)
            df_data_model = df_data_model[df_data_model.file_name == file_path]
            if len(df_data_model) > 0:
                return df_data_model
        
        if df is None and file_path is None:
            st.error("You need to provide either a dataframe or a file path")
            return None

        df_data_model = self.get_column_info_for_df(df)
        df = self.convert_to_appropriate_dtypes(df, df_data_model)
        self.save_data_model(df_data_model, data_model_file_name)
        self.save_dataframe(df, file_path)

        return df_data_model

    def interface(self):
        
        #Let the user select the file from the list of files in the data folder
        # Get the data model and get the files available 

        data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
        if not os.path.exists(data_model_file):
            st.error("No data model found.  Please upload some data first.")
            return None
        data_model = pd.read_parquet(data_model_file)
        available_files = data_model.file_name.unique().tolist()
        file_path = st.selectbox("Select your data", available_files)
        df_data_model = data_model[data_model.file_name == file_path]
        st.write(df_data_model)
        return None
