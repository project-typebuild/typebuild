import os
import streamlit as st

def add_default_session_states():
    # Add a dict with session state variables
    ss_vars = {
        'messages': [],
        'ss_num': 0,
        'menu_id': 0,
        'show_developer_options': False,
        'ask_llm': False,
        'current_task': 'orchestration',
        'current_chat': None,
        'call_status': None,
        'dir_path': os.path.dirname(os.path.realpath(__file__)),
        'home_dir' : os.path.expanduser("~"),
        'typebuild_root' : os.path.join(os.path.expanduser("~"), '.typebuild'),
        'user_folder': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token),
        'project_folder': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token),
        'data_folder': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token, 'data'),
        'secrets_file_path' : os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token, 'secrets.toml'),
        'profile_dict_path': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', 'admin', 'profile_dict.pk'),
        'should_rerun': False,
        'selected_node': 'HOME',
        'all_messages': [],
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
                'error', 'message_to_agent',
                'last_function_call',
                ]
    for key in key_vars:
        if key in st.session_state:
            del st.session_state[key]

    # Set ask llm as false
    st.session_state.ask_llm = False
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
    # load_header_states()
    add_default_session_states()
    return None