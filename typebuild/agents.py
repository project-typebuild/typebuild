"""
TODO:
- (Vivek) Graphs for tasks, not agents

- (Ranu) Create a menu tool and agent.  
    - Connect the agent to current projects, views, and research projects.
- (Ranu) Work on the LLM for reserch agent that creates the instruction first, runs samples, and then runs it on all text.

- (Ranu) Create a requests tool, separate that from the google search tool.
- (Ranu) Save messages by default, may be just save the graph.
- (later) Allow the user to retrieve not just the main thread but also subthreads, may be with expanders.

"""

import time
import yaml
import os
import streamlit as st
import importlib

from extractors import Extractors
from collections import namedtuple, OrderedDict

class Agent:
    # Class variable to store message history

    def __init__(self, agent_name):        
        self.assets_needed = []
        self.messages = []
        self.tools = []
        self.parse_instructions(agent_name)
        return None
   

    def get_messages_with_instruction(self, system_instruction, prompt=None):
        """
        Returns a copy of the messages list with a new system instruction message added at the beginning.

        Args:
            system_instruction (str): The system instruction message to be added.

        Returns:
            list: A new list of messages with the system instruction message added at the beginning.
        """
        messages = self.messages.copy()
        messages.insert(0, {'role': 'system', 'content': system_instruction})
        if prompt:
            messages.append({'role': 'user', 'content': prompt})
        return messages

    def add_context_to_system_instruction(self):
        # TODO: DOCUMENT WHAT THIS DOES.  
        # Should we rename this so we understand what context means?
        if hasattr(self, 'get_data_from'):
            module_name = self.get_data_from.get('module_name', '')
            function_name = self.get_data_from.get('function_name', '')
            # import the function from the module and run it
            tool_module = importlib.import_module(module_name)
            tool_function = getattr(tool_module, function_name)
            data_for_system_instruction = tool_function()
        else:
            data_for_system_instruction = None

        # Take the data_for_system_instruction and replace the variables in the system_instruction
        instruction = self.system_instruction
        if data_for_system_instruction:
            for key, value in data_for_system_instruction.items():
                instruction = instruction.replace(f"{{{key}}}", value) # We are using triple curly braces to avoid conflicts with the f-strings
            
        
        return instruction

    def get_system_instruction_for_agent(self):
        """
        Returns the system instruction for the agent.

        The system instruction includes the tool definitions and a final message for the agent manager.

        Returns:
            str: The system instruction.
        """
        instruction = self.add_context_to_system_instruction()
        # Add tools to the instruction
        instruction += self.get_tool_defs()

        instruction += """You can use tools multiple times and talk to the user.
        If you need human input, you have to do two things:
        1. Set the ask_human flag to true.
        2. Pose a question in the output so that the user know to respond.

        When your job is done, set the task_finished flag to true.  Until then, task_finished should be false.

        In every turn, your response should only be a valid JSON in this format:
        {"output": output, "task_finished": boolean, "ask_human": boolean}

        You must return the result in the format above and the keys have to be verbatim. 
        """
        return instruction

    
    def parse_instructions(self, agent_name):
        """
        Parse the instructions for a given agent.

        Args:
            agent_name (str): The name of the agent.

        Returns:
            dict: The parsed instructions.

        Raises:
            FileNotFoundError: If no system instruction is found for the given agent.
        """
        
        path = os.path.join(os.path.dirname(__file__), 'agent_definitions', f'{agent_name}.yml')
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                instructions = yaml.load(f, Loader=yaml.FullLoader)
            # Parse the variables
            for key in instructions:
                setattr(self, key, instructions[key])
            return instructions
        else:
            raise FileNotFoundError(f'No system instruction found for {agent_name}.')


    def get_instance_vars(self):
        """
        Returns a dictionary containing all the instance variables of the object.
        """
        return self.__dict__


    def get_tool_defs(self):
        """
        Returns a formatted string containing the list of available tools and their docstrings.
        
        The method retrieves the docstrings of the tools specified in the `self.tools` attribute.
        It then formats the information into a well-structured string, including the tool name and its docstring.
        
        Returns:
            str: A formatted string with the list of available tools and their docstrings.
        """
        add_to_instruction = ""
        if self.tools:
            add_to_instruction += """THE FOLLOWING IS A LIST OF TOOLS AVAILABLE.  DO NOT MAKE UP OTHER TOOLS.  
            CALL THEM BY THEIR NAME VERBATIM.
            
            TO USE THE TOOL, RETURN A WELL FORMATTED JSON OBJECT WITH the tool_name and kwargs as keys.
            YOU CAN FIND THE DOCSTRING OF THE TOOLS BELOW:

            """
            tools = st.session_state.extractor.get_docstring_of_tools(self.tools)
            
            for tool in tools:
                add_to_instruction += f"===\n\n{tool}: {tools[tool]}\n\n"
            
        
        return st.session_state.extractor.remove_indents_in_lines(add_to_instruction)

    def available_tools(self):
        """
        Returns a dictionary of available tools.

        The dictionary contains the names of the available tools as keys and their respective docstrings as values.

        Returns:
            dict: A dictionary of available tools with their docstrings.
        """
        extractor = Extractors()
        tools = {}
        for file in os.listdir(os.path.join(os.path.dirname(__file__), 'tools')):
            if file.endswith('.py'):
                tools[file] = extractor.get_docstring_of_tool(file)
        return tools


    def send_response_to_chat_framework(self):
        """
        Sends all the chat messages or the final message to the chat framework
        """
        pass

    def respond(self):
        # Implement the response logic
        # This can involve using the default_model, temperature, and max_tokens
        # to generate a response based on the current message history and assets
        pass

