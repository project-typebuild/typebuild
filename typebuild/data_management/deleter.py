import pandas as pd
import os
import time
import streamlit as st
from glob import glob


class DataDeleter:
    def __init__(self):
        pass

    def get_tablular_files(self):

        data_folder = st.session_state.data_folder
        
        # get all parquet files
        parquet_files = glob(os.path.join(data_folder, '*.parquet'))

        # remove the documents file
        file_names = [x for x in parquet_files if 'documents.parquet' not in x]

        return file_names

    def get_document_files(self):
            
        document_file = os.path.join(st.session_state.data_folder, 'documents.parquet')

        df_document = pd.read_parquet(document_file)

        # Change the column name filename to file_name if it is not already (This is the bug from the previous version)
        if 'filename' in df_document.columns:
            df_document = df_document.rename(columns={'filename': 'file_name'})
            df_document.to_parquet(document_file, index=False)

        file_names = df_document['file_name'].tolist()

        return file_names


    def delete_tabular_files(self, file_names):

        data_folder = st.session_state.data_folder

        for file_name in file_names:
                
                file_path = os.path.join(data_folder, file_name)
    
                os.remove(file_path)

        return None

    def delete_document_files(self, file_names):

        data_folder = st.session_state.data_folder

        document_file = os.path.join(data_folder, 'documents.parquet')

        df_document = pd.read_parquet(document_file)

        df_document = df_document[~df_document['file_name'].isin(file_names)]

        df_document.to_parquet(document_file)

        return None


    def delete_files(self):

        tabular_files = self.get_tablular_files()
        document_files = self.get_document_files()

        # Delete the directory name from the file names along with the extension
        clean_tabular_files = [os.path.basename(x) for x in tabular_files]
        document_files = [os.path.basename(x) for x in document_files]

        # remove the extension from the file names, should be parquet
        clean_tabular_files = [os.path.splitext(x)[0] for x in clean_tabular_files]

        # create a dictionary of file names and file paths
        tabular_files_dict = dict(zip(clean_tabular_files, tabular_files))

        # Add line break for visual consistency
        st.markdown('\n')

        # Ask the user what they want to delete tabular files or document files
        delete_type = st.radio(r"$\textsf{\ What type of files do you want to delete?}$", ['Data Files', 'Document Files'], key = f'delete_type_{st.session_state.ss_num}', horizontal=True)

        # Add line break for visual consistency
        st.markdown('\n')

        if delete_type == 'Data Files':

            # Ask the user to select the files they want to delete
            file_names = st.multiselect(r"$\textsf{\ Select the files you want to delete}$", clean_tabular_files, key = f'delete_table_files_{st.session_state.ss_num}')

            message_placeholder = st.empty()

            if len(file_names) == 0:
                st.warning('Please select at least one file to delete')
                st.stop()
            # Ask the user to confirm the deletion
            confirm_delete = message_placeholder.button('Confirm Delete')

            if confirm_delete:
                with st.spinner('Deleting files...'):
                    time.sleep(3)
                # replace the file names with the file paths
                file_names = [tabular_files_dict[x] for x in file_names]

                # Delete the files
                self.delete_tabular_files(file_names)

                message_placeholder.success('Files deleted successfully')
                time.sleep(2)
                st.session_state.ss_num += 1
                st.rerun()
        
        elif delete_type == 'Document Files':
            
            # Ask the user to select the files they want to delete
            file_names = st.multiselect(r"$\textsf{\ Select the files you want to delete}$", document_files, key = f'delete_document_files_{st.session_state.ss_num}')

            if len(file_names) == 0:
                st.warning('Please select at least one file to delete')
                st.stop()
            message_placeholder = st.empty()

            # Ask the user to confirm the deletion
            confirm_delete = message_placeholder.button('Confirm Delete')

            if confirm_delete:
                with st.spinner('Deleting files...'):
                    time.sleep(3)
                # Delete the files
                self.delete_document_files(file_names)

                message_placeholder.success('Files deleted successfully')
                time.sleep(2)
                st.session_state.ss_num += 1
                st.rerun()

