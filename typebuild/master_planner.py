"""
This file creates the script for the master planner
with different instructions at different stages of the process.
"""
import streamlit as st
import os
from glob import glob
from task import Task
from extractors import Extractors


# Instructions to create the task graph
instruction_before_task_graph = """Your first job is to create a task graph to help the user with their project.
    - First talk to the user to understand their objective.  
    - Once you understand, create one or more tasks to help the user achieve their objective.  
    - Most agents can do multiple steps in one task.  Understand their description and create more than one task only if necessary.
    - Then create a task graph to help the user achieve their objective.
To create a task graph, you should create a valid json in this format:
{
"type": "task_graph",
"name": "a detailed name for the task graph that the user can retrieve later.  Use all key details in name.",
"objective": "A detailed description of the user's objective that will be used by other agents in creating tasks.",
}
    """

create_task_general_instruction = """
Unless the user asks for it, keep the tasks minimal.
The output should be a list of valid json with an array of dicts.
The dicts should have the task_name, task_description, and agent_name.  
parent_task, add_before, and add_after are optional.  You can omit them or set them to null.
Upon creating the task list, set ask_llm to true if you need to ask the user for more information.
If the task is finished, set task_finished to true.  Else, set to false.

Use this format:
{
"task_list": [array of task dicts],
"ask_llm": bool,
"task_finished": bool
}
task dicts should be in this format:
{
"task_name": "name of the task",
"task_description": "description of the task",
"agent_name": "name of the agent that will perform the task",
"parent_task": "Set a parent if this task depends on the completion of another task, and needs its input.  Else, set to null",
"add_before": "name of the task that this task should be added before.  If this is the first task, set this to null",
"add_after": "name of the task that this task should be added after.  If this is the last task, set this to null",
} 

  Some tasks need data.  If a file and column are already selected, pass that information. Else work with the data_agent to select the data.
"""

# Instructions to create tasks after the task graph is created but any tasks has been created
instruction_first_tasks = """The task graph contains no task yet. You should create tasks to help the user achieve their objective.
  First think of all the tasks needed to for this project.
  Then generate a list of tasks to help the user achieve their objective. The list should be in the order in which tasks should be performed."""

instruction_first_tasks += create_task_general_instruction

# Instructions to add tasks
instruction_additonal_tasks = """The task graph already contains tasks given above.
Based on the conversation, if you assess that more tasks are needed, add them to the task graph."""

instruction_additonal_tasks += create_task_general_instruction




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
    Create the master planner and add it to the session state
    """
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
    planning = Task(
            task_name='planning', 
            task_description="To be set by update master planner function",
            agent_name='master_planner',
            available_agents=agent_names,
            )

    # The system instruction should change for the task graph
    # based on the situation.  It is added dynamically. 
    planning.system_instruction = instruction_before_task_graph
    st.session_state.planning = planning

    st.session_state.current_task = 'planning'
    return None


def update_master_planner():
    """
    Update the description and instructions for the master planner
    based on the current state of the task graph.
    There are three states:
    1. No task graph exists
    2. Task graph exists but no tasks have been added
    3. Task graph exists and tasks have been added, and more tasks may be added
    """
    planning = st.session_state.planning
    tg = st.session_state.task_graph
    # If there is no task graph name, the task graph has not been created
    if not tg.name:
        desc = "\nWe do not know the user's objective yet and the task graph has not been created.\n"
        planning.task_description = desc
        planning.system_instruction = instruction_before_task_graph
    
    # If the only node in the task graph is the root, no tasks have been added
    # Add tasks to the task graph
    elif tg.graph.number_of_nodes() == 1:
        # Since there is just the root node, there are no tasks
        # The graph details will fetch the task graph name and objective
        desc = get_task_graph_details()
        planning.task_description = desc
        # If any template has been selected, add that
        if st.session_state.task_graph.templates:
            # Update the template information
            template_info = "The user has selected a canned template that can help with planning.  Follow these instructions very carefully to create tasks for the objective:\n"  
            for template_name, template in st.session_state.task_graph.templates.items():
                template_info += f"\nINSTRUCTIONS FOR PLANNING: {template}\n\n"

            planning.task_description = desc + template_info
        planning.system_instruction = instruction_first_tasks

    # Tasks exist in the task graph
    # We should allow for new tasks to be added
    else:
        # Get all the tasks that exist
        desc = get_task_graph_details()
        planning.task_description = desc
        planning.system_instruction = instruction_additonal_tasks
    return None

def create_master_planner():
    """
    Add the planner to the session state, and update the task description and system instruction
    based on the current state of the task graph
    """
    if 'planning' not in st.session_state:
        add_planning_to_session_state()

    # If planning is in session state, update the task description
    else:
        update_master_planner()
    return None

def get_planner_instructions():
    """
    Get the instructions for the master planner
    """
    planning = st.session_state.planning
    system_instruction = planning.get_system_instruction()
    # If there are templates, use it.
    tg = st.session_state.task_graph
    if tg.templates:
        template_info = "The user has selected a canned template that can help with planning.  See the details below."
        for template_name, template in tg.templates.items():
            template_info += f"\n\nTemplate name: {template_name}"
            template_info += f"\nTemplate description: {template}\n\n"
        template_info += "Please use the information above to help with planning."
        system_instruction += f"\n\n{template_info}"
    # Store the system instruction in the session state for us to understand what 
    # information the planner was given
    st.session_state.planner_instructions = system_instruction
    return system_instruction