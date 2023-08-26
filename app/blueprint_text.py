"""
Blueprints consist of text and code.
This file deals with all aspects of text including:

- Creating, editing, deleting the text
- Layout of the text
- Helping the user to create high quality text instructions
"""

import re
import streamlit as st
from streamlit_quill import st_quill

import os

def update_md_file(file, value):
    """
    On Change, this saves the current labels to a file called labels.md in the root folder.
    """
    
    with open(file, 'w') as f:
        f.write(value)
    return None

def md_text_areas(file, key, widget_label):
    """
    We have stored text that the user can edit.  
    Given a file, load the text from the file and display it in a text area.
    On change, save the text to the file.
    """

    # Load current value from file.  If not create empty file
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write('')
    with open(file, 'r') as f:
        value = f.read()
    
    out = st_quill(
        value=value,
        placeholder="Write your requirements here...",
        key=key,
        html=True,
        )
    if out != value:
        
        if st.button("Update requirement", key=f"update_button_{key}"):
            update_md_file(file, value=out)
            st.experimental_rerun()
    # Add user requirements to session state
    st.session_state.user_requirements = out
    return out

def user_requirement_for_view():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = st.session_state.file_path + '.txt'
    key = st.session_state.file_path + '_key'
    widget_label = 'User requirements for ' + st.session_state.file_path
    return md_text_areas(file=file_path, key=key, widget_label=widget_label)