# JUST CREATED THIS FILE...HAVE TO WORK ON IT.
# Moved functiions from project_management.py to here.

def ideate_project():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = os.path.join(st.session_state.project_folder, 'project_settings', 'project_description.txt')
    key = 'Project Description'
    widget_label = 'Project Description'
    st.subheader('Ideate')
    project_description = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.project_description = project_description

    ideation_chat()
    return None


def ideation_chat():
    """
    A chat on the project description.
    That could be exported to the project description file.
    """
    # If there is no project description chat in the session state, create one
    if 'ideation_chat' not in st.session_state:
        st.session_state.ideation_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='project_description_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(
                st.session_state.ideation_chat, 
                model='gpt-3.5-turbo-16k'
                )
            # Add the response to the chat
            st.session_state.ideation_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.ideation_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None
