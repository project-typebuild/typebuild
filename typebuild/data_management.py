import pandas as pd
import os
import time
import streamlit as st
from glob import glob
from datetime import datetime
import chardet


class DataManager:
    def __init__(self):
        pass

    def upload_data_file(self, uploaded_file, file_extension):
        data_folder = os.path.join(st.session_state.project_folder, 'data')

        if file_extension not in ['csv', 'parquet', 'tsv', 'xlsx']:
            st.error(f'File type {file_extension} not supported')
            st.stop()

        df = self.load_dataframe(uploaded_file, file_extension)
        df = self.clean_dataframe(df)

        st.dataframe(df)

        file_name = uploaded_file.name.replace(f'.{file_extension}', '')
        st.info("Once you save the data, we will explore a few lines of data to a language model to understand the data. This will help us later to generate code for the data.")

        if st.button('Save Data'):
            file_path = os.path.join(data_folder, f'{file_name}.parquet')
            self.save_dataframe(df, file_path)
            st.success('File saved successfully')
            st.session_state.files_uploaded = False
            del st.session_state.data_manager
            # time.sleep(3)
            st.rerun()

    def load_dataframe(self, uploaded_file, file_extension):
        if file_extension == 'tsv':
            return pd.read_csv(uploaded_file, sep='\t')
        elif file_extension == 'xlsx':
            return pd.read_excel(uploaded_file)
        else:
            return pd.read_parquet(uploaded_file) if file_extension == 'parquet' else pd.read_csv(uploaded_file)

    def clean_dataframe(self, df):
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        col_names = df.columns.tolist()
        col_names = [col + f'_{col_names[:i].count(col) + 1}' if col_names.count(col) > 1 else col for i, col in enumerate(col_names)]
        df.columns = col_names

        all_col_infos = [{'column_name': column, 'column_type': str(df[column].dtype), 'column_info': ''} for column in df.columns]

        for col_info in all_col_infos:
            col_name, col_type = col_info['column_name'], col_info['column_type']
            df[col_name] = df[col_name].astype(col_type) if col_type != 'object' else df[col_name].astype(str)

        return df

    def save_dataframe(self, df, file_path):
        folder_name = os.path.dirname(file_path)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        df.to_parquet(file_path, index=False)

    def upload_document_file(self, uploaded_file, file_extension):
        tmp_folder = os.path.join(st.session_state.project_folder, 'documents')

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1]
        file_name = file_name.replace(f'.{file_extension}', '')
        tmp_file_path = os.path.join(tmp_folder, f'{file_name}.{file_extension}')

        with open(tmp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

    def file_upload_and_save(self):
        data_folder = os.path.join(st.session_state.project_folder, 'data')

        allowed_data_file_types = ['csv', 'parquet', 'xlsx', 'tsv', 'sqlite', 'db', 'sqlite3']
        allowed_document_file_types = ['pdf', 'txt', 'vtt']

        uploaded_files = st.file_uploader("Upload a file", type=allowed_data_file_types + allowed_document_file_types, accept_multiple_files=True)

        file_extension = None

        if len(uploaded_files) == 1:
            st.session_state.files_uploaded = True
            st.warning('Adding your new document(s) to the existing documents database')
            uploaded_file = uploaded_files[0]
            file_extension = uploaded_file.name.split('.')[-1]

            if file_extension in ['sqlite', 'db', 'sqlite3']:
                self.export_sqlite_to_parquet(uploaded_file, data_folder)
            elif file_extension in allowed_data_file_types:
                self.upload_data_file(uploaded_file, file_extension)
            elif file_extension in allowed_document_file_types:
                self.upload_document_file(uploaded_file, file_extension)

        elif len(uploaded_files) > 1:
            st.warning('Adding your new document(s) to the existing documents database')
            file_extension = uploaded_files[0].name.split('.')[-1]

            if file_extension in allowed_document_file_types:
                for uploaded_file in uploaded_files:
                    self.upload_document_file(uploaded_file, file_extension)

        if file_extension and file_extension in allowed_document_file_types:
            tmp_folder = os.path.join(st.session_state.project_folder, 'documents')
            df_chunks = self.create_document_chunk_df(tmp_folder)
            df_chunks['documents_tbid'] = df_chunks.index + 1
            cols = df_chunks.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            df_chunks = df_chunks[cols]

            st.dataframe(df_chunks)
            uploaded_file = None

            if st.button('Save Document'):
                file_path = os.path.join(data_folder, 'documents.parquet')

                if os.path.exists(file_path):
                    df = pd.read_parquet(file_path)
                    df = pd.concat([df, df_chunks]).drop_duplicates(keep='first')
                    df.to_parquet(file_path, index=False)
                    st.success('Data added successfully')
                else:
                    df_chunks = df_chunks.drop_duplicates(keep='first')
                    df_chunks.to_parquet(file_path, index=False)
                    st.success('Data saved successfully')

            del st.session_state.data_manager

    def append_data_to_existing_file(self):
        file_path = os.path.join(st.session_state.project_folder, 'data')
        files = glob(os.path.join(file_path, '*.parquet'))
        selected_file = st.selectbox('Select a file to append data to', files)
        df1 = pd.read_parquet(selected_file)
        uploaded_file = st.file_uploader('Upload a file', type=['csv', 'parquet'])

        if uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1]
            df2 = pd.read_csv(uploaded_file) if file_extension == 'csv' else pd.read_parquet(uploaded_file)
            st.dataframe(df2)

            df1_cols, df2_cols = set(df1.columns.tolist()), set(df2.columns.tolist())

            if df1_cols != df2_cols:
                missing_cols = df1_cols.difference(df2_cols)
                st.warning(f'The following columns are missing in the uploaded file: {missing_cols}')
            else:
                st.info('The columns in the uploaded file match the columns in the existing file')

            if st.button('Append data'):
                df = pd.concat([df1, df2])
                df.to_parquet(selected_file, index=False)
                st.success('Data appended successfully')

    def export_sqlite_to_parquet(self, uploaded_file, data_folder):
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1]
        file_name = file_name.replace(f'.{file_extension}', '')
        tmp_file_path = os.path.join(data_folder, f'{file_name}.{file_extension}')

        with open(tmp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        df = pd.read_sqlite(tmp_file_path)
        df.to_parquet(os.path.join(data_folder, f'{file_name}.parquet'), index=False)

    def create_document_chunk_df(self, documents_folder):
        """
        Select the documents to be used for the analysis and create a dataframe with the text of the chunks of the documents

        Parameters
        ----------
        documents_folder : str
            The path to the folder with the documents
        """
        tmp_folder = os.path.join(st.session_state.project_folder, 'documents')
        available_documents = glob(os.path.join(tmp_folder, '*'))
        # read all text files in the folder
        documents = []
        for document in available_documents:
            tmp_dict = {}
            with open(document, 'r') as f:
                contents = f.read()
                # encoding = chardet.detect(contents.encode('utf-8'))['encoding']
                # # encoding = chardet.detect(contents)['encoding']
                # contents = contents.decode('utf-8')
                tmp_dict['text'] = contents

            tmp_dict['filename'] = os.path.basename(document)
            documents.append(tmp_dict)
        
        return pd.DataFrame(documents)
