import streamlit as st

def chat_input_framework(chat_key):
    prompt = st.chat_input("Enter your message", key="chat_input")
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    if prompt:
        st.session_state[chat_key].append(prompt)
        # Set ask llm to true
        st.session_state.ask_llm = True
    return None

def display_messages_framework(chat_key):
    # Display the user and assistant messages
    # TODO: Perhaps I should print the messages from the agents using update?
    with st.status("View chat") as st.session_state.chat_framework_status:
        for i,msg in enumerate(st.session_state[chat_key]):
            if msg['role'] in ['user', 'assistant']:
                the_content = msg['content']
                with st.chat_message(msg['role']):
                    st.markdown(the_content)
    return None