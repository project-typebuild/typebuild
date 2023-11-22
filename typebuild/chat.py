import streamlit as st
from plugins.llms import get_llm_output
import os
from glob import glob
from agents import AgentManager, Agent
import importlib
import json    
import time
import inspect

def display_messages(messages, expanded=True):
    """
    Displays the messages in the chat.

    Utilizes Streamlit's expander and chat_message for displaying messages.
    This method iterates through the messages list and displays each one based
    on the role (user, assistant, system).

    Returns:
        None
    """
    if messages:
        with st.expander("View chat", expanded=expanded):
            for i, msg in enumerate(messages):
                if msg['role'] in ['user', 'assistant']:
                    the_content = msg['content']
                    with st.chat_message(msg['role']):
                        st.markdown(the_content)
    return None



def test_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    test_menu_items = [
        ['HOME', 'Chat', 'chat', 'test']
    ]    
    menu.add_edges(test_menu_items)
    return None

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
    system_instruction = agent_manager.get_system_instruction(st.session_state.current_task)
    if st.session_state.current_task == 'orchestration':
        # Check if there are new tasks
        next_task = agent_manager.get_next_task()
        if next_task:
            agent = agent_manager.get_agent(next_task)
        else:
            agent = agent_manager
    else:
        agent = agent_manager.get_agent(st.session_state.current_task)
    messages = agent.get_messages_with_instruction(system_instruction)
    st.session_state.last_request = messages

    # Get the response from the LLM
    with st.spinner("Getting response from LLM..."):      
        res = get_llm_output(messages, model=agent.default_model)
        st.info(f"LLM output: {res}")
        time.sleep(2)
    return res

def manage_task(agent_manager, res_dict, res):
    # If the response is a request for a new agent, create the agent, if it does not exist
    if 'transfer_to_task' in res_dict:
        agent_name = res_dict.get('agent_name', 'agent_manager')
        task_name = res_dict.get('transfer_to_task', 'orchestration')
        task_description = res_dict.get('task_description', 'No description provided.')

        st.session_state.current_task = task_name

        if task_name != agent_manager.current_task:
            st.info(f"Changing agent from {agent_manager.current_task} to {task_name}")
            agent_manager.add_task(
                agent_name=agent_name, 
                task_name=task_name, 
                task_description=task_description
                )


    # Agents that use tools may have to work more than once
    # with the tool to get the desired result.  When the agent is done
    # It sends a final response to the agent manager.  
    # If it is the final response, set the message to the agent manager
    # If not, set the message to the agent and ask LLM for another response

    if st.session_state.current_task == 'orchestration':
        st.session_state.ask_llm = False
    # If it is a final response from a worker agent
    elif 'final response' in res.lower():
        # Remove the line with the phrase "final response"
        res = '\n'.join([i for i in res.split('\n') if not i.lower().strip().startswith('final response')])
        
        # TEMP: Save agent messages to session state for debugging
        st.session_state.agent_messages = agent_manager.managed_tasks[st.session_state.current_task].agent.messages
        
        # TODO: REMOVE THE COMMENTED LINES BELOW
        # Get the current agent so that we can delete it
        # current_agent = agent_manager.current_agent
        # Set the current agent to the agent manager
        
        
        agent_manager.current_task = 'orchestration'
        # Set ask task to orchestration
        st.session_state.current_task = 'orchestration'
        # Delete the agent (We are not deleting the agent or task anymore so that we can retain the messages)
        # agent_manager.remove_agent(current_agent)
        st.session_state.ask_llm = False
    else:
        # Set the message to the worker agent via the agent manager
        st.session_state.ask_llm = True

    # Add the response to the current task
    agent_manager.set_assistant_message(res, task=st.session_state.current_task)

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
        st.sidebar.warning(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {st.session_state.current_task}")
        time.sleep(2)
    return None

# TODO: MAKE THIS A CHAT FRAMEWORK CLASS
def chat():

    # Add the agent manager to the session state
    add_agent_manager_to_session_state()
    agent_manager = st.session_state.agent_manager

    # Create the chat input and display
    agent_manager.chat_input_method()    
    display_messages(agent_manager.messages, expanded=True)

    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {st.session_state.current_task}")

    # ask_llm took can be set to true by agents or by tools
    # that add to the message queue without human input
    # and request a response from the llm
    if st.session_state.ask_llm:
        # Get the response from the llm
        res = manage_llm_interaction(agent_manager)        
        res_dict = st.session_state.extractor.extract_dict_from_response(res)
        manage_task(agent_manager, res_dict, res)
        # If a tool is used, ask the llm to respond again
        if 'tool_name' in res_dict:
            manage_tool_interaction(agent_manager, res_dict)

        st.rerun()

    return None
