import streamlit as st
import importlib


# For the selected_node, get the func_name and hte module_name
def run_function(module_name: str, func_name: str):
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    func()
    return None

def get_module_and_function(selected_node):
    """
    Get the module and function name from the selected node.
    """
    if not selected_node:
        selected_node = st.session_state.activeStep
    menu = st.session_state.menu

    if selected_node == 'HOME':
        module_name = 'home_page'
        func_name = 'home_page'
    else:
        mynode = menu.G.nodes[selected_node]
        module_name = mynode.get('module_name')
        func_name = mynode.get('func_name')
    return module_name, func_name

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

    module_name, func_name = get_module_and_function(st.session_state.activeStep)
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

def get_docstring_of_function(active_step):
    """
    Gets the docstring of the function selected in the menu.
    """
    if not active_step:
        active_step = st.session_state.activeStep
    module_name, func_name = get_module_and_function(active_step)
    st.info(f"M: {module_name}, F: {func_name}")
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    return func.__doc__