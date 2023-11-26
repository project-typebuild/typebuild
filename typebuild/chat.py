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
                # TODO: REMOVE SYSTEM MESSAGES AFTER FIXING BUGS
                the_content = msg['content']
                if msg['role'] in ['user', 'assistant']:
                    with st.chat_message(msg['role']):
                        if the_content.startswith('{'):
                            the_content = eval(the_content)
                            st.json(the_content)
                        if isinstance(the_content, dict):
                            st.json(the_content)
                        else:
                            st.markdown(the_content.replace('\n', '\n\n'))
                if msg['role'] == 'system':
                    st.info(the_content)        
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
    # FETC

    current_task = agent_manager.current_task
    # Get messages for the LLM
    system_instruction = agent_manager.get_system_instruction(agent_manager.current_task)
    # st.success(f"System instruction: {system_instruction}")
    prompt = None
    if agent_manager.current_task == 'orchestration':
        agent = agent_manager
    else:
        task = agent_manager.get_task(agent_manager.current_task)
        agent = task.agent
        task_name = task.task_name
        status = task.status
        if status == 'just_started':
            prompt = task.prompt
            agent_manager.set_task_status(task_name, 'current_task')
            prompt = task.prompt
        else:
            prompt = None

    messages = agent.get_messages_with_instruction(system_instruction, prompt=prompt)
    st.session_state.last_request = messages

    # Get the response from the LLM
    with st.spinner("Getting response from LLM..."):      
        res = get_llm_output(messages, model=agent.default_model)
        st.info(f"LLM output: {res}")
    return res

def populate_res_dict(res_dict, res):
    """
    If res dict is empty, use the string response to populate it.
    """
    if not res_dict:
        res_dict = {
            'output': res, 
            'task_finished': False,
            'ask_human': False,
            'ask_llm': True,
            }
    
    # If there is a final response, set the task_finished flag to true
    if 'final response' in res.lower():
        res_dict['task_finished'] = True
        res_dict['ask_llm'] = False
        res_dict['ask_human'] = False

    return res_dict

def manage_task(agent_manager, res_dict, res):
    
    # Convert the response to a dict even if it is a string
    res_dict = populate_res_dict(res_dict, res)
    
    # If the response is a request for a new agent, create the agent, if it does not exist
    if 'transfer_to_task' in res_dict:
        agent_name = res_dict.get('agent_name', 'agent_manager')
        task_name = res_dict.get('transfer_to_task', 'orchestration')
        task_description = res_dict.get('task_description', 'No description provided.')
        explain_to_user = res_dict.get('explain_to_user', None)
        # Add explanation as content to the messages
        if explain_to_user:
            agent_manager.set_message(
                role="assistant", 
                content=explain_to_user, 
                task=task_name
                )    

        if task_name != agent_manager.current_task and task_name != 'orchestration':
            st.info(f"Changing agent from {agent_manager.current_task} to {task_name}")
            agent_manager.add_task(
                agent_name=agent_name, 
                task_name=task_name, 
                task_description=task_description
                )
            # Add the message to the new task
            agent_manager.set_message(
                role="assistant", 
                content=task_description, 
                task=task_name,
                )

    if res_dict.get('task_finished', False):
        completed_task = agent_manager.current_task
        agent_manager.complete_task(completed_task)
        agent_manager.current_task = 'orchestration'
        st.session_state.ask_llm = False
    elif res_dict.get('ask_human', False):
        # Set the message to the worker agent via the agent manager
        st.session_state.ask_llm = False
    else:
        # If we are not sure, ask LLM.
        st.session_state.ask_llm = res_dict.get('ask_llm', True)
      

    # Add the response to the current task
    content = res_dict.get('output', str(res_dict))
    if content:
        agent_manager.set_message(
            role="assistant", 
            content=content, 
            task=agent_manager.current_task
            )

    # If ask_human is true in the response, set the ask_llm to false
    # If the current task is still orchestration, check for next task, if any.
    if agent_manager.current_task == 'orchestration':
        # Get the next task
        next_task = agent_manager.get_next_task()
        # If there is a next task, set the current task to the next task
        if next_task is not None:
            st.session_state.ask_llm = True

    return res_dict


