"""
Create projects, upload files, fetch file names in the project
and other aspects of understanding and manageing assets in the project folder
"""

from glob import glob
import os
import time
from helpers import text_areas
from llm_functions import get_llm_output
from documents_management import create_document_chunk_df
from menu import reset_menu
from project_management_data import get_column_info, get_data_model
from session_state_management import change_ss_for_project_change
import streamlit as st
import pandas as pd
import prompts
from streamlit_option_menu import option_menu
import extra_streamlit_components as stx
import sqlite3
from streamlit_extras.stateful_button import button
import json
import toml 
import pandas_profiling
from streamlit_pandas_profiling import st_profile_report
home_dir = os.path.expanduser("~")

def get_project_database():

    """
    This function establishes a connection to the project database. It will loop through the existing tables and create a dictionary of table_name and top two rows of the table. 

    Args:
    - None

    Returns:
    - table_dict (dict): A dictionary of table_name and top two rows of the table in markdown format.

    """

    # Get the list of tables in the database
    con = sqlite3.connect(f'{st.session_state.project_folder}/data.db')
    st.session_state.con = con
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", con=st.session_state.con)
    table_names = tables['name'].tolist()
    st.warning(f'The following tables are available in the database:{table_names}')
    # Create a dictionary of table_name and top two rows of the table
    table_dict = {}
    for table_name in table_names:
        table_dict[table_name] = pd.read_sql_query(f"SELECT * FROM {table_name}", con).head(2).to_markdown()
    return table_dict


def get_project_file_folder():
    """
    Returns the path to the project folder for the current user.
    Projects are folders within the user's folder.
    Project file is the path to the main.py file.
    
    Args:
    - None
    
    Returns:
    - project_file (str): The path to the project file.
    """
    token_name = st.session_state.token
    user_folder = st.session_state.user_folder 
    # Get just the directory names, ignore the files
    try:
        project_names = [i for i in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, i))]
    except FileNotFoundError as e:
        # Create the folder
        os.makedirs(user_folder)
        project_names = []

    # Ignore pycache
    project_names = [i for i in project_names if not 'pycache' in i]
    # Project names does not start in '.'
    project_names = [i for i in project_names if not i.startswith('.')]
    # Add new create project option
    project_names.append('Create new project')
    # Make the first project the default

    default_index = 0

    # If no project is selected, select the first project
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = project_names[default_index]
    
    # Project names in menu have "~" in them.
    if "~" in st.session_state.new_menu:
        selected_project = st.session_state.new_menu.split("~")[1]
        # If it is different from the current project, change the project
        # and change session state
        if selected_project != st.session_state.selected_project:
            st.session_state.selected_project = selected_project
            change_ss_for_project_change()
    
    selected_project = st.session_state.selected_project
    manage_project_toggle = False
    if selected_project == 'Create new project':
        create_new_project()        
        st.stop()
    
    project_folder = os.path.join(user_folder, selected_project)
    

    # Save to session state
    st.session_state.project_folder = project_folder
    
    return None

def add_llm_data_model(data_model_pkl_file):
    import pickle as pk
    with open(data_model_pkl_file, 'rb') as f:
        llm_model = pk.load(f)
    llm_data = ""
    for file_name in llm_model:
        llm_data += f"File path: {file_name}\n"
        system_instruction_path = llm_model[file_name]['system_instruction_path']
        # Open the system instruction
        with open(system_instruction_path, 'r') as f:
            si = f.read()
    
        # Add the system instruction to the llm_data for context
        llm_data += f"This table was created using an llm who got this instruction: {si}\n"

        # Add column info to the llm_data
        col_info = llm_model[file_name]['col_info']
        llm_data += f"Column info:\n{col_info}\n"
    return llm_data

def show_project_settings():
    show_settings = False
    if st.session_state.new_menu == 'project_settings':
        show_settings = True
    
    project_folder = st.session_state.project_folder
    data_model_file = project_folder + '/data_model.parquet'
    if not os.path.exists(data_model_file):
        show_settings = True
    
    return show_settings

def manage_project():
    """
    Allows the user to manage key aspects of the selected project:
    - Manage data
    - Set / edit project description
    """
    show_settings = show_project_settings()

    if show_settings:
        if st.sidebar.checkbox("Get data from YouTube"):
            from tools.yt_search import main as yt_search
            yt_search()
            st.warning("Uncheck get data from YouTube to go to project settings")
            st.stop()
        project_settings()

    return None

