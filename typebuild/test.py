import streamlit as st
from chat_framework import ChatFramework
from plugins.llms import get_llm_output
import os
from glob import glob
from agents import AgentManager, Agent
    
def test_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    test_menu_items = [
        ['HOME', 'Chat', 'chat', 'test'],
    ]    
    menu.add_edges(test_menu_items)
    return None

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
        cf.ask_llm = False
        st.rerun()

    if 'last_request' in st.session_state:
        st.json(st.session_state.last_request)
    return None