# JUST CREATED THIS FILE...HAVE TO WORK ON IT.
# Moved functiions from project_management.py to here.


def set_user_requirements():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = os.path.join(st.session_state.project_folder, 'project_settings', 'user_requirements.txt')
    key = 'User Requirements'
    widget_label = 'User Requirements'
    st.subheader('User requirements')
    user_requirements = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.user_requirements = user_requirements

    user_requirements_chat()
    st.stop()
    return None

def user_requirements_chat():

    """
    A chat on the user requirements.
    That could be exported to the user requirements file.
    """
    # If there is no user requirements chat in the session state, create one
    if 'user_requirements_chat' not in st.session_state:
        st.session_state.user_requirements_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='user_requirements_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(st.session_state.user_requirements_chat, model='gpt-3.5-turbo-16k')
            # Add the response to the chat
            st.session_state.user_requirements_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.user_requirements_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None


