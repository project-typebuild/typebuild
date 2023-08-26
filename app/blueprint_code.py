"""
Blueprints consist of text and code.  
This file deals with all aspects of code including:

- Generating code from user requirements text
- Modifying code based on requested changes
- Maintaining relationship between code and blueprint text (so that if one is updated, we will know to update the other)
- etc.

blueprint_text.py only deals with creating, editing, and deleting text.  It does not deal with code.
"""

import os
import time
import pandas as pd
from blueprint_text import user_requirement_for_view
import streamlit as st
from prompts import get_prompt_to_code, get_prompt_to_modify
from llm_functions import get_llm_output, parse_code_from_response, parse_modified_user_requirements_from_response
from project_management import file_upload_and_save, get_project_df
from glob import glob
import session_state_management
session_state_management.main()

import openai
openai.api_key = st.secrets.openai.key 

# Create a menu to run the app
# create_run_menu()

def generate_code_from_user_requirements(df=None, mod_requirements=None, current_code=None, confirmed=False):

    """
    The function that generates code from user requirements. 

    Args:
    - df: A pandas dataframe with sample data (optional, default None)

    Returns:
    - None

    """


    # Define the prompt
    st.header("Your requirements")
    user_requirements = user_requirement_for_view()
    if st.button("Generate code"):
        get_code(df=df, user_requirements=user_requirements, mod_requirements=mod_requirements, current_code=current_code)
        st.experimental_rerun()
    return None

def get_code(df=None, user_requirements="", mod_requirements=None, current_code=None):

    messages = get_prompt_to_code(
        user_requirements, 
        df=df,
        mod_requirements=mod_requirements,
        current_code=current_code,
        )
    with st.spinner('Generating code...'):
        response = get_llm_output(messages)
    
    st.session_state.response = response
    st.session_state.user_requirements = user_requirements
    st.session_state.messages = messages
    st.session_state.code = '\n\n'.join(parse_code_from_response(response))
    
    return None

def modify_code():
    """
    The function that modifies code based on user requirements.

    Args:
    - user_requirements: initial user requirements. 
    - all_function_descriptions: descriptions of all the functions available
    - df: A pandas dataframe with sample data (optional, default None)

    Returns:
    - None

    """

    # Get the current code from the current file
    file = st.session_state.file_path + '.py'
    with open(file, 'r') as f:
        current_code = f.read()
    # Define the prompt
    st.header("Modify requirements")
    user_requirements = user_requirement_for_view()
    st.info("If requirements are correct but the output is not as expected, tell us what changes you want to make to the function.")
    change_requested = st.text_area("What changes do you want to make to the function?")
    if st.button("Modify"):
        get_code(df=st.session_state.df, mod_requirements=change_requested, current_code=current_code)
    return None

def modify_code_old(user_requirements, all_function_descriptions,df=None):

    """
    The function that modifies code based on user requirements.

    Args:
    - user_requirements: initial user requirements. 
    - all_function_descriptions: descriptions of all the functions available
    - df: A pandas dataframe with sample data (optional, default None)

    Returns:
    - None

    """

    if st.sidebar.checkbox('Modify function', key=f'modify_checkbox_{st.session_state.ss_num}'):
        
        change_requested = st.sidebar.text_area("What changes do you want to make to the function?")
        if st.sidebar.button("Make the change"):
            messages_modify = get_prompt_to_modify(change_requested=change_requested, user_requirements=user_requirements, df=df, all_function_descriptions=all_function_descriptions)
            st.session_state.messages_modify = messages_modify
            response = get_llm_output(messages_modify)
            st.session_state.response = response
            modified_code = '\n\n'.join(parse_code_from_response(response))
            modified_user_requirements = parse_modified_user_requirements_from_response(response)[0]
            st.session_state.modified_code = modified_code
            st.session_state.modified_user_requirements = modified_user_requirements
            st.session_state.change_requested = change_requested

    if 'modified_code' in st.session_state:
        st.info('Modified code')
        st.code(st.session_state.modified_code, language='python')