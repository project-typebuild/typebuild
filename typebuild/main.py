import sys
import simple_auth
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
import streamlit as st
import yaml
from tools.google_search import GoogleSearchSaver
# import tools

# Make it full width
st.set_page_config(layout="wide", page_title='TB Chat Framework')
token = simple_auth.simple_auth()

st.session_state.token = token

from helpers import starter_code, set_or_get_llm_keys, config_project 
# Starter code has to run early.  Do not move.
starter_code()

from test import test_main
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

if 'agent_messages' in st.session_state:
    if st.sidebar.checkbox('Show agent messages'):
        st.success(st.session_state.agent_messages)

test_main()

# TODO: THIS CREATES TWO SEARCH MENUS.  FIX IT.

google_menu = [
    ['HOME', 'Search', 'empty_func', 'test'],
    ['Search', 'Google Search', 'google_search_interface', 'test'],
    ['Search', 'YouTube Search', 'search_youtube', 'test'],
    ]

menu.add_edges(google_menu)
menu.create_menu()
run_current_functions()
