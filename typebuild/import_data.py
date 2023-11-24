

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
