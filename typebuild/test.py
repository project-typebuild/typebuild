import streamlit as st
from chat_framework import ChatFramework

def test_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    test_menu_items = [
        ['HOME', 'Chat', 'chat'],
    ]    
    menu.add_edges(test_menu_items, 'test')
    return None

def chat():
    if 'test_cf' not in st.session_state:
        st.session_state.test_cf = ChatFramework()
    cf = st.session_state.test_cf
    cf.set_system_message("Welcome to the test chat!")
    cf.chat_input_method()
    cf.display_messages()
    return None