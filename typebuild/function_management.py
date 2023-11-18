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
    st.sidebar.code(f'st.session_state.activeStep: {st.session_state.activeStep}')
    st.sidebar.code(f'Module name: {module_name}')
    st.sidebar.code(f'Function name: {func_name}')
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
