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


def generate_code_from_user_requirements(df=None):

    """
    The function that generates code from user requirements. 

    Args:
    - df: A pandas dataframe with sample data (optional, default None)

    Returns:
    - None

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
    if st.checkbox("Show request"):
        st.json(messages)

    if st.button("Get code"):
        response = get_llm_output(messages)
        code = parse_code_from_response(response)[0]
        
        st.session_state.response = response
        st.session_state.user_requirements = user_requirements
        st.session_state.messages = messages
        st.session_state.code = '\n\n'.join(parse_code_from_response(response))
    
    return None

def modify_code(user_requirements, all_function_descriptions,df=None):

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
        st.warning('Please request a change to the app by typing in the box below.')
        change_requested = st.chat_input("What changes do you want to make to the function?")
        if change_requested:
            messages_modify = get_prompt_to_modify(change_requested=change_requested, user_requirements=user_requirements, df=df, all_function_descriptions=all_function_descriptions)
            st.session_state.messages_modify = messages_modify
            response = get_llm_output(messages_modify)
            st.session_state.response = response
            modified_code = '\n\n'.join(parse_code_from_response(response))
            modified_user_requirements = parse_modified_user_requirements_from_response(response)[0]
            st.session_state.modified_code = modified_code
            st.session_state.modified_user_requirements = modified_user_requirements
            st.session_state.change_requested = change_requested


    

# There should be a modify checkbox for every page
# Add create new view in the menu
# Add 
