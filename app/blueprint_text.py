"""
Blueprints consist of text and code.
This file deals with all aspects of text including:

- Creating, editing, deleting the text
- Layout of the text
- Helping the user to create high quality text instructions
"""

import re
from helpers import text_areas
import streamlit as st

import os


def user_requirement_for_view():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = st.session_state.file_path + '.txt'
    key = st.session_state.file_path + '_key'
    widget_label = 'User requirements for ' + st.session_state.file_path
    return text_areas(file=file_path, key=key, widget_label=widget_label)

def blueprint_builder():
    """
    An interactive experience to build a blueprint.
    """
    st.title('Blueprint Builder')
    # Get the user requirements files
    user_requirements = user_requirement_for_view()

    return None