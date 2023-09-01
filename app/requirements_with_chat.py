"""
Generating functional and technical requirements 
with the help of LLMs
"""
from llm_functions import get_llm_output
import streamlit as st
import prompts

def project_description_chat():
    """
    A chat on the project description.
    That could be exported to the project description file.
    """
    # If there is no project description chat in the session state, create one
    if 'project_description_chat' not in st.session_state:
        st.session_state.project_description_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='project_description_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(st.session_state.project_description_chat, model='gpt-3.5-turbo-16k')
            # Add the response to the chat
            st.session_state.project_description_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.project_description_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None
