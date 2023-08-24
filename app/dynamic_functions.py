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

def create_run_menu(dir):
    """
    The given directory should contain a set of modules.
    Create a selectbox based on the file names in the directory.
    When a file is selected, import the module and run the main function.
    """
    # Get the file names from the directory
    file_names = os.listdir(dir)

    # Create a selectbox to select the file
    selected_file = st.sidebar.selectbox('Menu', file_names)

    # Create a path to the selected file
    file_path = os.path.join(dir, selected_file)

    # Import the module
    my_functions = import_functions(file_path, ['main'])
    if my_functions:
        # Run the main function
        my_functions['main']()


    return None