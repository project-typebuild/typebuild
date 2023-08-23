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

def main():
    add_default_session_states()
    return None