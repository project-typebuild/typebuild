import os
import time
import pandas as pd
import streamlit as st
from prompts import get_prompt_to_code, get_prompt_to_modify
from llm_functions import get_llm_output
from parse_llm_response import parse_code_from_response, parse_modified_user_requirements_from_response
from file_management import file_upload_and_save
from glob import glob
import session_state_management
session_state_management.main()

import openai
openai.api_key = st.secrets.openai.key 

# Create a menu to run the app
# create_run_menu()


def generate_code_from_user_requirements(df=None):

    """
    The function takes in a list of user requirements and generates code to meet those requirements.

    """

    if st.sidebar.checkbox('Upload a CSV file'):
        file_upload_and_save()
        st.stop()


    # Define the prompt
    user_requirements = st.text_area("What are your requirements for the project?", value = st.session_state.user_requirements if 'user_requirements' in st.session_state else '')

    # Convert the user requirements to a list with bullet points
    user_requirements = ['- ' + line.strip() for line in user_requirements.split('\n') if line.strip()]

    # Join the list items into a single string
    user_requirements = '\n'.join(user_requirements)


    messages = get_prompt_to_code(user_requirements, df=df)

    if st.button("Go GPT!"):
        response = get_llm_output(messages)
        code = parse_code_from_response(response)[0]
        
        st.session_state.response = response
        st.session_state.user_requirements = user_requirements
        st.session_state.messages = messages
        st.session_state.code = '\n\n'.join(parse_code_from_response(response))
    
    return None

def modify_code(df=None):
    if st.sidebar.checkbox('Modify function', key='modify checkbox'):
        change_requested = st.text_area("What changes do you want to make to the function?")
        if change_requested:
            messages_modify = get_prompt_to_modify(change_requested=change_requested, user_requirements=user_requirements, df=df, all_function_descriptions=all_function_descriptions)
            st.session_state.messages_modify = messages_modify
         
            all_function_descriptions = [{'function_name': 'authenticate_user',
            'mandatory_args': [],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    Function to authenticate the user using a token.\n    '},
            {'function_name': 'display_data',
            'mandatory_args': ['df', 'state', 'district', 'block'],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    Function to display the data for the selected location.\n\n    Args:\n    df: pandas DataFrame containing the data\n    state: Selected state\n    district: Selected district\n    block: Selected block\n    '},
            {'function_name': 'load_data',
            'mandatory_args': [],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': None},
            {'function_name': 'plot_data',
            'mandatory_args': ['df', 'state', 'district', 'block'],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    Function to plot the data for the selected location.\n\n    Args:\n    df: pandas DataFrame containing the data\n    state: Selected state\n    district: Selected district\n    block: Selected block\n    '},
            {'function_name': 'select_location',
            'mandatory_args': ['df'],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    Function to select the location for which to view the data.\n\n    Args:\n    df: pandas DataFrame containing the data\n\n    Returns:\n    selected_state, selected_district, selected_block: Selected state, district, and block\n    '},
            {'function_name': 'set_page_title',
            'mandatory_args': [],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    Function to set the title of the Streamlit app.\n    '},
            {'function_name': 'set_preferences',
            'mandatory_args': [],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    Function to set the user preferences for language and view.\n    '},
            {'function_name': 'simple_auth',
            'mandatory_args': [],
            'args_with_info': {},
            'optional_args': [],
            'function_docstring': '\n    This tries to authenticate first with session state variable,\n    next with a cookie and if both fails, it asks for the user to login. \n\n    It also creates a logout button.\n    '}]

        # if st.button("GO MODIFY", key='modify button'):
            response = get_llm_output(messages_modify)
            st.session_state.response = response
            modified_code = parse_code_from_response(response)[0]
            modified_user_requirements = parse_modified_user_requirements_from_response(response)[0]
            st.session_state.modified_code = modified_code
            st.session_state.modified_user_requirements = modified_user_requirements
            st.session_state.change_requested = change_requested


    

# There should be a modify checkbox for every page
# Add create new view in the menu
# Add 
