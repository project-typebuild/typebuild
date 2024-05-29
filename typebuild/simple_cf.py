import time
import streamlit as st
import requests
import json
from simple_agent_definitions.get_agent_definitions import get_main_instruction
from tools.new_code_agent import tool_main as new_code_agent

def display_messages():
    for message in st.session_state.conversations:
        if message["role"] == "user":
            avatar = "👤"
        elif message["role"] == "assistant":
            avatar = "🤖"
        else:
            avatar = "💻"
        # Show only user and assistant messages

        if message["role"] in ["user", "assistant"]:   
            with st.chat_message(message["role"], avatar=avatar):
                st.write(message["content"])    

def get_tools():
    file = "tools.json"
    with open(file, "r") as f:
        tools = json.load(f)
    return tools

def get_llm_response(messages, functions, model="gpt-4-turbo-preview", max_tokens=2000):
    url = "https://general.viveks.info/generate"
    # url = "https://general.viveks.info/claude"
    model = 'gpt-3.5-turbo'
    # The data to be sent to the endpoint
    data = {
        "messages": messages,
        "model": model,  # Optional: Specify the model you want to use
        "max_tokens": 2000,  # Optional: Specify the maximum number of tokens
        "functions": get_tools()
    }

    # The headers for the request, including the Authorization token
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer llm_token"  # Replace with your actual token
    }

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response

def manage_llm_interaction():
    """"
    This function calls the llm and gets the response, when required.
    """
    if 'ask_llm' not in st.session_state:
        st.session_state.ask_llm = False
    
    if st.session_state.ask_llm:
        with st.spinner("Thinking..."):
            response = get_llm_response(
                messages=st.session_state.conversations, 
                functions=get_tools(), 
                model='gpt-4-turbo-preview', 
                max_tokens=2000
                )
        if response.status_code == 200:
            response = response.json()
            
            st.session_state.latest_response = response
            message = response.get('message')
            if message:
                st.session_state.conversations.append({"role": "assistant", "content": message})
            
            if response.get('function_call'):
                function_call(response['function_call'])
                # Set the ask_llm to True
                st.session_state.ask_llm = True
                st.rerun()
            # If no function call, set ask_llm to False
            else:
                st.session_state.ask_llm = False
                # Rerun the app
                st.rerun()
        else:
            st.error(f"Error: {response.text}")


def function_call(function_call):
    name = function_call['name']
    arguments = function_call['arguments']
    # If arguments are a string, convert to dictionary
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    
    # show the arguments
    st.info(f"Calling function: {name}")
    st.info(f"Arguments: {arguments}")
    time.sleep(3)
    if name == "agent_code_creator":
        st.info("Starting code creator...")
        with st.spinner("Generating code..."):
            res = new_code_agent(arguments['objective'], arguments['file_name'], arguments['description'])
        st.code(res)
        st.stop()
    # If the name starts with 'endpoint_', remove it
    if name.startswith("endpoint_"):
        name = name.replace("endpoint_", "")
    # Call the llm endpoint
    url = f"https://general.viveks.info/{name}"
    with st.spinner(f"Calling {name}..."):
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        response = requests.get(url, params=arguments)
    # If the response is successful, add the response to the conversations
    if response.status_code == 200:
        response = response.text
        st.session_state.conversations.append({"role": "function", "name": name, "content": response})
    else:
        st.session_state.conversations.append({"role": "function", "name": name, "content": f"There was an error processing your request: {response}"})

    return None

def chat():

    # If the conversation is empty, add the main instruction
    if len(st.session_state.conversations) == 0:
        st.session_state.conversations.append({"role": "system", "content": get_main_instruction()})
    # Add last response to the sidebar, if it exists
    if 'latest_response' in st.session_state:
        st.header("Latest response:")
        st.sidebar.write(st.session_state.latest_response)

    prompt = st.chat_input("Type your message here")
    if prompt:
        st.session_state.conversations.append({"role": "user", "content": prompt})
        st.session_state.ask_llm = True
    display_messages()
    manage_llm_interaction()