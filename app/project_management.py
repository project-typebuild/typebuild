"""
Create projects, upload files, fetch file names in the project
and other aspects of understanding and manageing assets in the project folder
"""

from glob import glob
import os
import time
from helpers import text_areas
from llm_functions import get_llm_output
from project_management_data import get_column_info, get_data_model
from session_state_management import change_ss_for_project_change
import streamlit as st
import pandas as pd
import prompts
from streamlit_option_menu import option_menu
import sqlite3


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
    user_folder = os.path.join('users', token_name)
    # Get just the directory names, ignore the files
    try:
        project_names = [i for i in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, i))]
    except FileNotFoundError as e:
        # Create the folder
        os.makedirs(user_folder)
        project_names = []

    # Ignore pycache
    project_names = [i for i in project_names if not 'pycache' in i]
    # Add new create project option
    project_names.append('Create new project')
    # Make the first project the default

    default_index = 0
    selected_project = st.sidebar.selectbox(
        "Select project", 
        project_names, 
        index=default_index,
        key='selected_project',
        on_change=change_ss_for_project_change
        )
    if selected_project == 'Create new project':
        create_new_project()
        st.stop()
        
    project_folder = os.path.join(user_folder, selected_project)
    
    # Save to session state
    st.session_state.project_folder = project_folder
    if st.sidebar.checkbox("Manage project"):
        manage_project()
    return None

def manage_project():
    """
    Allows the user to manage key aspects of the selected project:
    - Manage data
    - Set / edit project description
    """
    options = [
        'Project description',
        'Upload data',
        'Data Modelling',
        'Append data (optional)'
    ]

    with st.sidebar:
        selected_option = option_menu(
            "Project settings",
            options=options, 
            key='project_settings',            
            )
    
    if selected_option == 'Upload data':
        file_upload_and_save()

    if selected_option == 'Append data (optional)':
        append_data_to_exisiting_file()

    if selected_option == 'Project description':
        set_project_description()

    if selected_option == 'Data Modelling':
        get_data_model()
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
    project_description = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.project_description = project_description

    project_description_chat()
    st.stop()
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
            res = get_llm_output(st.session_state.project_description_chat, model='gpt-3.5-turbo-16k')
            # Add the response to the chat
            st.session_state.project_description_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.project_description_chat:
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
    token_name = st.session_state.token
    user_folder = os.path.join('users', token_name)

    # Create the user folder if it does not exist
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    project_folder = os.path.join(user_folder, project_name)
    if os.path.exists(project_folder):
        st.write('Project already exists, please rename')
        st.stop()

    # Create the project folder
    project_folder = os.path.join(user_folder, project_name)
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
        st.success("Created the project.  You are ready to use it.")
        time.sleep(2)
    # Save to session state
    st.session_state.project_folder = project_folder
    # Increment session number
    st.session_state.ss_num += 1

    return None


def get_project_df():

    """

    This function gets the project dataframe from the project folder.

    """

    files = glob(f'{st.session_state.project_folder}/data/*.csv')
    if files:
        df = pd.read_csv(files[0])
        st.session_state.df = df
    else:
        st.session_state.df = None

    return None

def file_upload_and_save():
    """
    This function allows the user to upload a CSV or a parquet file, load it as a dataframe,
    and provides a button to save the file as a parquet file with the same name.
    """
    # Define the allowed file types
    allowed_file_types = ['csv', 'parquet']

    # Ask the user to upload a file
    uploaded_file = st.file_uploader("Upload a file", type=allowed_file_types)

    # If a file was uploaded
    if uploaded_file is not None:
        # Get the file extension
        file_extension = uploaded_file.name.split('.')[-1]

        # Load the file as a dataframe
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension == 'parquet':
            df = pd.read_parquet(uploaded_file)

        # Show the dataframe
        st.dataframe(df)

        # Get the name of the uploaded file
        file_name = uploaded_file.name
        # Remove the file extension
        file_name = file_name.replace(f'.{file_extension}', '')

        # Create a button to save the file as a parquet file with the same name
        if st.button('Save as Parquet'):
            # Save the file to the data folder
            file_path = st.session_state.project_folder + '/data/' + file_name + '.parquet'
            # Create folder if it does not exist
            folder_name = os.path.dirname(file_path)
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            df.to_parquet(file_path, index=False)
            st.success(f'File saved successfully')
    st.stop()
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

    # Check if a file was selected


