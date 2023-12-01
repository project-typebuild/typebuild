"""
A class for messages.
"""

from collections import namedtuple
import streamlit as st
import time

class Messages:
    """
    A class to hold the messages for one task graph.
    """
    def __init__(self, task_name):
        self.task_name = task_name
        self.messages = []
        self.message_tuple = namedtuple('message_tuple', ['content', 'role', 'created_by', 'created_for', 'ts'])

    def set_message(self, content, role, created_by, created_for):
        self.messages.append(self.message_tuple(content, role, created_by, created_for, time.time()))
        return None
    
    def get_messages_for_task(self, task_name):
        return [{'role': m.role, 'content': m.content} for m in self.messages if m.created_for == task_name]
    
    def get_messages_by_task(self, task_name):
        return [m for m in self.messages if m.created_by == task_name]
    
    def get_all_messages(self):
        return self.messages
    
    def chat_input_method(self, task_name=None):
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
            if not task_name:
                task_name = st.session_state.current_task
            self.set_message(role="user", content=prompt, created_by="user", created_for=task_name)
            self.ask_llm = True
            st.session_state.ask_llm = True
            self.display_expanded = True
            st.session_state.all_messages.append({'role': 'user', 'content': prompt})
        return None

    def get_messages_with_instruction(self, system_instruction, created_for=None, prompt=None):
        """
        Returns a copy of the messages list with a new system instruction message added at the beginning.

        Args:
            system_instruction (str): The system instruction message to be added.
            prompt (str, optional): The prompt to be added at the end of the list. Defaults to None.

        Returns:
            list: A new list of messages with the system instruction message added at the beginning.
        """
        messages = self.messages.copy()
        # Get role and content from the named tuple as a dict
        if created_for:
            messages = [{'role': m.role, 'content': m.content} for m in messages if m.created_for == created_for]
        else:
            messages = [{'role': m.role, 'content': m.content} for m in messages]

        # Add the system instruction message at the beginning
        messages.insert(0, {'role': 'system', 'content': system_instruction})

        if prompt:
            messages.append({'role': 'user', 'content': prompt})
        return messages
