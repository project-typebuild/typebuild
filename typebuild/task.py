import yaml
import os
import streamlit as st
import importlib

from extractors import Extractors

class Task:
    """
    A class for tasks.  Each task is assigned to an agent.
    Some agents can deletgate tasks to other agents. In such cases,
    they know a list of available agents.
    """

    def __init__(self, task_name, agent_name, task_description, available_agents=[]):
        self.task_name = task_name
        agent_instructions = self._parse_instructions(agent_name)
        self.task_description = task_description
        # Some agents have access to tools.  They are specified in agent definitions.
        self.tools = []
        
        # Some agents can delegate tasks to other agents.
        # This dict contains the names and descriptions of the available agents.
        self.agent_descriptions = {}
        self._set_available_agent_descriptions(available_agents)

        return None
   

    def _replace_placeholder_with_actual_values(self):
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

    
    def _parse_instructions(self, agent_name):
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


    def _get_tool_defs(self):
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

    # TODO: Deprecate? This is not used anywhere.
    def _available_tools(self):
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

    def _set_available_agent_descriptions(self, available_agents):
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
    
    def get_system_instruction(self):
        """
        Add the agent name and description to the system instructions

        Args:
            agent_name (str): The name of the agent

        Returns:
            str: The system instruction with the agent name and description
        """

        instruction = self._replace_placeholder_with_actual_values()
        # Add tools to the instruction
        instruction += self._get_tool_defs()
        
        # If this agent could delegate, add that information
        # to the instruction.
        if self.agent_descriptions:
            instruction += "THE FOLLOWING IS A LIST OF AGENTS AVAILABLE.  DO NOT MAKE UP OTHER AGENTS.  CALL THEM BY THEIR NAME VERBATIM:\n"
            for agent_name, description in self.agent_descriptions.items():
                instruction += f"- {agent_name}: {description}\n"

        instruction += """Your response must always be a valid json.  It could contain different keys based on the task.
        The following keys should always be present in the response:
        - user_message: Your message to the user
        - ask_human: boolean.  If True, the agent will ask for human intervention.        
        """        
        if self.task_name != 'orchestration':
            instruction += "\n- task_finished: boolean"
        return instruction