def project_settings():
    """
    This function allows the user to manage key aspects of the selected project:
    - Manage data
    - Set / edit project description
    """    
    
    # Get the project folder
    project_folder = st.session_state.project_folder
    # If the file called data_model.parquet is missing, toggle the manage project button
    data_model_file = project_folder + '/data_model.parquet'
    if os.path.exists(data_model_file):
        # Add data description to session state
        st.session_state.data_description = pd.read_parquet(data_model_file).to_markdown(index=False)
    
        # Close project settings button
        if st.sidebar.button('🛑 Close project settings 🛑'):
            st.warning("You have to close project settings to work on other aspects of the project.")
            reset_menu()

    options = [
        'Project description',
        'Upload data',
        'Data Modelling',
        'Config',
        'Upload Custom LLM'
    ]
    
    val = stx.stepper_bar(steps=options)

    selected_option = options[val]

    if selected_option == 'Upload data':
        file_upload_and_save()
        st.stop()

    if selected_option == 'Append data (optional)':
        append_data_to_exisiting_file()
        st.stop()

    if selected_option == 'Project description':
        set_project_description()
        st.stop()

    if selected_option == 'Data Modelling':
        get_data_model()
        st.stop()
    
    if selected_option == 'Upload Custom LLM':
        upload_custom_llm_file()
        st.stop()
    
    if selected_option == 'Config':
        config_project()
        st.stop()

    return None

def set_project_description():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = st.session_state.project_folder + '/project_settings/project_description.txt'
    key = 'Project Description'
    widget_label = 'Project Description'
    st.subheader('Project description')
    project_description = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.project_description = project_description

    project_description_chat()
    return None


def project_description_chat():
    """
    A chat on the project description.
    That could be exported to the project description file.
    """
    # If there is no project description chat in the session state, create one
    if 'project_description_chat' not in st.session_state:
        st.session_state.project_description_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='project_description_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(
                st.session_state.project_description_chat, 
                model='gpt-3.5-turbo-16k'
                )
            # Add the response to the chat
            st.session_state.project_description_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.project_description_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None

def set_user_requirements():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = st.session_state.project_folder + '/project_settings/user_requirements.txt'
    key = 'User Requirements'
    widget_label = 'User Requirements'
    st.subheader('User requirements')
    user_requirements = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.user_requirements = user_requirements

    user_requirements_chat()
    st.stop()
    return None

def user_requirements_chat():

    """
    A chat on the user requirements.
    That could be exported to the user requirements file.
    """
    # If there is no user requirements chat in the session state, create one
    if 'user_requirements_chat' not in st.session_state:
        st.session_state.user_requirements_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='user_requirements_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(st.session_state.user_requirements_chat, model='gpt-3.5-turbo-16k')
            # Add the response to the chat
            st.session_state.user_requirements_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.user_requirements_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None


