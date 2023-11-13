import streamlit as st
st.set_page_config(layout="centered")
st.sidebar.title("Graphical Menu")
import pandas as pd
import altair as alt
from test import test_main

class ChatFramework:
    ask_llm = False
    # Create a container for the chat messages
    messages = []
    display_expanded = False
    available_methods = ['show_chart', 'chat_input_method', 'display_messages']
    show_methods = ['show_chart', 'chat_input_method', 'display_messages']

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

    # Create a random altair chart
    def show_chart(self):
        df = pd.DataFrame(
            [[1, 5, 2], [2, 4, 3], [3, 3, 4], [4, 2, 5], [5, 1, 6]],
            columns=['a', 'b', 'c'])
        c = alt.Chart(df).mark_circle().encode(
            x='a', y='b', size='c', color='c', tooltip=['a', 'b', 'c'])
        st.altair_chart(c)

        return None

    def dynamic_menu(self):
        for method in self.show_methods:
            getattr(self, method)()
        # For hidden methods, give a button to toggle them on the sidebar
        for method in self.available_methods:
            if method not in self.show_methods:
                st.info(self.show_methods)
                if st.sidebar.button(f"Open {method}"):
                    self.add_to_menu(method)
        # For shown methods, give a button to toggle them off the sidebar
        for method in self.show_methods:
            if method in self.available_methods:
                if st.sidebar.button(f"Close {method}"):
                    self.remove_from_menu(method)
        return None

    def remove_from_menu(self, method):
        if method in self.show_methods:
            self.show_methods.remove(method)
            st.rerun()
    
    def add_to_menu(self, method):
        if method not in self.show_methods:
            self.show_methods.append(method)
            st.rerun()

if 'a' not in st.session_state:
    a = ChatFramework()
    st.session_state['a'] = a
else:
    a = st.session_state['a']

if 'should_rerun' not in st.session_state:
    st.session_state['should_rerun'] = False

st.sidebar.success(st.session_state.should_rerun)

# a.dynamic_menu()
# if st.button("Remove chart"):
#     a.remove_from_menu('show_chart')

from graphical_menu import GraphicalMenu, menu_edges_data

if 'menu' not in st.session_state:
    menu = GraphicalMenu()
    st.session_state['menu'] = menu
    menu.add_edges(menu_edges_data, 'success')
    
else:
    menu = st.session_state['menu']
menu.create_menu()

test_main()
# Show the menu edges
# st.json(st.session_state.menu.menu_edges)