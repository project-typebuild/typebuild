import time
import streamlit as st
import requests

def endpoint_main(endpoint, get_post='get', kwargs={}):
    """
    Given an endpoint, this tool will call the endpoint and display the result.
    """
    # If endpoing does not have a leading /, add it
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    if get_post == 'get':
        url = f"http://localhost:8000{endpoint}"
        response = requests.get(url, params=kwargs)
    else:
        response = requests.post(url, params=kwargs)
    if response.status_code == 200:

        return response.text
    else:
        return f"Error: {response.status_code}"
    
def tool_main(key, endpoint, get_post='get', kwargs={}, auto_rerun=False):
    """
    Given an endpoint, this tool will call the endpoint and display the result.

    Args:
        key (str): A unique key for this function, which can be used to update the function later.
        endpoint (str): The endpoint to call.
        get_post (str, optional): Whether to use a get or post request. Defaults to 'get'.
        kwargs (dict, optional): The parameters to pass to the endpoint. Defaults to {}.
    """
    

    result = endpoint_main(endpoint, get_post, kwargs)


    # Show the result
    st.session_state.tool_result = result
    
    res_dict = {
        "content": str(result),
        "task_finished": False,
        "ask_llm": True,
        "ask_human": False,
        "task_name": st.session_state.current_task,
        "key": key,
    }

    return res_dict