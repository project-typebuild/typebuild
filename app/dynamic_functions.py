"""
Creates a menu of functions available in the module
and runs the selected function
"""
import streamlit as st
import altair as alt
import pandas as pd
import os
import re
import importlib.util
import inspect
import datetime
from file_management import create_new_project, create_new_view
import time
from blueprint import generate_code_from_user_requirements

def import_functions(module_path, function_names):
    """
    Import functions from a module given the module path and a list of function names.

    Parameters:
    module_path (str): The path to the module to import.
    function_names (list): A list of function names to import.

    Returns:
    dict: A dictionary of imported functions, where the keys are the function names and the values are the function objects.
    """
    # Load the module from the file path
    spec = importlib.util.spec_from_file_location("module_name", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Create a dictionary of imported functions
    imported_functions = {}
    for function_name in function_names:
        # Check if the module has the function
        if hasattr(module, function_name):
            # Add the function to the dictionary
            imported_functions[function_name] = getattr(module, function_name)

    return imported_functions

def create_run_menu():
    """
    The given directory should contain a set of modules.
    Create a selectbox based on the file names in the directory.
    When a file is selected, import the module and run the main function.
    """
    # Get the file names from the directory
    dir = st.session_state.project_folder

    file_names = os.listdir(dir)
    
    # Ignore files that start with __
    file_names = [i for i in file_names if not i.startswith('__')]

    # Read only files that end with .py
    file_names = [i for i in file_names if i.endswith('.py')]

    # Remove the .py extension
    file_names = [i.replace('.py', '') for i in file_names]

    file_names.append('Create new view')

    # Create a selectbox to select the file
    selected_file = st.sidebar.selectbox('Menu', file_names)

    if selected_file == 'Create new view':
        create_new_view()

    else:
        # Add .py extension
        selected_file = selected_file + '.py'

        # Create a path to the selected file
        file_path = os.path.join(dir, selected_file)
        
        # Check if the python file is empty. read the file and check if it is empty

        with open(file_path, 'r') as f:
            file_content = f.read()
        if len(file_content.split()) == 0:
            generate_code_from_user_requirements()
            code = st.session_state.code
            # Add the function to the file
            append_function_to_file(code, file_path=file_path)
            st.stop()

        else:
            # Import the module
            my_functions = import_functions(file_path, ['main'])
            if my_functions:
                # Run the main function
                my_functions['main']()


    return None



def append_function_to_file(func_str, file_path):
    """
    Append the function to the file called user_functions.py
    """
    # Add necessary decorator to the function
    # decorator = "@run_before_and_after(load_state, save_state)\n"
    decorator = '\n'
    # Remove import statements
    func_str = '\n'.join([line for line in func_str.split('\n') if not line.startswith('import')]).strip()

    # Add the decorator above the first function
    func_str = func_str.replace('def', decorator + 'def', 1)
    
    # All key names should start with uc_
    func_str = func_str.replace('key="', 'key="uc_')
    # Do the same for keys starting with single quotes
    func_str = func_str.replace("key='", "key='uc_")
    # Take care of f strings
    func_str = func_str.replace('key=f"', 'key=f"uc_')
    func_str = func_str.replace("key=f'", "key=f'uc_")

    # Add the function to the file
    with open(file_path, 'a') as f:
        # Add empty lines before
        f.write('\n\n')
        # Add decorator
        # f.write(f'{decorator}\n')
        # Add lines before and after the function
        f.write(func_str)
    return None


def replace_function_in_place(current_file, func_name, new_func):
    """
    current_file is the entire content of a python file.  In this,
    there is a function with a specific name that we are trying to replace.
    Given the full code for the new function, this will remove the old function
    and replace it with the new one.

    """
    
    # Replace from def func_name to the next def or end of file
    # Get the index of the function name
    start = current_file.find(f'def {func_name}')

    if start == -1:
        # The function doesn't exist
        return current_file + "\n\n" + new_func
    else:
        # Get the index of the next def
        end = current_file.find('def ', start+1)
        # If end is -1, then we are at the end of the file
        if end == -1:
            end = len(current_file)
        # Replace the function
        new_file = current_file[:start] + "\n\n" + new_func + "\n\n" + current_file[end:]
    return new_file
