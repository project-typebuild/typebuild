"""
Runs arbitrary code from an arbitrary file in the llm_code folder
"""
import streamlit as st
import importlib

def run_code(file_name: str, code: str = ""):
    """
    Given a python file, this tool runs the main function from that file.
    and returns if it was successful or not.
    If code is provide, it will first save the code to the file and then run the file.

    Args:
        file_name (str): The name of the file to run or save the code to
        code (str, optional): The code to run. Defaults to "".
    """
    if not file_name.endswith(".py"):
        file_name = file_name + ".py"
    if code:
        # If filename does not end with .py, add it
        
        with open(f"llm_code/{file_name}.py", "w") as f:
            f.write(code)

    function_name = "main"
    try:
        # Remove the .py extension
        file_name = file_name[:-3]
        module = importlib.import_module(f"llm_code.{file_name}")
        # Reload the module to ensure the latest code is run
        module = importlib.reload(module)
        function = getattr(module, function_name)
        function()
        return "Code ran successfully!"
    except Exception as e:
        return f"Error running code: {e}"
    
def tool_main(key: str, file_name: str, code: str = "", auto_run: bool = True):
    """
    Given a python file, this tool runs the main function from that file.
    and returns if it was successful or not.

    Args:
        key (str): A unique key for this function, which can be used to update the function later.
        file_name (str): The name of the file to run or save the code to
        code (str, optional): The code to run. Defaults to "".
        auto_run (bool, optional): Whether to run the function automatically. Defaults to True.
    """
    # Run the code
    result = run_code(file_name=file_name, code=code)
    res_dict = {
        "content": result,
        "task_finished": False,
        "ask_llm": True,
        "ask_human": False,
        "task_name": st.session_state.current_task,
        "key": key,
    }
    return res_dict