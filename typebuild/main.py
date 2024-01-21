import sys
import simple_auth
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

import streamlit as st
import yaml

# Make it full width
st.set_page_config(layout="wide", page_title='TB Chat Framework')
token = simple_auth.simple_auth()
st.session_state.token = token

from helpers import starter_code
# Starter code has to run early.  Do not move.
starter_code()

# from chat import chat
from chat_with_planning import chat
from graphical_menu import GraphicalMenu
from tb_settings import settings_main, llm_access_settings
from function_management import run_current_functions

if 'menu' not in st.session_state:
    menu = GraphicalMenu()
    st.session_state['menu'] = menu
    settings_main()
    st.rerun()
else:
    menu = st.session_state['menu']
    settings_main()

# If latest request or response are there, show checkbox to show them
please_stop = False
with st.sidebar.expander("Admin"):
    st.checkbox("Show developer options", key='show_developer_options')
    
    if 'last_request' in st.session_state:
        show_request = st.checkbox('Show latest request')
        if show_request:
            please_stop = True
            st.write(st.session_state.last_request)
        show_all_messages = st.checkbox('Show all messages')
        if show_all_messages:
            please_stop = True
            st.write(st.session_state.all_messages)
    if 'last_response' in st.session_state:
        show_response = st.checkbox('Show latest response')
        if show_response:
            please_stop = True
            res = st.session_state.last_response
            st.warning(st.session_state.last_response)
    if 'planner_instructions' in st.session_state:
        show_planner_instructions = st.checkbox('Show planner instructions')
        if show_planner_instructions:
            please_stop = True
            st.write(st.session_state.planner_instructions)
    # If there is a message from the agent, show it (temporary)
    if 'agent_messages' in st.session_state:
        if st.checkbox('Show agent messages'):
            please_stop = True
            st.success(st.session_state.agent_messages)
if please_stop:
    st.stop()
# test_main()


# menu options down below are a list of lists, 
# the first element of which is the parent node, the second element is the node name, 
# the third element is the function name, and the fourth element is the module name (python file name)
menu_bar_options = [
    ['HOME', 'Search', 'search_placeholder', 'helpers'], # search_placeholder is a placeholder function because when Search is clicked, it should not do anything and should just show the children of Search
    ['Search', 'Google Search', 'google_search_interface_for_menu', 'helpers'],
    ['Search', 'YouTube Search', 'youtube_search_interface_for_menu', 'helpers'],
    ['Search', 'Arxiv Search', 'arxiv_search_interface_for_menu', 'helpers'],
    ['HOME','Data','search_placeholder','helpers'],
    ['Data','Upload Data','data_management_interface','helpers'],
    ['Data','Upload Documents','data_management_interface','helpers'],
    # ['Data', 'Select Data', 'data_management_interface', 'helpers'],
    ['Data','Delete Data','data_management_interface','helpers'],
    ['Data', 'Data Model', 'data_management_interface', 'helpers'],
    ['HOME', 'Nodes', 'show_node_properties', 'graphical_menu'],
    ['HOME','LLM Research','llm_research_interface','helpers'],
    ]

if not 'openai_key' in st.session_state:
    llm_access_settings() # LLM access settings

menu.add_edges(menu_bar_options) # add the edges to the menu in the GraphicalMenu class
menu.create_menu() # create the meu bar
run_current_functions() # run the current functions in the session state
# st.sidebar.warning(st.session_state.selected_node)

chat() # chat interface

# Naviagate through the menu using the chat interface
# TODO: Ranu, even though we are not adding anything to sesssion state
# or doing anything with the return value, we still need to call this
# for some reason.  Without it, chat is not opening menus. 
from tools.navigator import get_available_destinations
nodes = get_available_destinations()
# st.json(f'{nodes}')

