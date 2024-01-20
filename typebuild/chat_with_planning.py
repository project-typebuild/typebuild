"""
***Current objective:***

- If a graph exists, allow the user to add tasks to it. Right now, planner is creating new graphs.
- [ ] Vivek: How to use metadata in files while executing tasks.  We need this to get system instruction from 
    prompt agent to the llm for tables agent.
- [ ] Vivek: User should be able to go back to a task anytime.
- [ ] Vivek: Start task button should not appear after a task is done.

# Ranu: Create APIs    
- [x] Create youtube search
- [ ] Add comment search, search by channel and playlist
- [ ] Write endpoint API functions for Azure. 
- [ ] Run the data from the tools through data model. 
- [x] Create bing search function
- [ ] Create "subscription" based access to the apis. 
- [ ] How to store credentials securely.

# TODO: Ranu: Task graph management
- If the graph exists, do not overwrite.  Ask the user if the old one should be used.
- Make sure that the names are descriptive.
- When a new task starts it should have a new name and new conversations to be attached to it.
- Work on the palnner to add new tasks anytime.

# TODO: Vivek: LLM Research
- Sampling
- Showing research
- Adding system instruction

# TODO: Categorization template:
- Create a template for categorization and make sure it works well.

# TODO: Better layout for templates
- When a conversation starts, provide templates as cards with images and information for users to select.

# TODO: Menu
- Hamburger when the menu collapses.
- Add Parent to the menu bar.
- Change color of the menu bar when we go to different levels.

# TODO:
- Send errors back to LLM fix.
- Remove admin for non server users.
# FOR ANOTHER DAY: NAVIGATION FIXES
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
import yaml

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
        st.code(msg)
        content = ""
        # Some tools return a key called res_dict.  Parse it here.
        if 'res_dict' in msg:
            res_dict = msg['res_dict']
            content = res_dict.get('content', res_dict.get('user_message', ''))
        # LLMs return a dict, but the content is typically json
        # Parse the content key, which is the json.
        elif msg.get('content', '').strip().startswith('{'):
            res_dict = json.loads(msg['content'])
            content = res_dict.get('content', res_dict.get('user_message', ''))
        else:
            res_dict = {}
            content = msg.get('content', '')
        
        if content:
            if msg['role'] in ['user', 'assistant']:

                with st.chat_message(msg['role']):
                    st.markdown(content.replace('\n', '\n\n'))
            # TODO: REMOVE SYSTEM MESSAGES AFTER FIXING BUGS
            if msg['role'] == 'system':
                st.info(content)        
        else:
            st.code(res_dict)
        
        if "tool_name" in res_dict:
            # st.success(f"Tool name: {res_dict['tool_name']}")
            with st.spinner("Running tool..."):
                manage_tool_interaction(res_dict, from_llm=False)
    return None

def manage_llm_interaction():

    planning = st.session_state.planning
    tg = st.session_state.task_graph
    m = tg.messages
    model = planning.default_model
    if st.session_state.current_task == 'planning':
        system_instruction = planning.get_system_instruction()
        # If there are templates, use it.
        if tg.templates:
            template_info = "The user has selected a canned template that can help with planning.  See the details below."
            for template_name, template in tg.templates.items():
                template_info += f"\n\nTemplate name: {template_name}"
                template_info += f"\nTemplate description: {template}\n\n"
            template_info += "Please use the information above to help with planning."
            system_instruction += f"\n\n{template_info}"
                
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
    
    HERE IS THE INFORMATION ABOUT THE TASK GRAPH:
    TASK GRAPH NAME: {task_name}
    OBJECTIVE: {task_objective}
    LIST OF SUBTASKS:
    {task_md}
    """
    extractors = Extractors()
    return extractors.remove_indents_in_lines(task_info)

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
    # If planning is in session state, update the task description
    else:
        planning = st.session_state.planning
        planning.task_description = get_task_graph_details()


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
        # When we get the tool result, set the delete task for tool
        del st.session_state['task_for_tool']
        st.error(f"Args for tools: {args_for_tool}")
        st.sidebar.code(f'Tool result: {tool_result}')
        # TODO: Some tools like search need to consume the tool results.
        # Others like navigator need not.  Create a system to pass to the
        # correct task. 
        if isinstance(tool_result, str):
            tool_result = {'content': tool_result}

        # Check if the the task is done and can be transferred to orchestration.

        st.sidebar.error("looking at tool result")
        if from_llm:
            # Add the tool result to the task graph
            # TODO: SHOLD WE UPDATE THE TASK GRAPH HERE DURING A RERUN? 
            tg = st.session_state.task_graph
            tg.update_task(
                task_name=st.session_state.current_task,
                other_attributes=tool_result
                )
            if tool_result.get('task_finished', False) == True:
                finish_tasks(tool_result)
            else:
                st.session_state.ask_llm = True
    
            content = tool_result.get('content', '')
            if content:
                # Add this to the agent's messages
                st.session_state.task_graph.messages.set_message(
                    role='user', 
                    content=content, 
                    created_by=st.session_state.current_task, 
                    created_for=st.session_state.current_task
                    )

    return None

