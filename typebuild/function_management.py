import streamlit as st
import importlib


# For the selected_node, get the func_name and hte module_name
def run_function(module_name: str, func_name: str):
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    func()
    return None

def run_current_functions():
    """
    Runs the functions selected in the menu.

    This function retrieves the module name and function name from the menu based on the active step.
    If the active step is 'HOME', it sets the module name and function name to 'home_page'.
    Otherwise, it retrieves the module name and function name from the menu's graph based on the active step.
    
    If the module name is 'home_page', the function does nothing.
    If both the module name and function name are not None, it calls the 'run_function' function with the module name and function name as arguments.
    If either the module name or function name is None, it raises an error using the 'st.error' function.

    Parameters:
    None

    Returns:
    None
    """
    menu = st.session_state.menu
    if st.session_state.activeStep == 'HOME':
        module_name = 'home_page'
        func_name = 'home_page'
    else:
        mynode = menu.G.nodes[st.session_state.activeStep]
        module_name = mynode.get('module_name')
        func_name = mynode.get('func_name')
    # If module name and func name are not None, run the function
    # Otherwise, do nothing
    if module_name == 'home_page':
        pass
    elif module_name and func_name:  
        run_function(module_name, func_name)
    else:
        # Tell me what was None
        if not module_name:
            st.error("Module name was None")
        if not func_name:
            st.error("Function name was None")
