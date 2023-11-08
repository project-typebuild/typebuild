import streamlit as st
import pandas as pd
import altair as alt

# Create a random altair chart
def show_chart():
    df = pd.DataFrame(
        [[1, 5, 2], [2, 4, 3], [3, 3, 4], [4, 2, 5], [5, 1, 6]],
        columns=['a', 'b', 'c'])
    c = alt.Chart(df).mark_circle().encode(
        x='a', y='b', size='c', color='c', tooltip=['a', 'b', 'c'])

    return c

class ChatFramework:
    ask_llm = False
    # Create a container for the chat messages
    messages = []
    display_expanded = False
    
    def __init__(self):
        return None

    def set_user_message(self, message):
        self.messages.append({'role': 'user', 'content': message})

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
            self.messages.append({'role': 'user', 'content': prompt})
            # Set ask llm to true
            self.ask_llm = True
            self.display_expanded = True
        return None
    
    def display_chart(self, chart_object):
        # Close the expander
        if st.checkbox("Show chart"):
            self.display_expanded = False
            st.altair_chart(chart_object)
            st.rerun()
        return None


if 'a' not in st.session_state:
    a = ChatFramework()
    st.session_state['a'] = a
else:
    a = st.session_state['a']

a.chat_input_method()
a.display_messages()
a.display_chart(chart_object=show_chart())

