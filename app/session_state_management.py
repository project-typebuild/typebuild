import streamlit as st

def add_default_session_states():
    # Add a dict with session state variables
    ss_vars = {
        'messages': [],
        }

    for key in ss_vars:
        if key not in st.session_state:
            st.session_state[key] = ss_vars[key]
    return None

def change_project():
    """
    When the project is changed, clear the session state
    of key variables.
    """
    if 'text_list' in st.session_state:
        del st.session_state['text_list']
    if 'project_file' in st.session_state:
        del st.session_state['project_file']
    if 'project_folder' in st.session_state:
        del st.session_state['project_folder']
    return None

def change_view():
    """
    When the view is changed, clear the session state
    of key variables.
    """
    key_vars = ['code', 'response', 'user_requirements', 'messages']
    for key in key_vars:
        if key in st.session_state:
            del st.session_state[key]
    return None

def main():
    add_default_session_states()
    return None