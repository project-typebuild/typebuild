import streamlit as st

def settings_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    settings_menu_items = [
        ["HOME", "Projects", "projects"],
        ["HOME", "Settings", "settings"],
        ["Settings", "LLM Access", "llm_access"],

    ]
    
    menu.add_edges(settings_menu_items, 'tb_settings')

def settings():
    st.title("Settings")
    st.info("This is the settings page")
    return None

def projects():
    st.title("Projects")
    st.info("This is the projects page")
    return None

def llm_access():
    st.title("LLM Access")
    st.info("This is the LLM Access page")
    return None