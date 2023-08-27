import streamlit as st
import os
from streamlit_quill import st_quill

def update_text_file(file, value):
    """
    On Change, this saves the current labels to a file called labels.md in the root folder.
    """
    
    with open(file, 'w') as f:
        f.write(value)
    return None



def text_areas(file, key, widget_label):
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
        
        if st.button(f"Update {widget_label}", key=f"update_button_{key}"):
            update_text_file(file, value=out)
            st.experimental_rerun()
    # Add user requirements to session state
    st.session_state.user_requirements = out
    return out