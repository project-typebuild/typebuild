from blueprint_code import select_view
import simple_auth
import streamlit as st
# Make it full width
st.set_page_config(layout="wide")
token = simple_auth.simple_auth()
st.session_state.token = token

import session_state_management

session_state_management.main()

from project_management import get_project_file_folder, get_project_df
from function_management import create_run_menu, run_code_in_view_file
from function_calling_spec_maker import main as fcsm
from requirements_with_chat import technical_requirements_chat
from plugins.create_content_with_llms import add_data_with_llm

if st.session_state.token == 'admin':
    if st.sidebar.checkbox('Show session state'):
        st.write(st.session_state)
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
            st.stop()

# Get the project file and data
get_project_file_folder()


if st.sidebar.checkbox('Function call maker'):
    fcsm()
    st.warning("Turn off function call maker to view the app.")
    st.stop()

add_or_view = st.sidebar.radio(
    "Add or view data", 
    ['Add data', 'View data'],
    # captions= ['Add data with llms', 'Extract insights from data']
    )
if add_or_view == 'Add data':
    add_data_with_llm()
    st.stop()

function_calling_availability = st.sidebar.radio("Function Call type", ['---','auto', 'manual'], key='function_calling_availability')
if function_calling_availability == '---':
    st.stop()
if add_or_view == 'View data':
    # Select the view from the menu
    select_view()
    run_code_in_view_file()
    technical_requirements_chat(widget_label='Test requirement')

