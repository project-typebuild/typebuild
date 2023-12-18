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

        # remove null values if any
        data_model_df = data_model_df[data_model_df['file_name'].notnull()]
        if data_model_df is not None:
            return list(data_model_df['file_name'].unique())
        else:
            return []

    def _get_all_document_data(self):
        """
        Returns a list of all available document data files.
        """
        documents_path = os.path.join(self.data_folder, 'documents.parquet')
        documents_df = self._read_parquet_file(documents_path)
        if documents_df is not None:
            return list(documents_df['file_name'].unique())
        else:
            return []

    def _get_data_model(self):
        """
        Returns the data model as a DataFrame.
        """
        data_model_path = os.path.join(self.project_folder, 'data_model.parquet')
        return self._read_parquet_file(data_model_path)

    def _get_tabular_data_and_col_names(self, file_name=None):
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

    
    def get_data_and_docs(self):
        """
        Returns a string containing information about the available data.
        """
        # Get nested dict of all available data
        data_dict = self._get_tabular_data_and_col_names()

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
    
    def interface(self):
        """
        # TODO: IF there is a filter condiditon, we need to pass that to LLM operation on the table. 
        The UI for data selection.  
        - Asks if the data is tabular or document.
        - Selects the file
        - Selects the input column
        """
        st.markdown('## Data Selection')
        st.markdown('### Select data type')
        data_type = st.radio('Select data type', ['Tabular', 'Document'], horizontal=True)
        if data_type == 'Tabular':
            tabular_file_paths = self._get_all_available_tabular_data()
            # Create a mappping dict of file_name to full path to avoid displaying the full path
            tabular_files = [os.path.splitext(os.path.basename(file_name))[0] for file_name in tabular_file_paths]
            mappping_dict = dict(zip(tabular_files, tabular_file_paths))
            # Add a select file option to the list if it is not already there
            if 'Select file' not in tabular_files:
                tabular_files.insert(0, 'Select file')
            file_path = st.selectbox('Select file',tabular_files)
            if file_path == 'Select file':
                st.stop()
            file_name = mappping_dict[file_path]

            st.markdown('### Select input column')
            df_data_model = self._get_data_model()
            df_data_model_file = df_data_model[df_data_model['file_name'] == file_name].drop(columns=['file_name'])

            # Get the columns
            columns = df_data_model_file.column_name.unique().tolist()
            if 'Select Column' not in columns:
                columns.insert(0, 'Select Column')
            input_column = st.selectbox('Select input column', columns)

            if input_column == 'Select Column':
                st.stop()
            return file_name, input_column
        else:
            # Read the file and get the columns
            df_document = self._read_parquet_file(os.path.join(self.data_folder, 'documents.parquet'))
            columns = df_document.columns.tolist()

            if 'Select Column' not in columns:
                columns.insert(0, 'Select Column')

            document_files = list(df_document['file_name'].unique())
            # Create a mappping dict of file_name to full path to avoid displaying the full path
            document_files = [os.path.splitext(os.path.basename(file_name))[0] for file_name in document_files]
            mappping_dict = dict(zip(document_files, document_files))
            # Add a select file option to the list if it is not already there
            if 'Select file' not in document_files:
                document_files.insert(0, 'Select file')
            # This contains txt from various files.  Select the file of interst.
            file_path = st.selectbox('Select file', document_files)
            
            if file_path == 'Select file':
                st.stop()

            file_name = mappping_dict[file_path]
            # Get input column
            st.markdown('### Select input column')
            columns.remove('file_name')
            input_column = st.selectbox('Select input column', columns)
            if input_column == 'Select Column':
                st.stop()
            return file_name, input_column