def manage_tool_interaction(agent_manager, res_dict):
    """
    If an agent requested to use a tool,
    this function will run the tool and return the result to the agent.

    It will also request a response from the LLM.
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
    if tool_result.get('task_finished', True):
        # Add a message from the tool to the agent manager
        content = f"""MESSAGE TO THE AGENT MANAGER.  
        The {agent_manager.current_task} task is done.\n"""

        if tool_result.get('content', None):
            content += f"""Here are some notes from the completed task that you can use to help the user:  
            {tool_result['content']}"""
        # Set the current task to orchestration
        agent_manager.current_task = 'orchestration'
        # Message to agent manager goes as system message
        role = 'system'
    else:
        content = tool_result.get('content', '')
        role = 'user'
    # Set ask_llm status
    st.session_state.ask_llm = tool_result.get('ask_llm', True)
    if content:
        # Add this to the agent's messages
        agent_manager.set_message(
            role=role, 
            content=content,
            task=agent_manager.current_task
            )

    with st.spinner("Let me study the results..."):
        st.sidebar.warning(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {agent_manager.current_task}")
    return None

def show_task_messages(agent_manager):
    """
    Show the task names in a drop down
    and the messages for the selected task.
    """
    # Get the task names
    task_names = agent_manager.managed_tasks.keys()
    # Show the task names in a drop down
    all_tasks = list(task_names)
    all_tasks.insert(0, 'orchestration')
    all_tasks.insert(0, 'SELECT')
    selected_task = st.sidebar.selectbox("Select task", all_tasks)
    # Show the messages for the selected task
    if selected_task != 'SELECT':
        if selected_task == 'orchestration':
            messages = agent_manager.messages
        else:
            messages = agent_manager.managed_tasks[selected_task].agent.messages
        st.header(f"Messages for {selected_task}")
        display_messages(messages)
        st.stop()
    return None

def add_objective(agent_manager):
    """
    Adds the next tasks to the agent manager.
    """

    # TODO: FIND OUT WHY THIS GETS REPEATED MANY TIMES.
    objective = "Haiku collection on each season"
    tasks = ['summer', 'winter']
    # Tasks not in managed tasks
    tasks_to_add = [i for i in tasks if i not in agent_manager.managed_tasks]
    
    if tasks_to_add:
        st.sidebar.info("There are new tasks to add.  Click the button below to add them.")
        if st.sidebar.button("Add new tasks"):
            for task in tasks_to_add:
                # Create new search task
                agent_manager.add_task(
                    agent_name='agent_manager', 
                    task_name=f'{task}_haiku', 
                    task_description=f'Write a haiku about {task}'
                    )
                # Set ask llm to true
            st.session_state.ask_llm = True
    completed_tasks = "\n- ".join([i for i in tasks if i in agent_manager.completed_tasks])
    if completed_tasks:
        completed_tasks = f"### Completed tasks:\n\n- {completed_tasks}"
    scheduled_tasks = "\n- ".join([i for i in tasks if i in agent_manager.scheduled_tasks])
    if scheduled_tasks:
        scheduled_tasks = f"### Scheduled tasks:\n\n- {scheduled_tasks}"
    task_info = f"""# {objective}
    There are {len(tasks)} tasks in this objective.
    {completed_tasks}
    {scheduled_tasks}
    """
    # Remove indents
    task_info = "\n".join([i.strip() for i in task_info.split('\n')])
    st.sidebar.markdown(task_info)
    return None

# TODO: MAKE THIS A CHAT FRAMEWORK CLASS
def chat():

    # Add the agent manager to the session state
    add_agent_manager_to_session_state()
    agent_manager = st.session_state.agent_manager
     
    add_objective(agent_manager)

    # Create the chat input and display
    st.sidebar.success(f"Scheduled tasks: {agent_manager.scheduled_tasks}")
    agent_manager.chat_input_method()    
    show_task_messages(agent_manager)
    messages = agent_manager.get_messages()    
    display_messages(messages, expanded=True)

    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {agent_manager.current_task}")

    # ask_llm took can be set to true by agents or by tools
    # that add to the message queue without human input
    # and request a response from the llm
    if st.session_state.ask_llm:
        # Get the response from the llm
        res = manage_llm_interaction(agent_manager)        
        # Extract the response dictionary
        res_dict = st.session_state.extractor.extract_dict_from_response(res)
        # st.write(res_dict)
        # st.code(res)
        res_dict = manage_task(agent_manager, res_dict, res)
        # If a tool is used, ask the llm to respond again
        if 'tool_name' in res_dict:
            manage_tool_interaction(agent_manager, res_dict)
            

        st.rerun()

    return None
