import streamlit as st
import os
import pandas as pd


class DataSelector:
    """
    A class for selecting and managing data files.
    """

    def __init__(self):
        """
        Initializes the DataSelector object.
        """
        if 'project_folder' not in st.session_state:
            st.session_state.project_folder = '/Users/ranu/.typebuild/users/admin/test_lewys/'
        self.project_folder = st.session_state.project_folder
        self.data_folder = os.path.join(self.project_folder, 'data')

    def _read_parquet_file(self, file_path):
        """
        Reads a parquet file and returns the DataFrame.
        """
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        else:
            return None

    def _get_all_available_tabular_data(self):
        """
        Returns a list of all available tabular data files.
        """
        data_model_path = os.path.join(self.project_folder, 'data_model.parquet')
        data_model_df = self._read_parquet_file(data_model_path)
        if data_model_df is not None:
            return data_model_df['file_name'].tolist()
        else:
            return []

    def _get_all_document_data(self):
        """
        Returns a list of all available document data files.
        """
        documents_path = os.path.join(self.data_folder, 'documents.parquet')
        documents_df = self._read_parquet_file(documents_path)
        if documents_df is not None:
            return documents_df['file_name'].tolist()
        else:
            return []

    def _get_data_model(self):
        """
        Returns the data model as a DataFrame.
        """
        data_model_path = os.path.join(self.project_folder, 'data_model.parquet')
        return self._read_parquet_file(data_model_path)

    def _get_tabular_data_as_nested_dict(self, file_name=None):
        """
        Returns the tabular data as a nested dictionary.
        If file_name is provided, returns the data for that specific file.
        If file_name is not provided, returns the data for all files.
        """
        df_data_model = self._get_data_model()
        if df_data_model is not None:
            if file_name:
                df_data_model_file = df_data_model[df_data_model['file_name'] == file_name].drop(columns=['file_name'])
                df_data_model_records = df_data_model_file.to_dict(orient='records')

                data_dict = {
                    'file_name': file_name,
                    'records': df_data_model_records
                }
            else:
                data_dict = {}
                for file_name in df_data_model['file_name'].unique():
                    df_data_model_file = df_data_model[df_data_model['file_name'] == file_name].drop(columns=['file_name'])
                    df_data_model_records = df_data_model_file.to_dict(orient='records')

                    data_dict[file_name] = {
                        'file_name': file_name,
                        'records': df_data_model_records
                    }

            return data_dict
        else:
            return {}

    def get_available_data_info_of_project(self):
        """
        Returns a string containing information about the available data.
        """
        # Get nested dict of all available data
        data_dict = self._get_tabular_data_as_nested_dict()

        # Get all available document data
        document_data = self._get_all_document_data()

        # Get all available tabular data
        tabular_data = self._get_all_available_tabular_data()

        # Return the nested dict, document data, and tabular data as a string
        available_data_info = f"Available data:\n\n"

        available_data_info += f"\nTabular data files:\n"
        available_data_info += "\n".join(tabular_data)

        available_data_info += f"\n\nData model with file_name as key and available columns and its info:\n"
        available_data_info += f"- {data_dict}\n\n"

        if len(document_data) > 0:
            available_data_info += f"Available Documents:\n"
            available_data_info += "\n".join(document_data)

        return available_data_info