def init_chat():
    """
    Initiate some key variables for the chat
    """
    if st.sidebar.button("New chat"):
        st.session_state.task_graph = TaskGraph()
        st.session_state.current_task = 'planning'
        st.session_state.ask_llm = True
        if 'task_for_tool' in st.session_state:
            del st.session_state['task_for_tool']
    if st.sidebar.button("Stop LLM"):
        st.session_state.ask_llm = False
    if 'task_graph' not in st.session_state:
        st.session_state.task_graph = TaskGraph()
    add_planning_to_session_state()
    tg = st.session_state.task_graph
    tg.messages.chat_input_method(task_name=st.session_state.current_task)
    st.sidebar.info(f"Ask llm: {st.session_state.ask_llm}\n\nCurrent task: {st.session_state.current_task}")
    display_messages()


def post_llm_processes():
    tg = st.session_state.task_graph
    next_task = tg.get_next_task()
    if next_task:
        run_next_task(tg, next_task)
    else:
        show_templates(tg)
    return None

def run_next_task(tg, next_task):
    """
    Get the next task and display it
    """    
    if st.button(f"Start task {next_task}"):
        st.session_state.ask_llm = True
        tg.send_to_planner = False
        st.session_state.current_task = next_task
        the_task = tg.graph.nodes[next_task]['task']
        si = the_task.get_system_instruction()
        st.code(si)
        st.markdown(the_task.task_description)
        st.rerun()

def show_templates(tg):
    """
    Show task templates if there are no
    messages in the conversation

    Parameters:
    tg (object): The task generator object.

    Returns:
    None
    """
    # See if there are no messages
    with st.sidebar.expander("Load templates & past work", expanded=True):
        if not tg.messages.get_all_messages() and st.session_state.selected_node == 'HOME':
            # DL version
            # tg._load_from_file()
            # json version
            tg._load_from_json()
            load_templates()
            if tg.templates:
                st.sidebar.info(f"{len(tg.templates)} templates loaded.")
    return None

def load_templates():

    # Open templates.yml file
    with open('templates.yml', 'r') as f:
        templates = yaml.safe_load(f)

    # Let the user select a template, with "SELECT" as the default
    template_names = st.multiselect('Select a template', list(templates.keys()))
    
    # If the user selects a template, show the description.
    for template_name in template_names:
        st.info(templates[template_name]['description'])
    

    # If the user clicks on the button, load the template
    if st.button("Load templates"):
        tg = st.session_state.task_graph
        for template_name in template_names:
            template = templates[template_name]
            tg.templates[template_name] = template
    
    return None

def chat():

    init_chat()
    tg = st.session_state.task_graph
    

    # Check if any task has been allocated for a tool.
    # If yes, run it before we get to the ask llm loop.
    if 'task_for_tool' in st.session_state:
        res_dict = st.session_state.task_for_tool
        with st.spinner("Running tool..."):
            manage_tool_interaction(res_dict, from_llm=True, run_tool=True)

    # Show the system instruction for the current task if it exists
    if st.session_state.current_task == 'planning':
        si = st.session_state.planning.get_system_instruction()
        # st.sidebar.warning(si)

    if st.session_state.ask_llm:
        res = manage_llm_interaction()
        res_dict = json.loads(res)
        # Find if LLM should be invoked automatically
        # and next action if task is finished
        try:
            set_next_actions(res_dict)
        except Exception as e:
            # Add the errror to the messages and ask LLM to fix it.
            st.session_state.task_graph.messages.set_message(
                role='user', 
                content=f"I got this error: {e}.\nPlease fix it.", 
                created_by=st.session_state.current_task, 
                created_for=st.session_state.current_task
                )
            st.session_state.ask_llm = True

        if 'tool_name' in res_dict:
            st.session_state.task_for_tool = res_dict

        # Save the graph to file, if it has a name
        # TODO: Make sure that we don't create a name that overwrites an existing one.
        if tg.name:
            # Save the graph to file
            # as .DL
            # tg._save_to_file()
            # as .json
            tg._save_to_json()
        st.rerun()
    # Display the agent name
    post_llm_processes()
    return None