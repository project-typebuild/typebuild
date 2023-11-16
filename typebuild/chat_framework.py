import streamlit as st
import pandas as pd
import altair as alt

class ChatFramework:
    """A class to manage the chat framework
    TypeBuild could have different chats going on for different projects, etc.
    Each instance will hold the data for that particular chat.
    """
    def __init__(self):
        
        # At the end of the loop, this determines if the LLM will be called
        self.ask_llm = False
        
        # Create a container for the chat messages
        self.messages = []
        
        # Expand or collaps the display container
        self.display_expanded = False

    def set_user_message(self, message):
        self.messages.append({'role': 'user', 'content': message})

    def set_assistant_message(self, message):
        self.messages.append({'role': 'assistant', 'content': message})

    def set_system_message(self, message):
        self.messages.append({'role': 'system', 'content': message})

    def display_messages(self):
        # Display the user and assistant messages
        # TODO: Perhaps I should print the messages from the agents using update?
        if self.messages:
            with st.expander("View chat", expanded=self.display_expanded):
                for i, msg in enumerate(self.messages):
                    if msg['role'] in ['user', 'assistant']:
                        the_content = msg['content']
                        with st.chat_message(msg['role']):
                            st.markdown(the_content)
        return None
        
    def chat_input_method(self):
        prompt = st.chat_input("Enter your message", key="chat_input")
        if prompt:
            self.set_user_message(prompt)
            # Set ask llm to true
            self.ask_llm = True
            self.display_expanded = True
        return None


