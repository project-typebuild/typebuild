import sys
import simple_auth
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
import streamlit as st


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

menu.create_menu()
run_current_functions()

import yaml

# read the yaml file for the system instructions
with open('system_instructions/agent_manager.yml', 'r') as f:
    system_instruction = yaml.load(f, Loader=yaml.FullLoader)

# del system_instruction['available_agents']
# st.json(system_instruction)

# instantiate the agent manager
from new_agent import AgentManager

am = AgentManager('data_agent')

instance_vars = am.get_instance_vars()

# available_agents = instance_vars['available_agents']
st.sidebar.write(instance_vars)