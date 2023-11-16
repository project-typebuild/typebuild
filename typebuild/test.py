import streamlit as st
from chat_framework import ChatFramework
from plugins.llms import get_llm_output

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
    if 'system_instruction' not in st.session_state:
        cf.set_system_message("Welcome to the test chat!")
    else:
        cf.set_system_message(st.session_state.system_instruction)
    cf.chat_input_method()
    cf.display_messages()
    
    if cf.ask_llm:
        res = get_llm_output(cf.messages)
        cf.set_assistant_message(res)
        cf.ask_llm = False
        st.rerun()

    return None