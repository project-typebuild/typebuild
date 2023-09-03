"""
GPT models have the ability to make function calls. 
This file helps with creating the dicts that could be passed
to GPT to make function calls.
"""
from glob import glob
import os
from helpers import extract_python_code
from llm_functions import get_llm_output
import streamlit as st
import prompts
import ast

def get_functions(file_path):
    """
    Returns a list of dictionaries, each containing information about a function defined in the given Python file.
    
    Parameters:
    -----------
    file_path: str
        The path to the Python file.
    
    Returns:
    --------
    A list of dictionaries, each containing the following keys:
        - name: the name of the function (string)
        - docstring: the docstring of the function (string)
        - args: a list of argument names (strings)
        - source: the source code of the function (string)
    """
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            docstring = ast.get_docstring(node) or ''
            args = [arg.arg for arg in node.args.args]
            source = ast.unparse(node)
            functions.append({'name': name, 'docstring': docstring, 'args': args, 'source': source})
    return functions

def create_function_dict(function):
    """
    Creates a function dict based on openai requirement.

    Args:
    - function (dict): A dictionary with the function name, arguments, types, descriptions, keyword arguments, docstrings, and return values.

    Returns:
    - function_dict (dict): A dictionary with the function name, arguments, and information on parameters.
    
    """
    # Show the source
    st.code(function['source'])
    func_info = {
        "name": function['name'],
        "description": function['docstring'],
    }
    messages = prompts.get_parameter_info(function['source'])
    if st.button("Get info"):
        res = get_llm_output(messages, model='gpt-4-0613')
        # Add to session state
        st.session_state['function_info'] = res
    if 'function_info' in st.session_state:
        function_info = st.session_state['function_info']
        p = extract_python_code(function_info)
        func_info = extract_parameters(p, func_info)    
        st.json(func_info)

def extract_parameters(p, func_info):
    if not p:
        return func_info
    else:
        # If p is a list of lists, get the first element
        if isinstance(p[0], list):
            p = p[0]
        params = {}
        required = []
        # Loop through the parameters and add to the function dict
        for i in p:
            the_type = i['type']
            if the_type == 'str':
                the_type = 'string'
            params[i['name']] = {
                "type": the_type,
                "description": i['description']
            }
            if i['required']:
                required.append(i['name'])
            
            if i['options']:
                params[i['name']]['enum'] = i['options']

        func_info['parameters'] = {"type": "object", "properties": params}
        func_info['required'] = required
    return func_info


def remove_function_info():
    """
    Removes the function info from the session state.
    Invoked when select a function is changed.
    """
    if 'function_info' in st.session_state:
        del st.session_state['function_info']
    return None

def main():
    """
    Main function to run the script.
    """
    # Get files from root folder and subfolders
    files = glob('**/*.py', recursive=True)
    # Select a file
    selected_file = st.selectbox('Select a file', files)
    # Get the functions
    functions = get_functions(selected_file)
    # Select a function
    selected_function = st.selectbox(
        'Select a function', 
        [f['name'] for f in functions],
        on_change=remove_function_info
        )
    # Get the function
    function = [f for f in functions if f['name'] == selected_function][0]
    # Display the function
    create_function_dict(function)
    return None
