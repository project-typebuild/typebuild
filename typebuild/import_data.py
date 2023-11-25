import streamlit as st

# RANU: I CREATED THIS NEW FUNCTION JUST TO LET YOU KNOW THAT WE 
# HAVE TO ADD THESE FUNCTIONALITIES SOMEWHERE.
def data_menus():
    options = [
        'Upload your data',
        'Fetch data',
    ]


    default_index = 0

    selected_option = st.radio(
        "Select an option", 
        options, 
        captions=["CSV, XLSX, TXT, VTT, etc.", "YouTube, Google Search"],
        horizontal=True, 
        index=default_index
        )
    st.markdown("---")
    if selected_option == 'Upload your data':
        file_upload_and_save()
        get_data_model()
        st.stop()

    if selected_option == 'Fetch data':
        if st.checkbox("Get data from YouTube"):
            from tools.yt_search import main as yt_search
            yt_search()
            st.warning("Uncheck get data from YouTube to go to project settings")
        if st.checkbox("Get data from Google"):
            from tools.google_search import main as google_search
            google_search()
            st.warning("Uncheck get data from Google to go to project settings")
        st.stop()



def export_sqlite_to_parquet(uploaded_file, output_dir):
    
    tmp_folder = os.path.join(st.session_state.project_folder, 'documents')
    # Create the tmp folder if it does not exist
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    
    with open(os.path.join(tmp_folder, 'tmp.sqlite'), 'wb') as f:
        f.write(uploaded_file.read())
    # Connect to the SQLite database
    conn = sqlite3.connect(os.path.join(tmp_folder, 'tmp.sqlite'))
    # Get the list of all tables in the database
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = conn.execute(query).fetchall()
    tables = [table[0] for table in tables]

    tables = st.multiselect("Select tables to import", tables)
    if st.button("Import these tables"):
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # For each table, read it into a pandas DataFrame and then write it to a Parquet file
        for table in tables:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            df.to_parquet(os.path.join(output_dir, f"{table}.parquet"), index=False)

    # Close the SQLite connection
    conn.close()
    return None

def upload_data_file(uploaded_file, file_extension):
    """
    Upload data files to import them into the project.
    """
    data_folder = os.path.join(st.session_state.project_folder, 'data')
    # Load the file as a dataframe
    if file_extension == 'csv':
        df = pd.read_csv(uploaded_file)
    elif file_extension == 'parquet':
        df = pd.read_parquet(uploaded_file)
    elif file_extension == 'tsv':
        df = pd.read_csv(uploaded_file, sep='\t')
    elif file_extension in ['xlsx']:
        df = pd.read_excel(uploaded_file)
    else:
        st.error(f'File type {file_extension} not supported')
        st.stop()    
    # Clean column names.  Strip, lower case, replace spaces with underscores
    df.columns = [i.strip().lower().replace(' ', '_') for i in df.columns]
    
    # Create a streamlit form, with all columns and data types and allow the user to edit the data types

    # Get the list of column names
    col_names = df.columns.tolist()

    # If there are duplicate column names, add _1, _2, etc. to the end of the column name
    for i, col_name in enumerate(col_names):
        if col_names.count(col_name) > 1:
            col_names[i] = col_name + '_' + str(col_names[:i].count(col_name) + 1)

    # Rename the columns with the updated column names
    df.columns = col_names

    # If there are duplicate col names, add _1, _2, etc. to the end of the col name
    # Get the list of col names
        
    # Get the column names and data types


    # Get the column names and data types
    all_col_infos = []
    for column in df.columns:
        column_info = {}
        column_info['column_name'] = column
        column_info['column_type'] = str(df[column].dtype)
        column_info['column_info'] = ''
        all_col_infos.append(column_info)

    # Update the data types of the dataframe
    for col_info in all_col_infos:
        col_name = col_info['column_name']
        col_type = col_info['column_type']
        if col_type != 'object':
            df[col_name] = df[col_name].astype(col_type)

    # Show the dataframe
    
    st.dataframe(df)

    # Get the name of the uploaded file
    file_name = uploaded_file.name
    # Remove the file extension
    file_name = file_name.replace(f'.{file_extension}', '')
    st.info("Once you save the data, we will explore a few lines of data to a language model to understand the data.  This will help us later to generate code for the data.")
    # Create a button to save the file as a parquet file with the same name
    if st.button('Save Data'):
        
        # Save the file to the data folder
        file_path = os.path.join(data_folder, file_name + '.parquet')
        # Create folder if it does not exist
        folder_name = os.path.dirname(file_path)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        df = clean_col_formats(df)
        df.to_parquet(file_path, index=False)
        st.success(f'File saved successfully')
        st.session_state.files_uploaded = False

    return None

