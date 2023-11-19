import streamlit as st
import pandas as pd
import altair as alt


def display_messages(messages, expanded=True):
    """
    Displays the messages in the chat.

    Utilizes Streamlit's expander and chat_message for displaying messages.
    This method iterates through the messages list and displays each one based
    on the role (user, assistant, system).

    Returns:
        None
    """
    if messages:
        with st.expander("View chat", expanded=expanded):
            for i, msg in enumerate(messages):
                if msg['role'] in ['user', 'assistant']:
                    the_content = msg['content']
                    with st.chat_message(msg['role']):
                        st.markdown(the_content)
    return None

