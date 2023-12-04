import time
import streamlit as st

from function_management import get_docstring_of_function

def get_available_destinations():
        
    G = st.session_state['menu'].G

    nodes = G.nodes()

    # convert to list
    nodes = list(nodes)

    # Join the nodes into a string
    destination_string = '- ' + '\n- '.join(nodes)

    return {'destinations': destination_string}


def tool_main(activeStep, auto_rerun=True):
    """
    This tool will help the users navigate through the menu using the chat interface. it takes the activeStep as an input 
    and changes the activeStep in the session state to the activeStep that the user wants to go to.

    Parameters:
    - activeStep (str): The activeStep that the user wants to go to
    - tool_name (str): The name of the tool. always set to 'navigator'

    Returns (str):
    - 'Done.'

    """

    st.session_state.activeStep = activeStep
    st.snow()
    st.sidebar.info(f"Active step is {activeStep}")
    time.sleep(2)
    docstring = get_docstring_of_function(activeStep)
    st.sidebar.success(f'The path is {activeStep}')

    helpful_chat_hints = """\n\nAsk the user to use the UI above.  Offer further help
    if necessary."""
    res = {
        'content': f'{docstring}\n{helpful_chat_hints}',
        'ask_llm': True,
        'task_finished': True,
        }
    return res