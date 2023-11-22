import streamlit as st

def get_available_destinations():
        
    G = st.session_state['menu'].G

    nodes = G.nodes()

    # convert to list
    nodes = list(nodes)

    # Join the nodes into a string
    destination_string = '- ' + '\n- '.join(nodes)

    return {'destinations': destination_string}


def tool_main(activeStep, tool_name='navigator'):
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
    st.sidebar.success(f'The path is {activeStep}')
    return 'Done.'