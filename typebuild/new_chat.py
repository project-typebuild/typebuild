
import streamlit as st
from plugins.llms import get_llm_output
import os
from glob import glob
from task import Task
from task_graph import TaskGraph
import importlib

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
                
                if msg.role in ['user', 'assistant']:
                    with st.chat_message(msg.role):
                        if msg.content.startswith('{'):
                            msg.content = eval(msg.content)
                            st.json(msg.content)
                        if isinstance(msg.content, dict):
                            st.json(msg.content)
                        else:
                            st.markdown(msg.content.replace('\n', '\n\n'))
                if msg.role == 'system':
                    st.info(msg.content)        
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

def get_template():
    task_graph = TaskGraph("Create haikus on all seasons")
    # Example Usage
    task_graph.add_task(
        task_name='Fall haiku', 
        agent_name='haiku_agent',
        task_description='Write a haiku about the Fall season',
        )

    task_graph.add_task(
        task_name='Winter haiku', 
        agent_name='haiku_agent',
        task_description='Write a haiku about winter',
        )
    return task_graph

def add_orchestration_to_session_state():
    if 'orchestration' not in st.session_state:
        task_graph = get_template()
        st.session_state.task_graph = task_graph
        # Get all the agents from the agent_definitions folder, in os independent way
        # Current directory plus agent_definitions
        agent_definitions = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'agent_definitions')
        # Get all the files in the agent_definitions folder
        agent_files = glob(os.path.join(agent_definitions, '*.yml'))
        # Get the agent names
        agent_names = [os.path.basename(i).replace('.yml', '') for i in agent_files]
        # Add the agent names to AgentManager
        orchestration_task_desc = f"""
        You are helping the user complete the task: {task_graph.name}.  It has {task_graph.graph.number_of_nodes()}.
        """
        orchestration = Task(
            task_name='orchestration', 
            task_description=orchestration_task_desc,
            agent_name='agent_manager',
            available_agents=agent_names,
            )
        st.session_state.orchestration = orchestration
        st.markdown(task_graph.generate_markdown())
        st.session_state.current_task = 'orchestration'
    return None

def manage_llm_interaction_old():
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

def manage_llm_interaction():

    orchestration = st.session_state.orchestration
    tg = st.session_state.task_graph
    messages = tg.messages.get_messages_for_task('orchestration')
    system_instruction = orchestration.get_system_instruction()
    messages = tg.messages.get_messages_with_instruction(system_instruction)
    res = get_llm_output(messages, model=orchestration.default_model)
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




# TODO: MAKE THIS A CHAT FRAMEWORK CLASS
def chat():

    # Add the agent manager to the session state
    add_orchestration_to_session_state()
    tg = st.session_state.task_graph    
    orchestration = st.session_state.orchestration
     
    # Create the chat input and display
    tg.messages.chat_input_method()    
    messages = tg.messages.get_all_messages()
    
    display_messages(messages, expanded=True)
    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {st.session_state.current_task}")


    # ask_llm took can be set to true by agents or by tools
    # that add to the message queue without human input
    # and request a response from the llm
    if st.session_state.ask_llm:
        # Get the response from the llm
        res = manage_llm_interaction()        
        # Extract the response dictionary
        res_dict = st.session_state.extractor.extract_dict_from_response(res)
        st.write(res_dict)
        st.code(res)
        st.stop()
        res_dict = manage_task(agent_manager, res_dict, res)
        # If a tool is used, ask the llm to respond again
        if 'tool_name' in res_dict:
            manage_tool_interaction(agent_manager, res_dict)
            

        st.rerun()

    return None