class AgentManager(Agent):
    def __init__(self, agent_name, available_agents):
        super().__init__(agent_name)

        self.available_agents = available_agents
        # TODO: Create a graph of tasks rather than a dict of agents
        
        self.completed_tasks = []
        self.scheduled_tasks = []
        self.agent_name = "agent_manager"
        # Only one agent can work at a time.  The default is the manager
        self.current_task = 'orchestration'
        self.managed_tasks = {}
        self.objectives = OrderedDict()
        self.task_tuple = namedtuple('Task', ['agent_name', 'agent', 'task_name', 'prompt', 'status'])
        # Agent names and descriptions of all available agents
        # All the agents available to this manager
        
        self.agent_descriptions = {}
        self.set_available_agent_descriptions(available_agents)
        
    def get_messages(self):
        """
        Returns the messages in the agent manager followed by messages of the 
        current task in one list.

        Parameters:
        None

        Returns:
        list: The messages in the agent manager followed by messages of the current task in one list.
        """
        messages = self.messages.copy()
        if self.current_task != 'orchestration':
            task = self.get_task(self.current_task)
            agent_messages = task.agent.messages.copy()
            
            messages.extend(agent_messages)
        return messages

    def add_objective(self, objective_name, task_list):
        """
        Add a new objective to the objectives attribute, which is an ordered dictionary.

        Args:
            objective_name (str): The name of the objective to be added as the key
            task_list (list): A list of tasks that are part of the objective.  
                These are prompts that will be passed to the agent manager to initiate each task.

        Returns:
            None
        """
        # Note: The ideal thing to do is to have unique names for each task, so that they can be
        # completed at any time.  However, we are not doing that for now.
        self.objectives[objective_name] = {
            'scheduled': task_list, 
            'completed': [], 
            'status': 'not_started'}
        return None


    def complete_task(self, task_name):
        """
        Mark a task as completed.

        Args:
            task_name (str): The name of the task to be marked as completed.

        Returns:
            None
        """
        if task_name in self.scheduled_tasks:
            task_index = self.scheduled_tasks.index(task_name)
            removed = self.scheduled_tasks.pop(task_index)
            self.completed_tasks.append(removed)
        else:
            with st.spinner(f"Task {task_name} not found."):
                st.error(f"Task {task_name} not found.")
        
        return None

    def get_next_task(self):
        """
        Returns the next task to be completed
        and sets the current task.

        Returns:
            str: The name of the next task to be completed.
        """
        if len(self.scheduled_tasks) > 0:
            self.current_task = self.scheduled_tasks[0]
            st.session_state.current_task = self.current_task
            return self.scheduled_tasks[0]
        else:
            return None

    def set_available_agent_descriptions(self, available_agents):
        """
        Set the available agent descriptions.

        Args:
            available_agents (list): A list of available agent names.
        """
        for agent_name in available_agents:
            path = os.path.join(os.path.dirname(__file__), 'agent_definitions', f'{agent_name}.yml')
            with open(path, 'r') as f:
                instructions = yaml.load(f, Loader=yaml.FullLoader)

            description = instructions.get('description', '')
            if description:
                self.agent_descriptions[agent_name] = description
        return None
    
    def get_system_instruction(self, task_name):
        """
        Add the agent name and description to the system instructions

        Args:
            agent_name (str): The name of the agent

        Returns:
            str: The system instruction with the agent name and description
        """

        if task_name == 'orchestration':
            instruction = self.add_context_to_system_instruction()
            # Add tools to the instruction
            instruction += self.get_tool_defs()
            instruction += "THE FOLLOWING IS A LIST OF AGENTS AVAILABLE.  DO NOT MAKE UP OTHER AGENTS.  CALL THEM BY THEIR NAME VERBATIM:\n"
            for agent_name, description in self.agent_descriptions.items():
                instruction += f"- {agent_name}: {description}\n"
            if self.scheduled_tasks:
                scheduled_tasks = '- ' + '\n- '.join(self.scheduled_tasks)
                instruction += f"""The following are the scheduled tasks:
                {scheduled_tasks}
                Explain to the user what you are working on."""

        else:
            task = self.get_task(task_name)
            agent_name = task.agent_name
            agent = task.agent
            instruction = agent.get_system_instruction_for_agent()
        
        return instruction

    def get_agent(self, task_name):
        if task_name == 'orchestration':
            return self
        else:
            return self.managed_tasks[task_name].agent

    def get_task(self, task_name):
        """
        Returns the agent for the given agent_name

        Parameters:
        agent_name (str): The name of the agent to retrieve.

        Returns:
        agent: The agent object associated with the given agent_name. If the agent_name is not found in the managed_tasks dictionary, returns self.
        """
        if task_name in self.managed_tasks:
            task = self.managed_tasks[task_name]
            return task
        else:
            return None
    
    def remove_task(self, task):
        if task in self.managed_tasks:
            del self.managed_tasks[task]
        return None
    
    def set_task_status(self, task_name, status):
        if task_name in self.managed_tasks:
            task = self.managed_tasks[task_name]
            self.managed_tasks[task_name] = task._replace(status=status)
        return None


    def set_message(self, role, content, task='orchestration'):
        """
        Adds a user, assistant or system content to the chat.

        Args:
            content (str): The content to add.
        """
        current_task = self.current_task
        if current_task == 'orchestration':
            self.messages.append({'role': role, 'content': content})
            st.session_state.all_messages.append({'role': role, 'content': content, 'task': 'orchestration'})
        else:
            task = self.get_task(current_task)
            agent = task.agent
            agent_name = task.agent_name
            agent.messages.append({'role': role, 'content': content})
            st.session_state.all_messages.append({'role': role, 'content': content, 'task': agent_name})    
    
        return None



    def set_assistant_message(self, message, task='orchestration'):
        """
        Adds an assistant message to the chat.

        Args:
            message (str): The message content from the assistant.
        """
        if task != 'orchestration':
            agent = self.get_agent(task)
            agent.messages.append({'role': 'assistant', 'content': message})
        else:
            self.messages.append({'role': 'assistant', 'content': message})
        return None

    def chat_input_method(self):
        """
        Handles the input of chat messages.

        This method provides an input field for the user to enter their message.
        Upon receiving a message, it updates the messages list and sets the
        `ask_llm` flag to True.

        Returns:
            None
        """
        prompt = st.chat_input("Enter your message", key="chat_input")
        if prompt:
            self.set_message(role="user", content=prompt)
            self.ask_llm = True
            st.session_state.ask_llm = True
            self.display_expanded = True
        return None

