import requests
import streamlit as st
import time

def tool_main(query, auto_rerun=False):
    """
    Returns the search results from the API as a string.

    Args:
        query (str): The query to search for.

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
    st.info(buf)
    time.sleep(5)
    return {
        'content': buf,
        'ask_llm': True,
        'task_finished': False,
    }
