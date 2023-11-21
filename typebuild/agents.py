"""
TODO:
- (Vivek) Graphs for tasks, not agents
- (Ranu) Convert tools to classes.  Each tool should have a run method & a visual method forh the UP.
    - (Ranu) Make sure that the agent knows how to use tools.
- (Ranu) Create a menu tool and agent.  Connect the agent to current projects, views, and research projects.
- (Ranu) Work on the LLM for reserch agent that creates the instruction first, runs samples, and then runs it on all text.

- (Ranu) Create a requests tool, separate that from the google search tool.
- (Ranu) Save messages by default, may be just save the graph.
- (later) Allow the user to retrieve not just the main thread but also subthreads, may be with expanders.

"""

import yaml
import os
import streamlit as st

from extractors import Extractors
from collections import namedtuple

class Agent:
    # Class variable to store message history

    def __init__(self, agent_name):        
        self.assets_needed = []
        self.messages = []
        self.tools = []
        self.parse_instructions(agent_name)
        return None
   

    def get_messages_with_instruction(self, system_instruction):
        """
        Returns a copy of the messages list with a new system instruction message added at the beginning.

        Args:
            system_instruction (str): The system instruction message to be added.

        Returns:
            list: A new list of messages with the system instruction message added at the beginning.
        """
        messages = self.messages.copy()
        messages.insert(0, {'role': 'system', 'content': system_instruction})
        return messages

    def get_system_instruction(self):
        """
        Returns the system instruction for the agent.

        The system instruction includes the tool definitions and a final message for the agent manager.

        Returns:
            str: The system instruction.
        """
        instructions = self.system_instruction
        # Add tools to the instruction
        instructions += self.get_tool_defs()

        instructions += """You can use tools multiple times and talk to the user.  
        When your job is done, pass it back to the orchestration with the final message.
        It should be valid json in this format:
        {"transfer_to_task": "orchestration", "final_message": "Your final message here"}
        """
        return instructions

    
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
        # Agents who are currently in action
        self.managed_tasks = {}
        self.task_tuple = namedtuple('Task', ['agent_name', 'agent', 'task_name', 'task_description'])
        # Agent names and descriptions of all available agents
        # All the agents available to this manager
        
        self.agent_descriptions = {}
        self.set_available_agent_descriptions(available_agents)
        
        # Only one agent can work at a time.  The default is the manager
        self.current_agent = 'agent_manager'
        

    def add_task(self, agent_name, task_name, task_description):
        """
        Add a new agent to the list of managed agents.

        Args:
            agent_name (str): The name of the agent to be added.

        Returns:
            None
        """
        if task_name not in self.managed_tasks:
            # Create an named tuple with the agent name, agent and description
            agent = Agent(agent_name)
            self.managed_tasks[task_name] = self.task_tuple(agent_name, agent, task_name, task_description)
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
    
    def get_system_instruction(self, task):
        """
        Add the agent name and description to the system instructions

        Args:
            agent_name (str): The name of the agent

        Returns:
            str: The system instruction with the agent name and description
        """
        if task in self.managed_tasks:
            instruction = self.managed_tasks[task].get_system_instruction()
        else:
            instruction = self.system_instruction
            # Add tools to the instruction
            instruction += self.get_tool_defs()
            instruction += "THE FOLLOWING IS A LIST OF AGENTS AVAILABLE.  DO NOT MAKE UP OTHER AGENTS.  CALL THEM BY THEIR NAME VERBATIM:\n"
            for agent_name, description in self.agent_descriptions.items():
                instruction += f"{agent_name}: {description}"
        return instruction

    def get_agent(self, task):
        """
        Returns the agent for the given agent_name

        Parameters:
        agent_name (str): The name of the agent to retrieve.

        Returns:
        agent: The agent object associated with the given agent_name. If the agent_name is not found in the managed_tasks dictionary, returns self.
        """
        if task in self.managed_tasks:
            agent = self.managed_tasks[task]
        else:
            agent = self
        return agent
    
    def remove_agent(self, task):
        if task in self.managed_tasks:
            del self.managed_tasks[task]

    def set_user_message(self, message):
        """
        Adds a user message to the chat.

        Args:
            message (str): The message content from the user.
        """
        current_task = st.session_state.current_task
        if current_task in self.managed_tasks:
            self.managed_tasks[current_task].messages.append({'role': 'user', 'content': message})
        
        # Always add the user message to the agent manager
        self.messages.append({'role': 'user', 'content': message})

    def set_assistant_message(self, message, task='orchestration'):
        """
        Adds an assistant message to the chat.

        Args:
            message (str): The message content from the assistant.
        """
        
        if task in self.managed_tasks:
            self.managed_tasks[task].agent.messages.append({'role': 'assistant', 'content': message})
        else:
            # TODO: Check if this works.  This is not a named tuple.  
            self.messages.append({'role': 'assistant', 'content': message})

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
            self.set_user_message(prompt)
            self.ask_llm = True
            st.session_state.ask_llm = True
            self.display_expanded = True
        return None

