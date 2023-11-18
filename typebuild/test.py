import streamlit as st
from chat_framework import ChatFramework
from plugins.llms import get_llm_output
import os
from glob import glob
from agents import AgentManager, Agent
import importlib
import json    

def test_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    test_menu_items = [
        ['HOME', 'Chat', 'chat', 'test']
    ]    
    menu.add_edges(test_menu_items)
    return None

def empty_func():
    return None

def print_success():
    st.success('Success')
    return None

def extract_dict(s):
    try:
        start = s.index('{')
        end = s.rindex('}') + 1
        dict_str = s[start:end]
        return json.loads(dict_str)
    except ValueError:
        return {}

def chat():
    # Get all the agents from the agent_definitions folder, in os independent way
    # current directory plus agent_definitions
    agent_definitions = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'agent_definitions')
    # Get all the files in the agent_definitions folder
    agent_files = glob(os.path.join(agent_definitions, '*.yml'))
    # Get the agent names
    agent_names = [os.path.basename(i).replace('.yml', '') for i in agent_files]
    # Add the agent names to AgentManager

    agent_manager = AgentManager('agent_manager')

    # Look for all the agents in the agent_deifnitions folder and add them.
    for agent_name in agent_names:
        agent = Agent(agent_name)
        agent_manager.add_agent(agent_name, agent)

    if 'test_cf' not in st.session_state:
        st.session_state.test_cf = ChatFramework()

    cf = st.session_state.test_cf
    cf.chat_input_method()
    cf.display_messages()
    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nAsk agent: {st.session_state.ask_agent}")
    
    if st.session_state.ask_llm:
        
        system_instruction = agent_manager.get_system_instruction(st.session_state.ask_agent)
        model = agent_manager.get_model(st.session_state.ask_agent)
        messages = cf.get_messages_with_instruction(system_instruction)
        st.session_state.last_request = messages
        
        res = get_llm_output(messages, model=model)
        cf.set_assistant_message(res)

        res_dict = extract_dict(res)
        if 'tool_name' in res_dict:
            tool_name = res_dict['tool_name']
            tool_module = importlib.import_module(f'tools.{tool_name}')
            tool_function = getattr(tool_module, 'tool_main')
            tool_result = tool_function(**res_dict['kwargs'])

        cf.ask_llm = False
        st.rerun()

        if 'last_request' in st.session_state:
            st.json(st.session_state.last_request)
        return None


from tools.google_search import GoogleSearchSaver
def google_search_interface():
    # Create an instance of the GoogleSearchSaver class
    searcher = GoogleSearchSaver()

    search_term = st.text_input('Enter search term')
    num_results = st.number_input('Enter number of results', min_value=1, max_value=50, value=10)

    if st.button('Get results'):
        with st.spinner('Getting results...'):
            # Perform the Google search
            searcher.get_google_search_results(search_term, num_results=num_results)
            # Save results to a Parquet file
            st.session_state.project_folder = 'tmp'
            searcher.store_to_db(search_term, project_folder=st.session_state.project_folder)

            # Retrieve and display the file name where results are saved
            file_name = searcher.get_file_name()
            st.success('Done.')
            st.write('Results saved to parquet file.')
            st.write(f"Data saved to {file_name}")
    return None

from tools.yt_search import search_youtube_and_save_results

def search_youtube():
    search_term = st.text_input("Search YouTube")
    num_videos = st.number_input("How many videos?", min_value=1, max_value=20, value=10, step=2)
    if st.button("Search"):
        search_youtube_and_save_results(search_term=search_term, num_videos=num_videos)
    return None