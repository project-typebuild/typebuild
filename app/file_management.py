"""
Deals with file operations such as creating, updating, deleting
loading, and saving files.  It does not do data operations,
llm related stuff, or streamlit related stuff.
"""
import os
import streamlit as st
import pandas as pd
import time
from glob import glob

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

def create_new_file_with_imports(func_str, file_path):
    """
    Create a new file with the given string
    """
    # Add the key imports
    import_statement = "import streamlit as st\nimport pandas as pd\nimport os\nfrom glob import glob\nimport altair as alt\n\n"
    func_str = import_statement + func_str

    # Comment out lines that call the "main" function
    func_lines = func_str.split('\n')
    for i, line in enumerate(func_lines):
        if 'main(' in line:
            func_lines[i] = '# ' + line

    # Join the modified lines back into a string
    func_str = '\n'.join(func_lines)

    # Add .py if not already there
    if not file_path.endswith('.py'):
        file_path += '.py'
    with open(file_path, 'w') as f:
        f.write(func_str)
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



def get_views():
    """
    TODO: Check that we are not using it and delete this function.
    """
    project_folder = st.session_state.project_folder
    # Get all the python files in the project folder
    files = glob(f'{project_folder}/*.py')

    # Ignore files that start with __
    files = [i for i in files if not i.startswith('__')]
    # Ignore files that end with main.py
    files = [i for i in files if not i.endswith('main.py')]
    
    # Remove the .py extension
    files = [i.replace('.py', '') for i in files]

    # ignore pycache
    files = [i for i in files if not 'pycache' in i]