def clean_col_formats(df):
    """
    Apache arrow requires clearn formatting.  Look at the 
    column names and data types and clean them up.

    Try saving as column type and see if it works. If not, save as string.

    Args:
    - df (dataframe): The dataframe to clean

    Returns:
    - df (dataframe): The cleaned dataframe
    """

    # Get the list of column names
    col_names = df.columns.tolist()

    # If there are duplicate column names, add _1, _2, etc. to the end of the column name
    for i, col_name in enumerate(col_names):
        if col_names.count(col_name) > 1:
            col_names[i] = col_name + '_' + str(col_names[:i].count(col_name) + 1)

    # Rename the columns with the updated column names
    df.columns = col_names

    # st.dataframe(df)

    # If there are duplicate col names, add _1, _2, etc. to the end of the col name
    # Get the list of col names
        
    # Get the column names and data types
    all_col_infos = []
    for column in df.columns:
        column_info = {}
        column_info['column_name'] = column
        column_info['column_type'] = str(df[column].dtype)
        column_info['column_info'] = ''
        all_col_infos.append(column_info)

    # Update the data types of the dataframe
    for col_info in all_col_infos:
        col_name = col_info['column_name']
        col_type = col_info['column_type']
        if col_type != 'object':
            try:
                df[col_name] = df[col_name].astype(col_type)
            except:
                df[col_name] = df[col_name].astype(str)
        
        if col_type == 'object':
            df[col_name] = df[col_name].astype(str)

    return df

