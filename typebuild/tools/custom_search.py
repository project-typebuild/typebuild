import requests
import streamlit as st
import time

def tool_main(key, query, auto_rerun=False):
    """
    Returns the search results from the API as a string.

    Args:
        query (str): The query to search for.
        key (str): A unique key for this task, which can be used to update the output of this tool.

    Returns:
        str: The search results as a string.
    """
    url = f"https://typebuildapi.azurewebsites.net/api/gs?query={query}"
    res = requests.get(url)
    buf = "RESULTS FROM THE QUERY: " + query + "\n"
    for r in eval(res.text):
        # Get a string with title, link, and snippet as key value
        # pairs separated by newlines
        buf += '\n'.join([f'{k}: {v}' for k, v in r.items() if k in ('title', 'link', 'snippet')])
        buf += "\n===\n"
    
    return {
        'content': buf,
        'ask_llm': True,
        'task_finished': False,
        'task_name': st.session_state.current_task,
        'key': key,
    }
