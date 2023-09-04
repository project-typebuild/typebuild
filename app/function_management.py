"""
This file is used to manage functions and their descriptions:
- Writing or modifying functions in a file
- Importing functions and their descriptions and running them
"""

import streamlit as st
import altair as alt
import pandas as pd
import os
import re
import importlib.util
import importlib
import inspect
import datetime
from file_management import create_new_file_with_imports
from project_management import create_new_project, user_requirements_chat
import time
from blueprint_code import generate_code_from_user_requirements, modify_code

def import_functions(module_path, function_names):
    """
    Import functions from a module given the module path 
    and a list of function names.
    Note: Currently, only functions called main are invoked
    in each module, but we can pass more in the future.

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
    Create or modify functions for the selected view.
    When the function is ready it is run. 
    """
    #--------GET CODE FOR NEW AND EXISTING VIEWS--------
    # Add .py extension
    selected_file = st.session_state.file_path + '.py'

    # If the file does not exist, generate code for it
    if os.path.exists(selected_file):
        with st.expander('View and change instructions, if necessary'):
            modify_code()

    else:
        generate_code_from_user_requirements()

    #--------IF THERE IS A NEW RESPONSE, WRITE TO FILE--------    
    if 'response' in st.session_state:
        # Get the code
        code = st.session_state.code
        # Add the function to the file
        create_new_file_with_imports(code, file_path=selected_file)
        
        st.session_state.ss_num += 1
        # Set the menu to be the newly created file name without the .py extension
        _,file_name = os.path.split(selected_file)
        file_name = file_name.replace('.py', '')
        
        st.session_state[f"selected_file_{st.session_state.ss_num}"] = file_name
        # Remove the response from the session state
        del st.session_state.response
        st.experimental_rerun()

def run_code_in_view_file():
    """
    Runs the code in the selected view file.
    """
    selected_file = st.session_state.file_path + '.py'
    if os.path.exists(selected_file):    
        # Import the module
        my_functions = import_functions(selected_file, ['main'])
        if my_functions:
            try:
                # Run the main function
                my_functions['main']()
            except Exception as e:
                st.session_state.error = f"I ran into this error: {e}"    
    return None


def append_function_to_file(func_str, file_path):
    """
    Append the function to the file called user_functions.py
    Widget key names start with uc_ so that we can 
    distinguish them from other session state keys.  This is useful 
    in identifying all the active widgets.

    TODO: Add a decorator to the function to save and load state.
    
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

def get_function_description(func):
    """Retrieve the name, arguments, types, descriptions, keyword arguments, docstring, and return value of a given function.
    
    Args:
    - func (str): The function name to retrieve the information for.

    Returns:
    - name (str): The name of the function.
    - args (list): A list of positional arguments.
    - args_with_info (dict): A dictionary of positional arguments with their types and descriptions.
    - kwargs (list): A list of keyword arguments.
    - docstring (str): The docstring of the function.
    - return_name (str): The name of the return value.
    - return_type (str): The type of the return value.
    - return_description (str): The description of the return value.

    """
    name = func.__name__
    signature = inspect.signature(func)
    parameters = signature.parameters
    args = []
    args_with_info = {}
    kwargs = []
    
    # Regular expression pattern to match argument descriptions in docstring
    arg_pattern = re.compile(r'\s*([\w_]+)\s*\(([^)]+)\):\s*(.*)')
    
    # Extract argument descriptions from docstring
    docstring_lines = func.__doc__.strip().split('\n') if func.__doc__ else []
    arg_descriptions = {}
    for line in docstring_lines:
        match = arg_pattern.match(line)
        if match:
            arg_name = match.group(1)
            arg_description = match.group(3)
            arg_descriptions[arg_name] = arg_description
    
    for param_name, param in parameters.items():
        if param.default == inspect.Parameter.empty:
            args.append(param_name)
        else:
            kwargs.append(param_name)
            
        if param.annotation != inspect.Parameter.empty:
            arg_type = param.annotation
            if 'str' in str(arg_type):
                arg_type = 'string'
            arg_info = {"type": arg_type}
            if param_name in arg_descriptions:
                arg_info["description"] = arg_descriptions[param_name]
            args_with_info[param_name] = arg_info
        
    return_name = None
    return_type = None
    return_description = None
    
    if func.__annotations__.get('return'):
        return_type = func.__annotations__['return']
        return_description = func.__doc__.partition('Returns: ')[2].partition('\n\n')[0].strip() if 'Returns: ' in func.__doc__ else None
        return_name = "return"
    
    return name, args, args_with_info, kwargs, func.__doc__, return_name, return_type, return_description

# Get all functions from a file using inspect

def get_all_function_descriptions(module_name,file_path):

    """
    Get all functions from a file using inspect.

    Args:
    - file_path (str): The path to the file to get the functions from.

    Returns:
    - all_functions (list): A list of dictionaries with the function names, arguments, types, descriptions, keyword arguments, docstrings, and return values.

    """
    # Get all functions from a file
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    all_functions = []
    for name, data in inspect.getmembers(module, inspect.isfunction):
        my_function = getattr(module, name)
        if name != 'main':
            # Get the function description
            name, args, args_with_info, kwargs, docstring, return_name, return_type, return_description = get_function_description(my_function)
            # Add to the list
            all_functions.append({'function_name': name,
            'mandatory_args': args,
            'args_with_info': args_with_info,
            'optional_args': kwargs,
            'function_docstring': docstring,
            'return_name': return_name,
            'return_type': return_type,
            'return_description': return_description
            })
    return all_functions