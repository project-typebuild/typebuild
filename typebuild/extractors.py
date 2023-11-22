import streamlit as st
import os
import importlib
import inspect
import re
import json


class Extractors:

    """
    This class contains functions to extract information from the response from the LLM.

    Available functions:
    - remove_indents_in_lines (response)
    - extract_dict_from_response (response)
    - extract_json_from_response (response)
    - extract_list_of_dicts_from_string (response)
    - extract_agent_name_and_message (response)
    - extract_message_to_agent (response)
    - extract_func_call_info (response)
    - extract_code_from_response (response)
    - extract_modified_user_requirements_from_response (response)
    - get_docstring_of_tool (tool, function_name='tool_main')
    - get_docstring_of_tools (tool_list)

    """
    
    def __init__(self):
        return None

    def remove_indents_in_lines(self, response):
        """
        Remove leading and trailing whitespace from each line in the given response.

        Args:
            response (str): The response to process.

        Returns:
            str: The response with leading and trailing whitespace removed from each line.
        """
        lines = response.split('\n')
        lines = [i.strip() for i in lines]
        return '\n'.join(lines)

    def extract_dict_from_response(self, response):
        """
        Extracts a dictionary from the given response.

        Args:
            response (dict or list or str): The response to extract the dictionary from.

        Returns:
            dict: The extracted dictionary.

        """
        if isinstance(response, dict):
            return response
        elif isinstance(response, list):
            return response
        elif isinstance(response, str):
            response = response.strip()
            try:
                start = response.index('{')
                end = response.rindex('}') + 1
                dict_str = response[start:end]
                return json.loads(dict_str)
            except ValueError:
                return {}
        else:
            return {}


    def extract_json_from_response(self, response):
        """
        Returns the JSON from the response from LLM.
        In the prompt to JSON, we have asked the LLM to return the JSON inside triple backticks.

        Args:
        - response (str): The response from LLM

        Returns:
        - json_dict (dict): A dictionary containing the parsed JSON
        """

        pattern = r"```json([\s\S]*?)```"
        matches = re.findall(pattern, response)
        if len(matches) > 0:
            json_str = '\n'.join(matches)
            try:
                json_dict = json.loads(json_str)
                return json_dict
            except json.JSONDecodeError:
                # Handle JSON decoding error
                return None
        else:
            return None

    def extract_list_of_dicts_from_string(self, response):
        """
        Extracts a list of dictionaries from a string.

        Args:
            response (str): The string containing the list of dictionaries.

        Returns:
            list: A list of dictionaries extracted from the string.

        """
        # Remove the new line characters
        response = response.replace('\n', ' ')

        # assuming `response` is the string with the list of dicts
        start_index = response.index('[') 
        end_index = response.rindex(']') + 1
        list_of_dicts_str = response[start_index:end_index]

        return eval(list_of_dicts_str)


    def extract_agent_name_and_message(self,response):
        """
        Extracts the agent name, instruction, and the rest of the response from a given response string.

        Args:
            response (str): The response string containing the agent name and instruction.

        Returns:
            tuple: A tuple containing the agent name, instruction, and the rest of the response.

        Example:
            >>> response = "<<<Agent1: Do this instruction>>> Some other text"
            >>> extract_agent_name_and_message(response)
            ('Agent1', 'Do this instruction', ' Some other text')
        """
        pattern = r"<<<([\s\S]*?):([\s\S]*?)>>>"
        matches = re.findall(pattern, response)
        if len(matches) == 1:
            agent_name = matches[0][0].strip()
            instruction = matches[0][1].strip()
            rest_of_response = response.replace(f'<<<{agent_name}:{instruction}>>>', '')
        else:
            agent_name = None
            instruction = None
            rest_of_response = response
        return agent_name, instruction, rest_of_response

    def extract_destination_edge(self, response):
        """
        Extracts the destination edge from the response.

        The destination edge is the edge that the agent manager should traverse to
        after the agent is done with the current edge.

        Args:
            response (str): The response from the LLM.

        Returns:
            str: The destination edge.
        """
        pattern = r"<<<([\s\S]*?)>>>"
        matches = re.findall(pattern, response)
        if len(matches) == 1:
            destination_edge = matches[0].strip()
        else:
            destination_edge = None
        return destination_edge

    def extract_message_to_agent(self, response):
        """
        Extracts the message to the agent from the response.
        This is found within <<< and >>>.
        There will be at least one set of triple angle brackets
        for this function to be invoked.

        Parameters:
        - response (str): The response string from which to extract the message.

        Returns:
        - message_to_agent (str): The extracted message to the agent.
        """
        pattern = r"<<<([\s\S]*?)>>>"
        matches = re.findall(pattern, response)
        if len(matches) == 1:
            message_to_agent = matches[0].strip()
        else:
            message_to_agent = '\n'.join(matches)
        
        # Add it to the session state
        st.session_state.message_to_agent = message_to_agent
        return message_to_agent

    def extract_func_call_info(self, response):
        """
        Extracts code or requirements from the given response.

        The LLM can return code or requirements in the content.  
        Ideally, requirements come in triple pipe delimiters, 
        but sometimes they come in triple backticks.

        Figure out which one it is and return the extracted code or requirements.

        Args:
            response (str): The response containing code or requirements.

        Returns:
            tuple: A tuple containing the extracted code or requirements and the corresponding function name.
        """
        # If there are ```, it could be code or requirements
        function_name = None
        if '```' in response:
            # If it's python code, it should have at least one function in it
            if 'def ' in response:
                extracted = self.extract_code_from_response(response)
                function_name = 'save_code_to_file'
            elif 'data_agent' in response:
                extracted = self.extract_modified_user_requirements_from_response(response)
                function_name = 'data_agent'
            elif 'json' in response:
                extracted = self.extract_json_from_response(response)
                function_name = ''
            # If it's not python code, it's probably requirements
            else:
                extracted = self.extract_modified_user_requirements_from_response(response)
                function_name = 'save_requirements_to_file'
        # If there are |||, it's probably requirements
        elif '|||' in response:
            extracted = self.extract_modified_user_requirements_from_response(response)
            function_name = 'save_requirements_to_file'
        else:
            extracted = None
        return extracted, function_name
                
    def extract_code_from_response(self,response):

        """
        Returns the code from the response from LLM.
        In the prompt to code, we have asked the LLM to return the code inside triple backticks.

        Args:
        - response (str): The response from LLM

        Returns:
        - matches (list): A list of strings with the code

        """

        pattern = r"```python([\s\S]*?)```"
        matches = re.findall(pattern, response)
        if len(matches) > 0:
            matches = '\n'.join(matches)
        else:
            matches = matches[0]
        return matches

    def extract_modified_user_requirements_from_response(self,response):
        
        """
        Returns the modified user requirements from the response from LLM. 
        In the prompt to modify, we have asked the LLM to return the modified user requirements inside triple pipe delimiters.

        Args:
        - response (str): The response from LLM

        Returns:
        - matches (list): A list of strings with the modified user requirements

        """
        if '|||' in response:
            pattern = r"\|\|\|([\s\S]*?)\|\|\|"
        if '```' in response:
            # It shouldnt have ```python in it
            pattern = r"```([\s\S]*?)```"

        matches = re.findall(pattern, response)
        # if there are multiple matches, join by new line
        if len(matches) > 0:
            matches = '\n'.join(matches)
        else:
            matches = matches[0]
        return matches

    
    def get_docstring_of_tool(self, tool, function_name='tool_main'):
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

    def get_docstring_of_tools(self,tool_list):
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
            tools[tool] = self.get_docstring_of_tool(tool)
        return tools
