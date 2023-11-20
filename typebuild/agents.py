import importlib
import inspect
import yaml
import os
import streamlit as st
from helpers import remove_indents_in_lines

def get_docstring_of_tool(tool, function_name='tool_main'):
    """
    Return the docstring of the file as a dict.

    Parameters:
    - file: The file to retrieve the docstring from.
    - function_name: The name of the function to retrieve the docstring from. Default is 'tool_main'.

    Returns (str):
    - The docstring of the file.
    """
    # Import the module
    module_name = f"tools.{tool}"
    module = importlib.import_module(module_name)
    # Get the function object from the module
    function = getattr(module, function_name, None)
    if function is None:
        return f"No function named '{function_name}' found in 'tools.{tool}'."

    # Get the docstring
    docstring = inspect.getdoc(function)
    return docstring if docstring else "No docstring available."


def get_docstring_of_tools(tool_list):
    """
    Given the list of tools, get their docstrings.

    Parameters:
    - tool_list: A list of tools to get the docstrings of.  This should be the name of the python file in the "tools" directory.

    Returns (dict):
    - A dictionary of the tool name and the docstring of the tool.
    """
    tools = {}
    for tool in tool_list:
        file = os.path.join(os.path.dirname(__file__), 'tools', f"{tool}.py")
        tools[tool] = get_docstring_of_tool(tool)
    return tools


def available_tools():
    """
    Look at the tools folder to see what tools are available for agents to use.
    Return the file name and the doc string of the file as a dict.
    """
    tools = {}
    for file in os.listdir(os.path.join(os.path.dirname(__file__), 'tools')):
        if file.endswith('.py'):
            tools[file] = get_docstring_of_tool(file)
    return tools


class Agent:
    # Class variable to store message history

    def __init__(self, agent_name):        
        self.assets_needed = []
        self.messages = []
        self.tools = []
        self.parse_instructions(agent_name)
        return None
   

    def get_messages_with_instruction(self, system_instruction):
        messages = self.messages.copy()
        messages.insert(0, {'role': 'system', 'content': system_instruction})
        return messages

    def get_system_instruction(self):
        """
        Returns the system instruction
        """
        instructions = self.system_instruction
        # Add tools to the instruction
        instructions += self.get_tool_defs()

        instructions += """You can use tools multiple times and talk to the user.  
        When your job is done, pass it back to the agent_manager with the final message.:
        <<<agent_manager: final_message>>>
        """
        return instructions

    
    def parse_instructions(self, agent_name):
        """
        There is a file called system_instruction/{agent_name}.yml.
        Parase the variables in it and create them as instance variables.
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
        Returns a dictionary of instance variables
        """
        return self.__dict__

    def get_tool_defs(self):
        """
        Find the list of tools available for this agent.
        Get the docstring of each tool to add to the system instruction.
        """
        add_to_instruction = ""
        if self.tools:
            add_to_instruction += """THE FOLLOWING IS A LIST OF TOOLS AVAILABLE.  DO NOT MAKE UP OTHER TOOLS.  
            CALL THEM BY THEIR NAME VERBATIM.
            
            TO USE THE TOOL, RETURN A WELL FORMATTED JSON OBJECT WITH the tool_name and kwargs as keys.
            YOU CAN FIND THE DOCSTRING OF THE TOOLS BELOW:

            """
            tools = get_docstring_of_tools(self.tools)
            
            for tool in tools:
                add_to_instruction += f"===\n\n{tool}: {tools[tool]}\n\n"
            
        
        return remove_indents_in_lines(add_to_instruction)

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
        self.managed_agents = {}
        self.available_agents = available_agents
        self.current_agent = 'agent_manager'
        self.agent_descriptions = {}
        self.set_available_agent_descriptions()

    def add_agent(self, agent_name, agent):
        self.managed_agents[agent_name] = agent

    def set_available_agent_descriptions(self):
        for agent_name in self.available_agents:
            path = os.path.join(os.path.dirname(__file__), 'agent_definitions', f'{agent_name}.yml')
            with open(path, 'r') as f:
                instructions = yaml.load(f, Loader=yaml.FullLoader)

            description = instructions.get('description', '')
            if description:
                self.agent_descriptions[agent_name] = description
        return None
    
    def get_system_instruction(self, agent_name):
        """
        Add the agent name and description to the system instructions
        """
        if agent_name in self.managed_agents:
            instruction = self.managed_agents[agent_name].get_system_instruction()
        else:
            instruction = self.system_instruction
            # Add tools to the instruction
            instruction += self.get_tool_defs()
            instruction += "THE FOLLOWING IS A LIST OF AGENTS AVAILABLE.  DO NOT MAKE UP OTHER AGENTS.  CALL THEM BY THEIR NAME VERBATIM:\n"
            for agent_name, description in self.agent_descriptions.items():
                instruction += f"{agent_name}: {description}"
        return instruction

    def get_agent(self, agent_name):
            """
            Returns the agent for the given agent_name
            """
            if agent_name in self.managed_agents:
                agent = self.managed_agents[agent_name]
            else:
                agent = self
            return agent
    
    def remove_agent(self, agent_name):
        if agent_name in self.managed_agents:
            del self.managed_agents[agent_name]

    def set_user_message(self, message):
        """
        Adds a user message to the chat.

        Args:
            message (str): The message content from the user.
        """
        current_agent = st.session_state.ask_agent
        if current_agent in self.managed_agents:
            self.managed_agents[current_agent].messages.append({'role': 'user', 'content': message})
        
        # Always add the user message to the agent manager
        self.messages.append({'role': 'user', 'content': message})

    def set_assistant_message(self, message, agent='agent_manager'):
        """
        Adds an assistant message to the chat.

        Args:
            message (str): The message content from the assistant.
        """
        
        if agent in self.managed_agents:
            self.managed_agents[agent].messages.append({'role': 'assistant', 'content': message})
        else:
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