def create_new_project():
    """
    Creates a new project folder, main.py file, and __init__.py file.
    TODO: Need to call this somewhere.
    """
    # Get the project name
    project_name = st.text_input("Enter the project name")
    if project_name == '':
        st.warning('Enter a project name')
        st.stop()
    # Lower case and replace spaces with underscores
    project_name = project_name.lower().replace(' ', '_')
    # Check if the project name already exists
    # token_name = st.session_state.token
    # user_folder = os.path.join('users', token_name)

    # Get the path to the home directory
    home_dir = os.path.expanduser("~")

    # Create the path to the .typebuild directory
    user_folder = os.path.join(home_dir, ".typebuild",'users', st.session_state.token)    
    
    # Check if the directory exists
    if not os.path.exists(user_folder):
        # Create the directory if it doesn't exist
        os.makedirs(user_folder)

    # Add user folder to the session state
    st.session_state.user_folder = user_folder

    # Project folder is project name inside the user folder
    project_folder = f"{user_folder}/{project_name}"
    if os.path.exists(project_folder):
        st.write('Project already exists, please rename')
        st.stop()
    st.session_state.project_folder = project_folder
    # Create the project folder
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    data_folder = os.path.join(project_folder, 'data')
    views_folder = os.path.join(project_folder, 'views')
    project_settings_folder = os.path.join(project_folder, 'project_settings')

    # Create these folders if they do not exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    if not os.path.exists(views_folder):
        os.makedirs(views_folder)
    if not os.path.exists(project_settings_folder):
            os.makedirs(project_settings_folder)

    # Create the __init__.py file
    init_file = os.path.join(project_folder, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
        st.success("Created the project.  Taking you to it now...")
        # Save to session state
        st.session_state.project_folder = project_folder
        # Increment session number
        st.session_state.ss_num += 1
        st.session_state[f'selected_project_{st.session_state.ss_num}'] = project_name
        st.session_state.selected_project = project_name
        time.sleep(2)
        # Take user to project settings
        reset_menu(new_menu='project_settings')
    return None


def get_project_df():

    """

    This function gets the project dataframe from the project folder.

    """

    files = glob(f'{st.session_state.project_folder}/data/*.parquet')

    if len(files) > 0:
        # Get the list of files in the project folder
        files = glob(f'{st.session_state.project_folder}/data/*.parquet')
        # Ask the user to select a file to append data to
        selected_file = st.selectbox("Select a file to append data to", files)
        # Load the file as a dataframe
        df = pd.read_parquet(selected_file)
        # Show the dataframe
        st.dataframe(df)
        return df

    return None

def export_sqlite_to_parquet(uploaded_file, output_dir):
    
    tmp_folder = st.session_state.project_folder + '/documents/'
    # Create the tmp folder if it does not exist
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    
    with open(tmp_folder + "tmp.sqlite", 'wb') as f:
        f.write(uploaded_file.read())
    # Connect to the SQLite database
    conn = sqlite3.connect(f'{tmp_folder}/tmp.sqlite')

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
    data_folder = st.session_state.project_folder + '/data'
    # Load the file as a dataframe
    if file_extension == 'csv':
        df = pd.read_csv(uploaded_file)
    elif file_extension == 'parquet':
        df = pd.read_parquet(uploaded_file)
    elif file_extension == 'tsv':
        df = pd.read_csv(uploaded_file, sep='\t')
    elif file_extension in ['.xlsx']:
        df = pd.read_excel(uploaded_file)
    
    # Clean column names.  Strip, lower case, replace spaces with underscores
    df.columns = [i.strip().lower().replace(' ', '_') for i in df.columns]
    # Create a streamlit form, with all columns and data types and allow the user to edit the data types
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

    button_placeholder = st.empty()
    # Pandas profiler report
    pr = df.profile_report()
    st_profile_report(pr)

    # Get the name of the uploaded file
    file_name = uploaded_file.name
    # Remove the file extension
    file_name = file_name.replace(f'.{file_extension}', '')
    
    # Create a button to save the file as a parquet file with the same name
    if button_placeholder.button('Save as Parquet'):
        # Save the file to the data folder
        file_path = st.session_state.project_folder + '/data/' + file_name + '.parquet'
        # Create folder if it does not exist
        folder_name = os.path.dirname(file_path)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        df.to_parquet(file_path, index=False)
        st.success(f'File saved successfully')

    return None


def upload_document_file(uploaded_file, file_extension):
    """
    This function allows the user to upload a document file and save it to the project folder.
    Args:
    - uploaded_file (file): The file uploaded by the user.
    - file_extension (str): The file extension of the uploaded file.

    Returns:
    - None
    """
    tmp_folder = st.session_state.project_folder + '/documents/'
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
    
    tmp_file_path =  tmp_folder + file_name + '.' + file_extension
    with open(tmp_file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
        uploaded_file = None
    return None

def file_upload_and_save():
    """
    This function allows the user to upload a CSV or a parquet file, load it as a dataframe,
    and provides a button to save the file as a parquet file with the same name.
    """
    data_folder = st.session_state.project_folder + '/data'
    # Define the allowed file types
    allowed_data_file_types = ['csv', 'parquet', 'xlsx' , 'tsv', 'sqlite', 'db', 'sqlite3']
    allowed_document_file_types = ['pdf', 'txt']
    # Ask the user to upload a file
    uploaded_files = st.file_uploader(
        "Upload a file", 
        type=allowed_data_file_types + allowed_document_file_types, 
        accept_multiple_files=True)

    file_extension = None
    if len(uploaded_files) ==1:
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
            tmp_folder = st.session_state.project_folder + '/documents/'
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
                file_path = st.session_state.project_folder + '/data/documents.parquet'
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

    file_path = os.path.join(st.session_state.project_folder + '/data/')

    # Get the list of files in the project folder
    files = glob(f'{file_path}/*.parquet')

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

import ast

def verify_functions(file_path, function_dict):
    # Parse the Python file using the ast library
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())


    # Extract all function definitions from the parsed tree
    functions = []
    for node in ast.walk(tree):
        tmp_dict = {}
        if isinstance(node, ast.FunctionDef):
            function_name = node.name
            args = [arg.arg for arg in node.args.args]
            tmp_dict['function_name'] = function_name
            tmp_dict['args'] = args
            functions.append(tmp_dict)

    # Check if the get_llm_output function is present in the functions list
    # if get_llm_output function present and the args do not match, show an error
        with open('plugins/llms.py', 'r') as f:
            tree = f.read()

    if 'get_llm_output' not in [i['function_name'] for i in functions]:
        st.error('get_llm_output function not found in the file, you need to have a get_llm_output function in the file, for the reference, see the get_llm_output function in the code block below')
        st.code(tree, language='python')
        st.stop()
    else:
        # Get the args for the get_llm_output function
        get_llm_output_args = [i['args'] for i in functions if i['function_name'] == 'get_llm_output'][0]
        # If the args do not match, show an error
        if get_llm_output_args != function_dict['args']:
            st.error(f'get_llm_output function args do not match. Expected: {function_dict["args"]}, Actual: {get_llm_output_args}')
            st.code(tree, language='python')
            st.stop()

        else:
            return True
    

def upload_custom_llm_file():
    """
    This function allows the user to upload a custom LLM file.
    """
    # Ask the user to upload a file
    uploaded_file = st.file_uploader("Upload a file", type=['py'])
    # If a file was uploaded, create a df2 dataframe
    if uploaded_file is not None:
        # Get the file extension
        file_extension = uploaded_file.name.split('.')[-1]
        # Load the file as a dataframe
        if file_extension == 'py':
            # Save the file to the tmp folder
            tmp_folder = '/tmp/'
            tmp_file_path =  tmp_folder + uploaded_file.name
            with open(tmp_file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            # Verify the functions in the file
            function_dict = {'function_name': 'get_llm_output', 'args': ['input', 'max_tokens', 'temperature', 'model']}
            if verify_functions(tmp_file_path, function_dict):
                success_message = st.empty()
                success_message.success('Functions verified successfully, you can now save the file by clicking the button below')
                if button('Save Custom LLM', key='save_custom_llm'):
                    success_message.empty()
                    file_path = 'plugins/custom_llm.py'
                    # if the file already exists, ask the user if they want to overwrite it or not
                    if os.path.exists(file_path):
                        overwrite = st.radio('File already exists, do you want to overwrite it?', ['Yes', 'No'], index=1)
                        if overwrite == 'Yes':
                            with st.spinner('Saving file...'):
                                time.sleep(2)
                                # Save the file to the data folder
                                with open(file_path, 'wb') as f:
                                    f.write(uploaded_file.getbuffer())
                                st.success(f'File saved successfully')
                        else:
                            st.warning('File not saved')
                    else:
                        # Save the file to the data folder
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(f'File saved successfully')
    st.stop()
    return None

def config_project():
    """
    For a new project, there should be a config.json file in the project_settings folder. if not, then this function will create one.
    this config file should have the following keys:
    - preferred model (str): The preferred model for the project, e.g. gpt-3.5-turbo-16k, gpt-3.5-turbo, gpt-4, etc.
    - api key (str): The API key for the openai API, if preferred model is openai's
    - function_call_availabilty (bool): Does the user have access to the 0613 models of openai?

    Save the api key to streamlit secrets.toml file
    
    """
    # If the file already exists, show the config in the default values
    config_file = st.session_state.project_folder + '/project_settings/config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        st.session_state.config = config
    else:
        st.session_state.config = {}
    # If the config exists in the session state, use the default values
    st.info('These are the choices you made when you created the project, you can change them if you want')
    
    api_key = st.text_input('Enter the API key', value=st.secrets.get('api_key', st.session_state.config.get('api_key', '')))
    function_call_availabilty = st.checkbox(
        "(Expert setting) I have access to function calling", 
        value=st.session_state.config.get('function_call_availabilty', True),
        help="Do you have access to openai models ending in 0613? they have a feature called function calling.",
        )
    
    if st.button("Submit config"):
        # Save the config to the config.json file
        config = {}
        config['api_key'] = api_key
        config['function_call_availabilty'] = function_call_availabilty
        # Save the config to the config.json file
        with st.spinner('Saving config...'):
            time.sleep(2)
        with open(config_file, 'w') as f:
            json.dump(config, f)
            st.toast('Hip!')
            time.sleep(.5)
            st.toast('Hip!')
            time.sleep(.5)
            st.toast('Hooray!', icon='🎉')
        # Get the project folder from the session state
        project_folder = st.session_state.project_folder
        # Create the secrets.toml file if it does not exist
        secrets_file_path = project_folder + '/secrets.toml'
        if not os.path.exists(secrets_file_path):
            with open(secrets_file_path, 'w') as f:
                f.write('')
        with open(secrets_file_path, 'r') as f:
            config_ = toml.load(f)
            config_['api_key'] = api_key
        with open(secrets_file_path, 'w') as f:
            toml.dump(config_, f)