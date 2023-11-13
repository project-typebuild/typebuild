import streamlit as st

def test_main():
    # Add a test menu
    # Get menu object
    menu = st.session_state.menu
    test_menu_items = [
        ['HOME', 'Test', 'print_success'],
        ['Test', 'Test 1', 'print_success'],
        ['Test', 'Test 2', 'print_success'],
        ['Test 2', 'Test 2.1', 'print_success'],
        ['Test 2.1', 'Test 2.1.1', 'print_success']
    ]
    
    menu.add_edges(test_menu_items, 'test')

def print_success():
    st.success("Success!")
    return None