def upload_document_file(uploaded_file, file_extension):
    """
    This function allows the user to upload a document file and save it to the project folder.
    Args:
    - uploaded_file (file): The file uploaded by the user.
    - file_extension (str): The file extension of the uploaded file.

    Returns:
    - None
    """
    tmp_folder = os.path.join(st.session_state.project_folder, 'documents')
    # Create the tmp folder if it does not exist
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    
    # Get the name of the uploaded file
    file_name = uploaded_file.name
    # Get the file extension
    file_extension = file_name.split('.')[-1]
    # Remove the file extension
    file_name = file_name.replace(f'.{file_extension}', '')
    # Save the file to the tmp folder
    
    tmp_file_path =  os.path.join(tmp_folder, f"{file_name}.{file_extension}")
    with open(tmp_file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
        uploaded_file = None
    return None


def file_upload_and_save():
    """
    This function allows the user to upload a CSV or a parquet file, load it as a dataframe,
    and provides a button to save the file as a parquet file with the same name.
    """
    data_folder = os.path.join(st.session_state.project_folder, 'data')
    # Define the allowed file types
    allowed_data_file_types = ['csv', 'parquet', 'xlsx' , 'tsv', 'sqlite', 'db', 'sqlite3']
    allowed_document_file_types = ['pdf', 'txt', 'vtt']
    # Ask the user to upload a file
    uploaded_files = st.file_uploader(
        "Upload a file", 
        type=allowed_data_file_types + allowed_document_file_types, 
        accept_multiple_files=True)

    file_extension = None
    if len(uploaded_files) ==1:
        st.session_state.files_uploaded = True
        st.warning(f'Adding your new document(s) to the existing documents database')   
        uploaded_file = uploaded_files[0]
        # Get the file extension
        file_extension = uploaded_file.name.split('.')[-1]
        # If the file is a data file, upload it as a data file
        if file_extension in ['sqlite', 'db', 'sqlite3']:
            export_sqlite_to_parquet(uploaded_file, data_folder)
            st.success(f'Files saved successfully')
        elif file_extension in allowed_data_file_types:
            upload_data_file(uploaded_file, file_extension)
        # If the file is a document file, upload it as a document file
        elif file_extension in allowed_document_file_types:
            upload_document_file(uploaded_file, file_extension)

    elif len(uploaded_files) > 1:
        st.warning(f'Adding your new document(s) to the existing documents database')
        # Get the file extension
        file_extension = uploaded_files[0].name.split('.')[-1]
        # If the file is a document file, upload it as a document file
        if file_extension in allowed_document_file_types:
            for uploaded_file in uploaded_files:
                upload_document_file(uploaded_file, file_extension)
    if file_extension:
        if file_extension in allowed_document_file_types:
            tmp_folder = os.path.join(st.session_state.project_folder, 'documents')
            # Create chunks of the document and save it to the data folder
            df_chunks = create_document_chunk_df(tmp_folder)
            # Add documents_tbid to the dataframe
            df_chunks['documents_tbid'] = df_chunks.index+1
                # Move the id column to the front
            cols = df_chunks.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            df_chunks = df_chunks[cols]

            # Show the dataframe
            st.dataframe(df_chunks)
            uploaded_file = None
            # Create a button to save the file as a parquet file in the data folder with the same name
            # If the parquet file already exists, append the data to the existing file
            if st.button('Save Document'):
                # Save the file to the data folder
                file_path = os.path.join(data_folder, 'documents.parquet')
                # If the file already exists, append the data to the existing file
                if os.path.exists(file_path):
                    # Load the existing file as a dataframe
                    df = pd.read_parquet(file_path)
                    # Append the data
                    df = pd.concat([df, df_chunks])
                    df = df.drop_duplicates(keep='first')
                    # Save the file to the data folder
                    df.to_parquet(file_path, index=False)
                    st.success(f'Data added successfully')
                else:
                    # Save the file to the data folder
                    df_chunks = df_chunks.drop_duplicates(keep='first')
                    df_chunks.to_parquet(file_path, index=False)
                    st.success(f'Data saved successfully')

    return None


def append_data_to_exisiting_file():

    """
    This function allows the user to append data to an existing file. 
    It also allows the user to process the data and save it to a new file.
    You can upload a CSV, JSON, PARQUET, EXCEL, or PICKLE file.

    Once the file is uploaded, it is added to an existing parquet file.

    """

    file_path = os.path.join(st.session_state.project_folder, 'data')

    # Get the list of files in the project folder
    files = glob(os.path.join(file_path, '*.parquet'))

    # Ask the user to select a file to append data to
    selected_file = st.selectbox("Select a file to append data to", files)
    df1 = pd.read_parquet(selected_file)
    # Upload a new file
    uploaded_file = st.file_uploader("Upload a file", type=['csv', 'parquet'])
    # If a file was uploaded, create a df2 dataframe
    if uploaded_file is not None:
        # Get the file extension
        file_extension = uploaded_file.name.split('.')[-1]

        # Load the file as a dataframe
        if file_extension == 'csv':
            df2 = pd.read_csv(uploaded_file)
        elif file_extension == 'parquet':
            df2 = pd.read_parquet(uploaded_file)

        # Show the dataframe
        st.dataframe(df2)

        # If the columns are different, show the missing columns
        df1_cols = set(df1.columns.tolist())
        df2_cols = set(df2.columns.tolist())
        if df1_cols != df2_cols:
            missing_cols = df1_cols.difference(df2_cols)
            st.warning(f'The following columns are missing in the uploaded file: {missing_cols}')
        else:
            st.info("The columns in the uploaded file match the columns in the existing file")


        # Create a button to append the data to the existing file
        if st.button('Append data'):
            # Append the data
            df = pd.concat([df1, df2])
            # Save the file to the data folder
            df.to_parquet(selected_file, index=False)
            st.success(f'Data appended successfully')
            uploaded_file = None
    return None


#######################################################################

##### GPT-4 REFACTORED CODE #####

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
from glob import glob

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
                pass  
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
    res = get_llm_output(messages, model='gpt-3.5-turbo', max_tokens=2000, temperature=0)
    # Get the list of dicts from the string
    list_of_dicts = extract_list_of_dicts_from_string(res)
    df_res = pd.DataFrame(list_of_dicts)
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
    data_folder = os.path.join(project_folder, 'data')
    data_files = glob(os.path.join(data_folder, '*.parquet'))

    # Get the list of files that have already been processed
    if data_model is None:
        # Create an empty dataframe
        data_model = pd.DataFrame(columns=['column_name', 'column_type', 'column_info', 'file_name'])
        data_model.to_parquet(os.path.join(project_folder, 'data_model.parquet'), index=False)
    processed_files = data_model.file_name.unique().tolist()

    if data_model is not None:
        data_model.column_info = data_model.column_info.fillna('')


    column_info = {}
    status = st.empty()
    all_col_infos = []
    all_col_info_markdown = ''

    for parquet_file_path in data_files:
        df = pd.read_parquet(parquet_file_path)  
        # Check which columns have col info
        avbl_col_info_for_file = data_model[
            (data_model.file_name == parquet_file_path) &
            (data_model.column_info != '')
            ].column_name.tolist()
        # Get missing cols
        missing_col_info_for_file = [i for i in df.columns.tolist() if i not in avbl_col_info_for_file]
        all_missing_dfs = []
        if len(missing_col_info_for_file) > 0:
            st.info(f"Getting column info for {missing_col_info_for_file} in {parquet_file_path}")
            df_missing = df[missing_col_info_for_file]
            df_col_info_missing = get_column_info_for_df(df_missing)
            all_missing_dfs.append(df_col_info_missing)
            df_col_info = df_col_info_missing
        else:
            df_col_info = data_model[data_model.file_name == parquet_file_path]
            
        df_col_info['file_name'] = parquet_file_path
        save_data_model(df_col_info, parquet_file_path)
        df = convert_to_appropriate_dtypes(df, df_col_info)
        try:
            df.to_parquet(parquet_file_path, index=False)
        except Exception as e:
            st.error(f"Could not save the file.  Got the following error: {e}")
        
        status.warning("Pausing for 5 secs to avoid rate limit")
        cols = df_col_info.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df_col_info = df_col_info[cols]
        all_col_infos.append(df_col_info)
        column_info = df_col_info.to_markdown(index=False)
        all_col_info_markdown += column_info + '\n\n'
        status.empty()

    st.session_state.column_info = all_col_info_markdown

    return None

def save_data_model(data_model_for_file, file_name):
    """
    Saves the data model.  If the model already exists, it will be appended to.
    Any old data model for the given file_name will be overwritten.
    """
    data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
    all_dfs = []
    if os.path.exists(data_model_file):
        current_model = pd.read_parquet(data_model_file)
        # Remove information about file_name from the current model
        # current_model = current_model[current_model.file_name != file_name]
        all_dfs.append(current_model)

    all_dfs.append(data_model_for_file)
    df_all_col_infos = pd.concat(all_dfs)
    # Remove duplicates for given file name and column name, keeping the last one
    df_all_col_infos = df_all_col_infos.drop_duplicates(subset=['file_name', 'column_name'], keep='last')
    df_all_col_infos.to_parquet(data_model_file, index=False)
    return None


import os
import pandas as pd
from glob import glob
import streamlit as st
import time

def check_uploaded_files():
    """
    Checks if files have been uploaded and updates the session state.
    """
    if 'files_uploaded' not in st.session_state:
        st.session_state.files_uploaded = False

def get_processed_files(data_model_file, data_files):
    """
    Determines which files have been processed and which need processing.

    Args:
    - data_model_file: The path to the data model file.
    - data_files: List of data file paths.

    Returns:
    - A tuple containing lists of processed files and files to process.
    """
    processed_files = []
    files_to_process = data_files

    if os.path.exists(data_model_file):
        data_model_df = pd.read_parquet(data_model_file)
        st.session_state.column_info = data_model_df.to_markdown(index=False)

        processed_files = data_model_df.file_name.unique().tolist()
        files_to_process = [i for i in data_files if i not in processed_files]

        for file in processed_files:
            df = pd.read_parquet(file)
            cols_in_file = df.columns.tolist()
            data_model_df.column_info = data_model_df.column_info.fillna('')
            cols_in_data_model = data_model_df[
                (data_model_df.file_name == file) &
                (data_model_df.column_info != '')].column_name.tolist()
            cols_not_in_data_model = [i for i in cols_in_file if i not in cols_in_data_model]
            if cols_not_in_data_model:
                files_to_process.append(file)

    return processed_files, files_to_process

def update_column_info(files_to_process, data_model_df, data_model_file):
    """
    Updates column info based on user input and session state.

    Args:
    - files_to_process: List of files that need processing.
    - data_model_df: DataFrame containing the data model.
    - data_model_file: The path to the data model file.
    """
    if files_to_process and not st.session_state.files_uploaded:
        if st.checkbox(
            "🚨 Re-generate column info automatically for the filtered files 🚨",
            help="The LLM will recreate column definitions. Use this only if the table needs major changes."
        ):
            st.warning("Use this only if the table needs major changes")
            if st.button("Confirm regeneration"):
                data_model_df.loc[data_model_df.file_name.isin(files_to_process), 'column_info'] = ''
                # Additional logic for regeneration can be added here

def get_data_model():
    """
    Main function to orchestrate the data model generation process.
    """
    check_uploaded_files()

    project_folder = st.session_state.project_folder
    data_folder = os.path.join(project_folder, 'data')
    data_model_file = os.path.join(project_folder, 'data_model.parquet')
    data_files = glob(os.path.join(data_folder, '*.parquet'))

    processed_files, files_to_process = get_processed_files(data_model_file, data_files)

    data_model_df = None if not os.path.exists(data_model_file) else pd.read_parquet(data_model_file)

    update_column_info(files_to_process, data_model_df, data_model_file)

    if 'column_info' not in st.session_state or files_to_process:
        with st.spinner("Studying the data to understand it..."):
            get_column_info(data_model=data_model_df, new_files_only=True)
            st.success("Done studying the data. You can start using it now")
            time.sleep(3)
            st.rerun()

    return None


def update_colum_types_for_table(data_model, data_model_file):
    """
    Looks at the data model and converts
    the selected files
    """
    st.markdown("""---""")
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
        st.session_state.filtered_files_for_data_model = selected_files
        display_editable_data(
            df=data_model,
            filtered_df=data_model[data_model.file_name.isin(selected_files)], 
            file_name=data_model_file
            )
        if st.button("Update the column types"):
            for file in selected_files:
                df = pd.read_parquet(file)
                df = convert_to_appropriate_dtypes(df, data_model[data_model.file_name == file])
                df.to_parquet(file, index=False)
            st.success("Updated the column types")
    return None