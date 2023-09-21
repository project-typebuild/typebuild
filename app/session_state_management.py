import streamlit as st

def add_default_session_states():
    # Add a dict with session state variables
    ss_vars = {
        'messages': [],
        'ss_num': 0,
        'menu_id': 0,
        'new_menu': 'Home',
        'show_developer_options': False,
        }

    for key in ss_vars:
        if key not in st.session_state:
            st.session_state[key] = ss_vars[key]
    return None

def change_view():
    """
    When the view is changed, clear the session state
    of key variables.
    """
    # Increment view number so that the widget selection changes
    # Clear the session state of key variables
    key_vars = ['code', 'code_str', 'response', 
                'user_requirements', 'messages', 'data_description',
                'error'
                ]
    for key in key_vars:
        if key in st.session_state:
            del st.session_state[key]

    return None

def change_ss_for_project_change():
    """
    When the project is changed, clear the session state
    of key variables that affect a project.
    """
    change_view()
    additional_vars = ['df', 'project_file', 'project_folder', 'column_info']
    for key in additional_vars:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.project_description_chat = []
    return None


def main():
    add_default_session_states()
    return None