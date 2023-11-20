import streamlit as st
from chat_framework import display_messages
from plugins.llms import get_llm_output
import os
from glob import glob
from agents import AgentManager, Agent, parse_agent_name_and_message
import importlib
import json    
import time


def test_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    test_menu_items = [
        ['HOME', 'Chat', 'chat', 'test']
    ]    
    menu.add_edges(test_menu_items)
    return None

def extract_dict(s):
    # TODO: Move this to a file called extractors.  Create a detailed class.
    if isinstance(s, dict):
        return s
    elif isinstance(s, list):
        return s
    elif isinstance(s, str):
        s = s.strip()
        try:
            start = s.index('{')
            end = s.rindex('}') + 1
            dict_str = s[start:end]
            return json.loads(dict_str)
        except ValueError:
            return {}
    else:
        return {}

# TODO: Refactor this code into smaller blocks.  Make this a class, perhaps the chat framework.
def add_agent_manager_to_session_state():
    if 'agent_manager' not in st.session_state:
        # Get all the agents from the agent_definitions folder, in os independent way
        # Current directory plus agent_definitions
        agent_definitions = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'agent_definitions')
        # Get all the files in the agent_definitions folder
        agent_files = glob(os.path.join(agent_definitions, '*.yml'))
        # Get the agent names
        agent_names = [os.path.basename(i).replace('.yml', '') for i in agent_files]
        # Add the agent names to AgentManager
        agent_manager = AgentManager('agent_manager', agent_names)
        st.session_state.agent_manager = agent_manager
    return None

def manage_llm_interaction(agent_manager):
    """
    This function sends messages to the LLM and gets a response.
    Based on the response, it could create additional specialized agents
    to handle the request.  It also routes the response to the appropriate agent.

    Parameters:
    - agent_manager: The agent manager object.

    Returns (str):
    - The response from the LLM.
    """
    # Get messages for the LLM
    system_instruction = agent_manager.get_system_instruction(st.session_state.ask_agent)
    # TODO: The agent has to be in the session state.  Just access from the manager.
    if st.session_state.ask_agent == 'agent_manager':
        agent = agent_manager
    else:
        agent = agent_manager.get_agent(st.session_state.ask_agent)
    messages = agent.get_messages_with_instruction(system_instruction)
    st.session_state.last_request = messages

    # Get the response from the LLM
    with st.spinner("Getting response from LLM..."):      
        res = get_llm_output(messages, model=agent.default_model)
        st.info(f"LLM output: {res}")
        time.sleep(2)

    # If the response is a request for a new agent, create the agent, if it does not exist
    if "<<<" in res:
        agent_name, instruction, res = parse_agent_name_and_message(res)
        st.session_state.ask_agent = agent_name

        if agent_name != agent_manager.current_agent:
            st.info(f"Changing agent from {agent_manager.current_agent} to {st.session_state.ask_agent}")
            agent_manager.add_agent(st.session_state.ask_agent)


    # Agents that use tools may have to work more than once
    # with the tool to get the desired result.  When the agent is done
    # It sends a final response to the agent manager.  
    # If it is the final response, set the message to the agent manager
    # If not, set the message to the agent and ask LLM for another response

    if st.session_state.ask_agent == 'agent_manager':
        st.session_state.ask_llm = False
    # If it is a final response from a worker agent
    elif 'final response' in res.lower():
        # Remove the line with the phrase "final response"
        res = '\n'.join([i for i in res.split('\n') if not i.lower().strip().startswith('final response')])
        
        # TEMP: Save agent messages to session state for debugging
        st.session_state.agent_messages = agent_manager.managed_agents[st.session_state.ask_agent].messages
        
        # Get the current agent so that we can delete it
        current_agent = agent_manager.current_agent
        # Set the current agent to the agent manager
        agent_manager.current_agent = 'agent_manager'
        # Set ask agent to agent manager
        st.session_state.ask_agent = 'agent_manager'
        # Delete the agent
        agent_manager.remove_agent(current_agent)
        st.session_state.ask_llm = False
    else:
        # Set the message to the worker agent via the agent manager
        st.session_state.ask_llm = True

    # Add the response to the current agent
    agent_manager.set_assistant_message(res, agent=st.session_state.ask_agent)

    return res

def manage_tool_interaction(agent_manager, res_dict):
    """
    If an agent requested to use a tool,
    this function will run the tool and return the result to the agent.

    It will also request a response from the LLM.
    """
    tool_name = res_dict['tool_name']
    tool_module = importlib.import_module(f'tools.{tool_name}')
    tool_function = getattr(tool_module, 'tool_main')
    tool_result = tool_function(**res_dict['kwargs'])
    st.info(tool_result)
    # Add this to the agent's messages
    agent_manager.set_user_message(tool_result)

    with st.spinner("Let me study the seach results..."):
        st.session_state.ask_llm = True
        st.sidebar.warning(f"Ask llm: {st.session_state.ask_llm}\n\nAsk agent: {st.session_state.ask_agent}")
        time.sleep(2)
    return None

def chat():

    # Add the agent manager to the session state
    add_agent_manager_to_session_state()
    agent_manager = st.session_state.agent_manager
    
    # Create the chat input and display
    agent_manager.chat_input_method()    
    display_messages(agent_manager.messages, expanded=True)

    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nAsk agent: {st.session_state.ask_agent}")

    # ask_llm took can be set to true by agents or by tools
    # that add to the message queue without human input
    # and request a response from the llm
    if st.session_state.ask_llm:
        # Get the response from the llm
        res = manage_llm_interaction(agent_manager)        
        res_dict = extract_dict(res)
        # If a tool is used, ask the llm to respond again
        if 'tool_name' in res_dict:
            manage_tool_interaction(agent_manager, res_dict)

        st.rerun()

    return None
