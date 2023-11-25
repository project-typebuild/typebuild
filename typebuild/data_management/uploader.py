import streamlit as st
import os
import pandas as pd
import time
from data_management.modeler import DataModeler
from glob import glob


class DataUploader:

    def __init__(self):
        pass
    
    def upload_and_save_file(self):

        data_folder = os.path.join(st.session_state.project_folder, 'data')
        allowed_tabular_file_extensions = ['csv', 'parquet', 'tsv', 'xlsx']
        allowed_document_file_extensions = ['txt', 'vtt']

    def clean_file_name(self, file_name):

        file_extension = file_name.split('.')[-1]
        # clean the file name without any spaces or periods or symbols
        file_name = file_name.replace(f'.{file_extension}', '').replace(' ', '_').replace('.', '_').replace('-', '_').replace(',','_')
        
        return file_name, file_extension

    def load_dataframe(self, uploaded_file, file_extension):
        if file_extension == 'tsv':
            return pd.read_csv(uploaded_file, sep='\t')
        elif file_extension == 'xlsx':
            return pd.read_excel(uploaded_file)
        elif file_extension == 'csv':
            return pd.read_csv(uploaded_file)
        elif file_extension == 'parquet':
            return pd.read_parquet(uploaded_file)        
        else:
            st.error(f'File type {file_extension} not supported')

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

        # Add file_path to the df
        df['file_name'] = file_path
        df.to_parquet(file_path, index=False)
        st.session_state.files_uploaded = False

    def upload_tabular_data(self, append=False):
        # Define the data folder
        data_folder = os.path.join(st.session_state.project_folder, 'data')

        # Create the data folder if it does not exist
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        # Let the user upload a file and it must be a csv, parquet, tsv, or xlsx file for now. 
        allowed_tabular_file_extensions = ['csv', 'parquet', 'tsv', 'xlsx']
        uploaded_file = st.file_uploader(r"$\textsf{\ Choose your file}$", type=allowed_tabular_file_extensions, key = f'table_upload_{st.session_state.ss_num}')
        if uploaded_file is None:
            st.warning('Please upload a file')
            st.stop()
        uploaded_file_name = uploaded_file.name
        file_name, file_extension = self.clean_file_name(uploaded_file_name)

        # Check if the file extension is valid
        if file_extension not in allowed_tabular_file_extensions:
            st.warning(f'Please upload a file with a valid extension: {", ".join(allowed_tabular_file_extensions)}')
            st.stop()

        # Load the dataframe and clean it
        df = self.load_dataframe(uploaded_file, file_extension)
        df = self.clean_dataframe(df)

        # Assign the file path
        file_path = os.path.join(data_folder, f'{file_name}.parquet')

        data_modeler = DataModeler()
        with st.spinner('We may use a sample of your data to understand your data better... Please wait...'):
            df_data_model = data_modeler.get_data_model(df, file_path)

        # Show the dataframe and data model side by side
        col1 , col2 = st.columns(2)

        # Show the dataframe
        col1.subheader('Your data')
        col1.data_editor(df.head())

        # Show the data model
        col2.subheader('Data model')
        col2.info('The below table is our understanding of your data. \nRead the column_info column to understand what we think about your data.')
        col2.data_editor(df_data_model)

        # if append: then return the dataframe 
        if append:
            return df

        # Save the dataframe

        if col1.button('Save your data'):
            with st.spinner('Saving your data... Please wait...'):
                time.sleep(3)
                self.save_dataframe(df, file_path)
            st.success('Your data has been saved successfully! You can upload more data or go to HOME page by clicking the button below.')
            time.sleep(3)
            st.session_state.files_uploaded = False
            st.session_state.ss_num += 1 # Increment the session state number so that the file upload widget changes
            st.rerun()

        if col2.button('Discard your data'):
            with st.spinner('Discarding your data... Please wait...'):
                time.sleep(3)
                # Delete the file and the data model for the file
                os.remove(file_path)
                data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
                df_data_model = pd.read_parquet(data_model_file)
                df_data_model = df_data_model[df_data_model.file_name != file_path]
                df_data_model.to_parquet(data_model_file, index=False)
                st.session_state.files_uploaded = False
                st.session_state.ss_num += 1
                st.success('Your data has been discarded successfully! You can upload more data or go to HOME page by clicking the button below.')
                time.sleep(3)
                st.rerun()

    def tabular_data(self):
        # Add a markdown empty lines
        st.markdown('<br>', unsafe_allow_html=True) # Add a line break

        # Check if the user wants to upload a file or append data to an existing file
        selection = st.radio(r"$\textsf{\ Do you want to upload a new file or append data to an existing file?}$", \
            ['Upload a new file', 'Append data to an existing file'], key = f'tabular_data_{st.session_state.ss_num}', horizontal=True)
        
        # Add a markdown empty lines
        st.markdown('<br>', unsafe_allow_html=True) # Add a line break

        if selection == 'Upload a new file':
            self.upload_tabular_data()

        elif selection == 'Append data to an existing file':
            self.append_tabular_data()

        return None



    def append_tabular_data(self):

        # Select the file to append data to
        data_folder = os.path.join(st.session_state.project_folder, 'data')

        files = glob(os.path.join(data_folder, '*.parquet'))
        # Add Select a file to the beginning of the list
        files = ['Select a file'] + files

        # Remove the documents.parquet file from the list
        files = [file for file in files if 'documents.parquet' not in file]

        # Remove the directory path from the file names and extensions
        clean_file_names = [os.path.basename(file) for file in files]

        # remove the .parquet extension from the file names
        clean_file_names = [file.replace('.parquet', '') for file in clean_file_names]

        # Create a mapping of file name to file path
        file_name_to_path = {file_name: file_path for file_name, file_path in zip(clean_file_names, files)}

        selected_file_name = st.selectbox(r"$\textsf{\ Select a file to append data to}$", clean_file_names, key = f'tabular_data_append_{st.session_state.ss_num}')
        if selected_file_name == 'Select a file':
            st.warning('Please select a file')
            st.stop()

        selected_file = file_name_to_path[selected_file_name]
        df1 = pd.read_parquet(selected_file)

        # Upload a new file
        df = self.upload_tabular_data(append=True)
        df['file_name'] = selected_file

        # If the columns are different, show the missing columns
        df1_cols = set(df1.columns.tolist())
        df2_cols = set(df.columns.tolist())
        if df1_cols != df2_cols:
            missing_cols = df1_cols.difference(df2_cols)
            st.warning(f'The following columns are missing in the uploaded file: {missing_cols} from the existing file. If you are okay with this, click the button below to append the data.')
        else:
            st.info("The columns in the uploaded file match the columns in the existing file")

        # Create a button to append the data to the existing file
        if st.button('Append data'):
            # Append the data
            df = pd.concat([df1, df])
            # Save the file to the data folder
            df.to_parquet(selected_file, index=False)
            st.success(f'Data appended successfully')
            st.session_state.files_uploaded = False
            st.session_state.ss_num += 1
            st.rerun()



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
            with open(document, 'r', encoding='utf-8', errors='ignore') as f:
                contents = f.read()
                tmp_dict['text'] = contents

            tmp_dict['file_name'] = os.path.basename(document)
            documents.append(tmp_dict)
        
        return pd.DataFrame(documents)


    def upload_document_files(self):
        """
        Uploads the document files and saves them to the documents folder. This function allows the user to upload multiple files at once.
        the documents folder is created if it does not exist and the files are saved to the documents folder temporarily.
        All the documents are then concatenated into a single dataframe and saved to the documents.parquet file in the data folder.
        Once the documents are saved, the files in the documents folder are deleted.
        
        Parameters:
        None

        Returns:
        None

        """
        
        allowed_document_file_extensions = ['txt', 'vtt']
        uploaded_files = st.file_uploader(r"$\textsf{\ Upload your documents}$", \
            type=allowed_document_file_extensions, key = f'document_upload_{st.session_state.ss_num}', \
                accept_multiple_files=True,
                help='Upload your documents here. You may upload multiple documents at once.')
        if uploaded_files is None:
            st.warning('Please upload a file')
            st.stop()
        if len(uploaded_files) == 0:
            st.warning('Please upload a file')
            st.stop()
        
        st.session_state.files_uploaded = True
        st.warning('Adding your new document(s) to the existing documents database')
        tmp_folder = os.path.join(st.session_state.project_folder, 'documents')
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_name, file_extension = self.clean_file_name(file_name)
            tmp_file_path = os.path.join(tmp_folder, f'{file_name}.{file_extension}')

            with open(tmp_file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

        df_chunks = self.create_document_chunk_df(tmp_folder)
        df_chunks['documents_tbid'] = df_chunks.index + 1
        cols = df_chunks.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df_chunks = df_chunks[cols]

        st.dataframe(df_chunks)
        
        if st.button('Save Document'):
            data_folder = os.path.join(st.session_state.project_folder, 'data')
            file_path = os.path.join(data_folder, 'documents.parquet')

            # Change the column name to file_name if it is not already file_name
            if 'file_name' not in df_chunks.columns.tolist():
                df_chunks = df_chunks.rename(columns={'filename': 'file_name'})

            if os.path.exists(file_path):
                df = pd.read_parquet(file_path)
                df = pd.concat([df, df_chunks])
            else:
                df = df_chunks

            df.to_parquet(file_path, index=False)
            st.success('Your document has been saved successfully! You can upload more documents or go to HOME page by clicking the button below.')
            time.sleep(3)
            # Delete all the files in the documents folder
            for f in glob(os.path.join(tmp_folder, '*')):
                os.remove(f)

            
            st.session_state.files_uploaded = False
            st.session_state.ss_num += 1
            st.rerun()

        return None