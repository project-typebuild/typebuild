import streamlit as st
import pandas as pd
import altair as alt

class ChatFramework:
    """A class to manage the chat framework for TypeBuild.
    
    This class enables the management of different chats for various projects.
    Each instance of the class holds the data for a specific chat, including messages
    and display settings.
    """

    def __init__(self):
        """
        Initializes the ChatFramework instance.

        Attributes:
            ask_llm (bool): Determines if the Large Language Model (LLM) should be called at the end of the loop.
            messages (list): A container for storing chat messages.
            display_expanded (bool): Flag to expand or collapse the display container.
        """
        self.ask_llm = False
        self.messages = []
        self.display_expanded = False

    def set_user_message(self, message):
        """
        Adds a user message to the chat.

        Args:
            message (str): The message content from the user.
        """
        self.messages.append({'role': 'user', 'content': message})

    def set_assistant_message(self, message):
        """
        Adds an assistant message to the chat.

        Args:
            message (str): The message content from the assistant.
        """
        self.messages.append({'role': 'assistant', 'content': message})


    def display_messages(self):
        """
        Displays the messages in the chat.

        Utilizes Streamlit's expander and chat_message for displaying messages.
        This method iterates through the messages list and displays each one based
        on the role (user, assistant, system).

        Returns:
            None
        """
        if self.messages:
            with st.expander("View chat", expanded=self.display_expanded):
                for i, msg in enumerate(self.messages):
                    if msg['role'] in ['user', 'assistant']:
                        the_content = msg['content']
                        with st.chat_message(msg['role']):
                            st.markdown(the_content)
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
            self.set_user_message(prompt)
            self.ask_llm = True
            st.session_state.ask_llm = True
            self.display_expanded = True
        return None

    def get_messages_with_instruction(self, system_instruction):
        messages = self.messages.copy()
        messages.insert(0, {'role': 'system', 'content': system_instruction})
        return messages