import sys
import simple_auth
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
import streamlit as st
import yaml
from tools.google_search import GoogleSearchSaver

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
test_main()

# TODO: THIS CREATES TWO SEARCH MENUS.  FIX IT.

google_menu = [
    # ['HOME', 'Search', 'google_search_interface', 'tools.google_search'],
    # ['HOME', 'Search', 'main', 'tools.yt_search'],
    ['HOME', "Search","", ""],
    ['Search', 'Google Search', 'google_search_interface', 'tools.google_search'],
    ['Search', 'YouTube Search', 'main', 'tools.yt_search']
    ]

menu.add_edges(google_menu)

menu.create_menu()
run_current_functions()
st.code(menu.G.nodes.data())
st.code(list(menu.G.successors('HOME')))

# from tools.google_search import tool_main as google_search

# if st.button('Google Search'):
#     res = google_search('nrega')

#     st.code(res)
