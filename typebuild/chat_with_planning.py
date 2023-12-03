"""
***Current objective:***
- LLM interprets parent as a task that has to happen before.  We start at the leaf.
- Planner creates tasks that require messages to be passed from one to the other.  Currently, each task gets only its message.

# TODO:
- Save graph to file and try opening it.
- Select conversation by graph name.

# TODO: NAVIGATION FIXES
- Navigation right now is not called as a task.  Either create a task, or call the nav agent directly.
- Make sure that we do not have too many calls for simple navigation.
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
from extractors import Extractors

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
        if msg.get('content', '').strip().startswith('{'):
            res_dict = json.loads(msg['content'])
        else:
            res_dict = {}
            
        if isinstance(msg, dict):
            content = msg.get('content')
            if 'user_message' in content:
                content = json.loads(content)['user_message']
        elif isinstance(msg.content, str) and msg.content.strip().startswith('{'):
            res_dict = json.loads(msg.content)
            content = res_dict.get('user_message', msg.content)
        else:
            content = msg.content

        if msg['role'] in ['user', 'assistant']:
            with st.chat_message(msg['role']):
                st.markdown(content.replace('\n', '\n\n'))
        # TODO: REMOVE SYSTEM MESSAGES AFTER FIXING BUGS
        if msg['role'] == 'system':
            st.info(content)        
        
        if "tool_name" in res_dict:
            st.success(f"Tool name: {res_dict['tool_name']}")
            manage_tool_interaction(res_dict, from_llm=False)
    return None

def manage_llm_interaction():

    planning = st.session_state.planning
    tg = st.session_state.task_graph
    m = tg.messages
    model = planning.default_model
    if st.session_state.current_task == 'planning':
        system_instruction = planning.get_system_instruction()
        messages = tg.messages.get_all_messages()
    else:
        next_task_name = tg.get_next_task()
        st.session_state.current_task = next_task_name
        next_task = tg.get_next_task_node()
        # Check if there are tasks, else send to planning
        if next_task:
            system_instruction = next_task['task'].get_system_instruction()
            messages = tg.get_messages_for_task_family(st.session_state.current_task)

            if 'default_model' in next_task['task'].__dict__:
                model = next_task['task'].default_model
        else:
            system_instruction = planning.get_system_instruction()
            messages = tg.messages.get_all_messages()
    
    messages.insert(0, {"role": "system", "content": system_instruction})
    res = get_llm_output(messages, model=model)
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
        if next_task:
            st.session_state.current_task = next_task
            st.session_state.ask_llm = True
            st.session_state.task_graph.send_to_planner = False
        else:
            st.session_state.current_task = 'planning'
            st.session_state.ask_llm = False
            st.session_state.task_graph.send_to_planner = True

    return None

def check_for_auto_rerun(func):
    # Get the signature of the function
    sig = inspect.signature(func)

    # Get the parameters from the signature
    params = sig.parameters

    # Get the arguments and their default values
    args_and_defaults = {name: param.default if param.default is not param.empty else None for name, param in params.items()}

    # Check if the function has an auto_rerun argument
    return args_and_defaults.get('auto_rerun', False)


def manage_tool_interaction(res_dict, from_llm=False, run_tool=False):
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
    
    if not run_tool:
        # Check if the tool should be run automatically
        run_tool = check_for_auto_rerun(tool_function)
    if run_tool:
        tool_result = tool_function(**kwargs)
        # TODO: Some tools like search need to consume the tool results.
        # Others like navigator need not.  Create a system to pass to the
        # correct task. 
        if isinstance(tool_result, str):
            tool_result = {'content': tool_result}

        # Check if the the task is done and can be transferred to orchestration.

        content = tool_result.get('content', '')
        # Set ask_llm status
        if content:
            if from_llm:
                if tool_result.get('task_finished', False) == True:
                    finish_tasks(tool_result)
                else:
                    st.session_state.ask_llm = True
                    st.sidebar.success(f"Task is not finished yet for task {st.session_state.current_task}")
                    time.sleep(2)
                # Add this to the agent's messages
                st.session_state.task_graph.messages.set_message(
                    role='user', 
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
    current_task = st.session_state.current_task
    st.sidebar.info(f"Current task: {current_task}")
    # all_messages = tg.get_messages_for_task_family(current_task)
    # st.sidebar.write(all_messages)
    
    if st.sidebar.button("Save graph"):
        tg._save_to_file()
        st.success("Saved graph to file.")
        st.stop()
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
            manage_tool_interaction(res_dict, from_llm=True)
        st.rerun()
    # TODO: Create the loop for the task graph.
    # Message 0 should be system instruction & message 1 should be the description.
    # Check if current node task is incomplete
    
    next_task = tg.get_next_task()
    if next_task:
        
        if st.button(f"Start task {next_task}"):
            st.session_state.ask_llm = True
            tg.send_to_planner = False
            st.session_state.current_task = next_task
            the_task = tg.graph.nodes[next_task]['task']
            si = the_task.get_system_instruction()
            st.code(si)
            st.markdown(the_task.task_description)
            st.rerun()
    else:
        # See if there are no messages
        if not tg.messages.get_all_messages():
            st.header("What would you like to do?")
            what_to_do = """Just chat with me below to get started.
            
            - Navigate with chat
            - Create a new project
        """
            extractor = Extractors()
            st.markdown(extractor.remove_indents_in_lines(what_to_do))
    #    Implement this after serialization to json is done
    #     # Allow the user to load a task graph
        
        tg._load_from_file()