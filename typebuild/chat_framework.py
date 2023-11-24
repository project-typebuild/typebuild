import streamlit as st

class ChatFramework:

    def __init__(self):
        # Create class variable ask_llm
        self.ask_llm = False
        # Create a container for the chat messages
        self.messages = []
        self.display = st.status("View chat")

    def chat_input(self):
        prompt = st.chat_input("Enter your message", key="chat_input")
        if prompt:
            self.messages.append({'role': 'user', 'content': prompt})
            # Set ask llm to true
            self.ask_llm = True
        return None

    def display_messages(self):
        # Display the user and assistant messages
        # TODO: Perhaps I should print the messages from the agents using update?
        with st.status("View chat") as display:
            for i, msg in enumerate(st.session_state[self.chat_key]):
                if msg['role'] in ['user', 'assistant']:
                    the_content = msg['content']
                    with st.chat_message(msg['role']):
                        st.markdown(the_content)
        return None

