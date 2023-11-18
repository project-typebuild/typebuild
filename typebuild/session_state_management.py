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
        'ask_agent': 'agent_manager',
        'current_chat': None,
        'call_status': None,
        'dir_path': os.path.dirname(os.path.realpath(__file__)),
        'home_dir' : os.path.expanduser("~"),
        'typebuild_root' : os.path.join(os.path.expanduser("~"), '.typebuild'),
        'user_folder': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token),
        'project_folder': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token),
        'secrets_file_path' : os.path.join(os.path.expanduser("~"), '.typebuild', 'users', st.session_state.token, 'secrets.toml'),
        'profile_dict_path': os.path.join(os.path.expanduser("~"), '.typebuild', 'users', 'admin', 'profile_dict.pk'),
        'should_rerun': False,
        'selected_node': 'HOME',
        }

    for key in ss_vars:
        if key not in st.session_state:
            st.session_state[key] = ss_vars[key]
    return None


def main():
    # load_header_states()
    add_default_session_states()
    return None