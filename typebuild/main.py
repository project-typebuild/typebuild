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
#  google_menu = [
#     ['HOME', 'Search', None],
#     ['Search', 'Google Search', 'google_search_interface']
#     ]
# menu.add_edges(google_menu, 'tools.google_search')

# youtube_menu = [
#     ['HOME', 'Search', None],
#     ['Search', 'YouTube Search', 'main']
#     ]
# menu.add_edges(youtube_menu, 'tools.yt_search')

menu.create_menu()
run_current_functions()

# from tools.google_search import google_search_interface

# google_search_interface()