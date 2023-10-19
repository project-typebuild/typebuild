import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
import simple_auth
import streamlit as st
from menu import reset_menu
# Make it full width
st.set_page_config(layout="wide", page_title='TypeBuild')
token = simple_auth.simple_auth()
st.session_state.token = token

import session_state_management

from helpers import starter_code, set_or_get_openai_api_key, config_project 

# Starter code has to run early.  Do not move.
starter_code()

from home_page import home_page
from project_management import get_project_file_folder, manage_project, ideate_project
from function_management import create_run_menu, run_code_in_view_file
from function_calling_spec_maker import main as fcsm
from requirements_with_chat import technical_requirements_chat
from blueprint_code import select_view
from func_research_with_llm import research_with_llm

from plugins.create_content_with_llms import analyze_with_llm
# Set the user type to developer for now.
user_type = 'developer'
st.session_state.user_type = user_type

# If new menu is toggle_developer_options, toggle the developer options
if st.session_state.new_menu == 'toggle_developer_options':
    st.session_state.show_developer_options = not st.session_state.show_developer_options
    reset_menu()

# If new menu is toggle_function_calling_mode, toggle the function calling mode
if st.session_state.new_menu == 'toggle_function_calling_mode':
    st.session_state.function_call = not st.session_state.function_call
    reset_menu()

# If developer options are enabled, show the developer options
if st.session_state.show_developer_options:
    # Display function call type
    st.sidebar.info(f"Function call is allowed: {st.session_state.function_call}")
    st.session_state.show_developer_options = True

if st.session_state.show_developer_options:
    if st.sidebar.checkbox('Show session state'):
        st.write(st.session_state)
    if st.sidebar.checkbox('Function call maker'):
        fcsm()
        st.warning("Turn off function call maker to view the app.")
        st.stop()
    if 'last_request' in st.session_state:
        if st.sidebar.checkbox("Show latest request"):
            with st.expander("Latest request"):
                st.write(st.session_state.last_request)
            if 'last_response' in st.session_state:
                with st.expander("Latest response"):
                    st.write(st.session_state.last_response)    
            if 'last_function_call' in st.session_state:
                with st.expander("Last Function call"):
                    st.write(st.session_state.last_function_call)
        # Separator line
        st.sidebar.markdown("---")
        st.stop()

# Check if openai key exists in the secrets file or custom_llm.py exists in the .typebuild folder, if not, then run the config_project function
api_key = set_or_get_openai_api_key()
if st.session_state.new_menu == 'Home':
    home_page()
    st.stop()

if api_key == '' and not os.path.exists(os.path.join(st.session_state.typebuild_root, 'custom_llm.py')):
    st.session_state.new_menu = 'llm_access'
if st.session_state.new_menu == 'llm_access':
    config_project()
    # st.error("Please add your OpenAI key or upload a custom LLM to continue.")
    st.stop()
    
# Get the project file and data
get_project_file_folder()

# If the option is ideate
if st.session_state.new_menu == 'ideate':
    ideate_project()
    st.stop()

# Get selected project in title case
selected_project = st.session_state.selected_project.replace('_', ' ').upper() + " PROJECT"
st.sidebar.header(f"{selected_project}", divider='rainbow')

# Manage project option will show up
# if user needs to set things up or if user selects it.
manage_project()


if st.session_state.new_menu == 'llm_analysis':
    analyze_with_llm()
    st.stop()

if st.session_state.new_menu == 'research':
    research_with_llm()

# If menu is apps_analysis, show the apps analysis
if st.session_state.new_menu == 'apps_analysis':
    # Select the view from the menu
    select_view()
    # if 'data_description' in st.session_state:
    #     st.write(st.session_state.data_description)
    run_code_in_view_file()
    technical_requirements_chat(widget_label='Test requirement')

