"""
Current objective:
- There chat can start with or without a task graph.
- If there is no task graph, the planner will create one.
- If there is a task graph, the planner will review it and suggest changes, if any.
- Then we move to the trask_graph that will complete tasks one by one.
"""

import streamlit as st
from plugins.llms import get_llm_output
import os
from glob import glob
from task import Task
from task_graph import TaskGraph
import importlib
import json
import inspect

def display_messages(expanded=True):
    """
    Displays the messages in the chat.

    Utilizes Streamlit's expander and chat_message for displaying messages.
    This method iterates through the messages list and displays each one based
    on the role (user, assistant, system).

    Returns:
        None
    """
    messages = st.session_state.task_graph.messages.get_all_messages()
    for i, msg in enumerate(messages):
        if isinstance(msg.content, str) and msg.content.startswith('{'):
            content = json.loads(msg.content).get('user_message', msg.content)
        else:
            content = msg.content
        if msg.role in ['user', 'assistant']:
            with st.chat_message(msg.role):
                st.markdown(content.replace('\n', '\n\n'))
        # TODO: REMOVE SYSTEM MESSAGES AFTER FIXING BUGS
        if msg.role == 'system':
            st.info(content)        
    return None

def manage_llm_interaction():

    planning = st.session_state.planning
    tg = st.session_state.task_graph
    m = tg.messages
    if tg.send_to_planner:
        system_instruction = planning.get_system_instruction()
    messages = tg.messages.get_messages_for_task('planning')
    system_instruction = planning.get_system_instruction()
    messages = m.get_messages_with_instruction(system_instruction)
    res = get_llm_output(messages, model=planning.default_model)
    m.set_message(role="assistant", content=res, created_by=st.session_state.current_task, created_for=st.session_state.current_task)
    return res

def get_task_graph_details():
    """
    Get the name of the task, the description, and the markdown of subtasks
    from the task graph as a string
    """
    tg = st.session_state.task_graph
    task_name = tg.name
    task_objective = tg.objective
    task_md = tg.generate_markdown()
    task_info = f"""
    TASK NAME: {task_name}
    OBJECTIVE: {task_objective}
    LIST OF SUBTASKS:
    {task_md}
    """
    return task_info

def add_planning_to_session_state():
    """
    Add the planner to the session state
    """
    if 'planning' not in st.session_state:
        
        # Get all the agents from the agent_definitions folder, in os independent way
        # Current directory plus agent_definitions
        agent_definitions = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'agent_definitions')
        # Get all the files in the agent_definitions folder
        agent_files = glob(os.path.join(agent_definitions, '*.yml'))
        # Get the agent names
        agent_names = [os.path.basename(i).replace('.yml', '') for i in agent_files]
        # TODO: Remove agent manager until we remove it from the definitions
        agent_names.remove('agent_manager')
        # Provide agent names to Planning task
        if 'task_graph' not in st.session_state:
            st.session_state.task_graph = TaskGraph()
        
        task_graph = st.session_state.task_graph
        # Get task graph details if the graph has a name.
        # No name means that the user has not yet defined the task graph
        if task_graph.name:
            planning_task_desc = get_task_graph_details()

        else:
            planning_task_desc = "\nWe do not know the user's objective yet and the task graph has not been created.\n"
        
        planning = Task(
            task_name='planning', 
            task_description=planning_task_desc,
            agent_name='master_planner',
            available_agents=agent_names,
            )
        st.session_state.planning = planning
        
        st.session_state.current_task = 'planning'
    return None

def chat():
    """
    Chat with the planning agent
    """
    add_planning_to_session_state()
    tg = st.session_state.task_graph
    planning = st.session_state.planning
    all_tasks = tg.graph.nodes
    st.sidebar.header("All tasks")
    st.sidebar.code(all_tasks)

    # Display chat input method
    tg.messages.chat_input_method()
    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {st.session_state.current_task}")
    display_messages()
    if st.session_state.ask_llm:
        res = manage_llm_interaction()
        res_object = json.loads(res)

        if isinstance(res_object, dict):
            res_list = [res_object]

        for res_dict in res_list:
            # If it has a task description, then add it to the task graph
            if res_dict.get('task_description', None):
                tg.add_task(**res_dict)
                
            if res_dict.get("ask_human", False):
                st.session_state.ask_llm = False
        
        st.rerun()