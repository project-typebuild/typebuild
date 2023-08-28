"""
Create projects, upload files, fetch file names in the project
and other aspects of understanding and manageing assets in the project folder
"""

from glob import glob
import os
import time
from helpers import text_areas
from llm_functions import get_llm_output
from session_state_management import change_ss_for_project_change
import streamlit as st
import pandas as pd
import prompts
from streamlit_option_menu import option_menu
import sqlite3
con = sqlite3.connect(f'{st.session_state.project_folder}/data.db')
st.session_state.con = con

def get_project_database():

    """
    This function establishes a connection to the project database. It will loop through the existing tables and create a dictionary of table_name and top two rows of the table. 

    Args:
    - None

    Returns:
    - table_dict (dict): A dictionary of table_name and top two rows of the table in markdown format.

    """

    # Get the list of tables in the database
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
        'Data Modelling',
        'Upload data',
    ]

    with st.sidebar:
        selected_option = option_menu(
            "Project settings",
            options=options, 
            key='project_settings',            
            )
    
    if selected_option == 'Upload data':
        file_upload_and_save()

    if selected_option == 'Project description':
        set_project_description()

    if selected_option == 'Data Modelling':
        st.header('Data Modelling')
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

    files = glob(f'{st.session_state.project_folder}/*.csv')
    if files:
        df = pd.read_csv(files[0])
        st.session_state.df = df
    else:
        st.session_state.df = None

    return None

def file_upload_and_save():
    """
    This function allows the user to upload a file and save it to the current folder. 
    It also allows the user to process the data and save it to a new file.
    You can upload a CSV, JSON, PARQUET, EXCEL, or PICKLE file.

    Once the file is uploaded, it is added to a sqlite database. the filename becomes the table name in the database.

    TODO: Add support for other file types: Parquet, Excel, etc.

    """

    # Create a file uploader
    uploaded_file = st.file_uploader("Choose a CSV or a JSON file")

    # Check if a file was uploaded
    if uploaded_file is not None:
        if st.button("Save file"):
            file_name 
        # Get the file name
        file_name = uploaded_file.name

        file_path = os.path.join(st.session_state.project_folder, file_name)

        # Save the file to the project folder
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Display a success message
        st.success(f"File '{file_name}' uploaded and saved successfully!")

        # Check if the uploaded file is a CSV file
        if file_name.endswith('.csv'):
            # Load the CSV file into a pandas DataFrame
            df = pd.read_csv(file_path)

            # Do some data processing here...

            # Save the processed data to a new CSV file
            df.to_csv(file_path, index=False)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")
        
        # Check if the uploaded file is a JSON file
        elif file_name.endswith('.json'):
            # Load the JSON file into a pandas DataFrame
            df = pd.read_json(file_path)

            # Do some data processing here...

            # Save the processed data to a new JSON file
            df.to_json(file_path, orient='records', lines=True)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")

        # Check if the uploaded file is a Parquet file
        elif file_name.endswith('.parquet'):
            # Load the Parquet file into a pandas DataFrame
            df = pd.read_parquet(file_path)

            # Do some data processing here...

            # Save the processed data to a new Parquet file
            df.to_parquet(file_path, index=False)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")

        # Check if the uploaded file is an Excel file
        elif file_name.endswith('.xlsx'):
            # Load the Excel file into a pandas DataFrame
            df = pd.read_excel(file_path)

            # Do some data processing here...

            # Save the processed data to a new Excel file
            df.to_excel(file_path, index=False)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")

        # Check if the uploaded file is a Pickle file
        elif file_name.endswith('.pkl'):
            # Load the Pickle file into a pandas DataFrame
            df = pd.read_pickle(file_path)

            # Do some data processing here...

            # Save the processed data to a new Pickle file
            df.to_pickle(file_path, index=False)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")
        st.session_state['file_uploaded'] = True
    return None