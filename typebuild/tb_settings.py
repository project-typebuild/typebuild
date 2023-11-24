import streamlit as st
from project_management.project_management import ProjectManagement
from llm_access import LLMConfigurator

def settings_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    settings_menu_items = [
        ["HOME", "Projects", "projects","tb_settings"],
        ["HOME", "Settings", "settings","tb_settings"],
        ["Settings", "LLM Access", "llm_access_settings","tb_settings"],
    ]
    
    menu.add_edges(settings_menu_items)

def settings():
    st.title("Settings")
    st.info("This is the settings page")
    return None

def projects():
    """
    Activities in TypeBuild are housed under projects.  This function opens a UI 
    that allows users to create new projects and select existing projects.
    Once a project is selected, the user can manage data, create apps, and use LLMs.
    """
    st.title("Projects")
    if 'project_manager' not in st.session_state:
        st.session_state.project_manager = ProjectManagement(st.session_state.user_folder)
    pm = st.session_state.project_manager
    pm.manage_project()
    
    return None

def llm_access_settings():
    st.title("LLM Access")
    if 'llm_configurator' not in st.session_state:
        st.session_state.llm_configurator = LLMConfigurator()
    lc = st.session_state.llm_configurator
    lc.config_project()
    return None