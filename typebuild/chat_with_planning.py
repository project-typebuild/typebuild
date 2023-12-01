"""
***Current objective:***
- LLM interprets parent as a task taht has to happen before.  We start at the leaf.
- Planner creates tasks that require messages to be passed from one to the other.  Currently, each task gets only its message.

"""

import time
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
        if isinstance(msg.content, str) and msg.content.strip().startswith('{'):
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
    else:
        next_task_name = tg.get_next_task()
        st.session_state.current_task = next_task_name
        next_task = tg.get_next_task_node()['task']
        system_instruction = next_task.get_system_instruction()
    
    messages = tg.messages.get_messages_for_task(st.session_state.current_task)
    messages.insert(0, {"role": "system", "content": system_instruction})
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

def set_next_actions(res_dict):
    """
    Parse the response to see 
    1. If the next step should go to the LLM or a human
    2. If tasks must be added to the task graph
    3. To set the current task in the session state
    """
    tg = st.session_state.task_graph
    if res_dict.get('type', None) == 'task_graph':
        tg.name = res_dict.get('name', None)
        tg.objective = res_dict.get('objective', None)
        st.success("I set the task graph name and objective.")
        time.sleep(2)

    # If ask human is in the response, set ask_llm to the opposite
    if "ask_human" in res_dict:
        st.session_state.ask_llm = not res_dict['ask_human']

    for task_res in res_dict.get('task_list', []):
        tg.add_task(**task_res)
        # If ask human is in the response, set ask_llm to the opposite
        if "ask_human" in res_dict:
            st.session_state.ask_llm = not res_dict['ask_human']
    if res_dict.get("task_finished", False):
        finish_tasks(res_dict)
    return None

def finish_tasks(res_dict):
    """
    Determines what to do when a task is finished
    """
    # If task_finished is True, set ask llm to False
    # If current task is planning, set it as not planning and other way around
    if st.session_state.current_task == 'planning':
        st.session_state.current_task = 'task_graph'
        st.session_state.task_graph.send_to_planner = False
    else:
        # Finish the current task
        st.session_state.task_graph.update_task(
            task_name=st.session_state.current_task,
            completed=True
            )
        next_task = st.session_state.task_graph.get_next_task()
        if next_task == 'root':
            st.success("All tasks are completed.")
            st.session_state.ask_llm = False
            st.session_state.task_graph.send_to_planner = True
        else:
            st.session_state.current_task = next_task
            st.session_state.ask_llm = True
            st.session_state.task_graph.send_to_planner = False

    return None

def manage_tool_interaction(res_dict):
    """
    
    """
    tool_name = res_dict['tool_name']
    tool_module = importlib.import_module(f'tools.{tool_name}')
    tool_function = getattr(tool_module, 'tool_main')

    # Get the tool arguments needed by the tool
    tool_args = inspect.getfullargspec(tool_function).args

    # Arguments for tool will be in res_dict under the key kwargs
    args_for_tool = res_dict.get('kwargs', res_dict)

    # select the required arguments from res_dict and pass them to the tool
    kwargs = {k: v for k, v in args_for_tool.items() if k in tool_args}
    tool_result = tool_function(**kwargs)
    # TODO: Some tools like search need to consume the tool results.
    # Others like navigator need not.  Create a system to pass to the
    # correct task. 
    if isinstance(tool_result, str):
        tool_result = {'content': tool_result}

    # Check if the the task is done and can be transferred to orchestration.

    content = tool_result.get('content', '')
    role = 'assistant'
    # Set ask_llm status
    if content:
        if tool_result.get('task_finished', False):
            finish_tasks(tool_result)
        else:
            st.session_state.ask_llm = True
        
        # Add this to the agent's messages
        st.session_state.task_graph.messages.set_message(
            role=role, 
            content=content, 
            created_by=st.session_state.current_task, 
            created_for=st.session_state.current_task
            )

    return None

def chat():
    """
    Chat with the planning agent
    """
    if st.sidebar.button("Stop LLM"):
        st.session_state.ask_llm = False
    if 'task_graph' not in st.session_state:
        st.session_state.task_graph = TaskGraph()
    add_planning_to_session_state()
    tg = st.session_state.task_graph
    all_tasks = tg.graph.nodes
    st.sidebar.header("All tasks")
    st.sidebar.code(all_tasks)

    # Display chat input method
    tg.messages.chat_input_method(task_name=st.session_state.current_task)
    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {st.session_state.current_task}")
    display_messages()
    if st.session_state.ask_llm:
        res = manage_llm_interaction()
        res_dict = json.loads(res)
        # Find if LLM should be invoked automatically
        # and next action if task is finished
        set_next_actions(res_dict)
        if 'tool_name' in res_dict:
            manage_tool_interaction(res_dict)
        st.rerun()
    # TODO: Create the loop for the task graph.
    # Message 0 should be system instruction & message 1 should be the description.
    
    next_task = tg.get_next_task()
    if next_task != 'root':
        task_object = tg.graph.nodes[next_task]['task']
        task_messages = tg.messages.get_messages_for_task(next_task)
        for node in tg.graph.nodes:
            st.info(tg.graph.nodes[node])
    if next_task != 'root':
        if st.button(f"Start task {next_task}"):
            st.session_state.ask_llm = True
            tg.send_to_planner = False
            the_task = tg.graph.nodes[next_task]['task']
            si = the_task.get_system_instruction()
            st.code(si)
            st.markdown(the_task.task_description)
            st.rerun()