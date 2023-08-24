import os
import streamlit as st
from session_state_management import change_project

def create_empty_if_not_exists(file_name):
    """
    Creates an empty file if it does not exist. If the folder containing the file does not exist, it creates the folder as well.
    
    Args:
    - file_name (str): The name of the file to create with full relative path 
    
    Returns:
    - None
    """
    folder_name = os.path.dirname(file_name)
    if not os.path.exists(folder_name):
        # Create the folder
        os.makedirs(folder_name, exist_ok=True)
    if not os.path.exists(file_name):
        # Crate an empty file
        with open(file_name, 'w') as f:
            f.write('')
    return None

def get_file_contents(file_name):
    '''
    Get the contents of a file as a string.
    Create empty file if not exists.
    '''
    create_empty_if_not_exists(file_name)
    with open(file_name, 'r') as f:
        return f.read()


def write_file_contents(file_name, contents):
    '''
    Write the contents of a file as a string.
    Create empty file if not exists.
    '''
    create_empty_if_not_exists(file_name)
    # Create folder if it does not exist
    folder_name = os.path.dirname(file_name)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    with open(file_name, 'w') as f:
        f.write(contents)
    return None

def create_main_file_if_not_exists(project_main_file):
    """
    If a project subfolder does not have a main.py file, create it.
    Also, check if the folder has __init__.py
    """
    if not os.path.exists(project_main_file):
        # Create the file with basic tech stack.
        # Do not multi-line this, it will cause indentation error
        import_statement = "import streamlit as st\nimport pandas as pd\nimport os\nfrom glob import glob\nimport altair as alt\n\n"
        with open(project_main_file, 'w') as f:
            f.write(import_statement)
    # Check if the folder has __init__.py
    init_file = os.path.join(os.path.dirname(project_main_file), '__init__.py')
    if not os.path.exists(init_file):
        # Create the file
        with open(init_file, 'w') as f:
            f.write('')
    return None


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
    project_names = [i for i in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, i))]
    # Ignore pycache
    project_names = [i for i in project_names if not 'pycache' in i]
    
    # Make the first project the default
    if len(project_names) > 0:
        default_index = 0
        selected_project = st.sidebar.selectbox(
            "Select project", 
            project_names, 
            index=default_index,
            key='selected_project',
            on_change=change_project
            )
        project_folder = os.path.join(user_folder, selected_project)
    else:
        project_folder = ''

    # Save to session state
    st.session_state.project_folder = project_folder

    # Get the project file path
    project_main_file = os.path.join(project_folder, 'main.py')
    # Create the file if it does not exist
    create_main_file_if_not_exists(project_main_file)
    # Save to session state
    st.session_state.project_main_file = project_main_file

    return None

def create_new_project():
    """
    Creates a new project folder, main.py file, and __init__.py file.
    TODO: Need to call this somewhere.
    """
    # Get the project name
    project_name = st.text_input("Enter the project name")
    if project_name == '':
        st.write('Enter a project name')
        return None
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
    
    # Create the main.py file
    project_main_file = os.path.join(project_folder, 'main.py')
    create_main_file_if_not_exists(project_main_file)
    
    # Create the __init__.py file
    init_file = os.path.join(project_folder, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
    # Save to session state
    st.session_state.project_folder = project_folder
    st.session_state.project_main_file = project_main_file
    return None

