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

from chat import chat
from graphical_menu import GraphicalMenu
from tb_settings import settings_main
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
if 'last_request' in st.session_state:
    show_request = st.sidebar.checkbox('Show latest request')
    if show_request:
        st.write(st.session_state.last_request)
if 'last_response' in st.session_state:
    show_response = st.sidebar.checkbox('Show latest response')
    if show_response:
        res = st.session_state.last_response
        st.warning(st.session_state.last_response)

# If there is a message from the agent, show it (temporary)
if 'agent_messages' in st.session_state:
    if st.sidebar.checkbox('Show agent messages'):
        st.success(st.session_state.agent_messages)

# test_main()


# menu options down below are a list of lists, 
# the first element of which is the parent node, the second element is the node name, 
# the third element is the function name, and the fourth element is the module name (python file name)
menu_bar_options = [
    ['HOME', 'Search', 'search_placeholder', 'helpers'], # search_placeholder is a placeholder function because when Search is clicked, it should not do anything and should just show the children of Search
    ['Search', 'Google Search', 'google_search_interface_for_menu', 'helpers'],
    ['Search', 'YouTube Search', 'youtube_search_interface_for_menu', 'helpers'],
    ['HOME','Data','search_placeholder','helpers'],
    ['Data','Upload Data','data_management_interface','helpers'],
    ['HOME', 'Nodes', 'show_node_properties', 'graphical_menu'],
    ]

menu.add_edges(menu_bar_options) # add the edges to the menu in the GraphicalMenu class
menu.create_menu() # create the meu bar
run_current_functions() # run the current functions in the session state


chat() # chat interface

# Naviagate through the menu using the chat interface

from tools.navigator import get_available_destinations
nodes = get_available_destinations()
# st.json(f'{nodes}')

st.sidebar.write(f'Active Step: {st.session_state.activeStep}')