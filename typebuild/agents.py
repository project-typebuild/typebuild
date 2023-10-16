"""
A list of agents who coordinate with each other
and the user to build things.
"""

import os
import pandas as pd
from helpers import get_approved_libraries
from plugins.llms import get_llm_output
import streamlit as st

def coordinator(chat_key, current_text="", prompt="", func_str=None):
    """
    This is the main agent that coordinates all the other agents.
    """
    # Check if there is a message to to any agent
    if st.session_state.message_to_agent:
        msg = st.session_state.message_to_agent

        if 'data_agent' in msg:
            data_agent(chat_key, msg)
            # Set ask llm to true
            st.session_state.ask_llm = True
    return None

def data_agent(content, name='data_agent'):
    """
    The data agent understands the data structure and
    can answer questions about the data.
    """
    # Get data description
    selected_view = st.session_state.selected_view
    data_description = st.session_state[f"data_description_{selected_view}"]

    system_instruction = f"""You are helping me with with the data required to code my project.
    I have the following data files:
    {data_description}

    Answer the following questions about the data:
    {content}

    Send detailed instructions including file names, column names, data types, and any other useful information to the developer,
    so that the developer is able to write the code without looking at the data.  Answer the question given to you
    and also include any other information that the developer may need to know about the data.

    """
    # Add the last two interactions to the chat
    chat_key = st.session_state.chat_key
    messages = st.session_state[chat_key][-2:].copy()
    # If the first message is from the system, replace it
    if messages[0]['role'] == 'system':
        messages[0] = {'role': 'system', 'content': system_instruction}
    else:
        messages.insert(0, {'role': 'system', 'content': system_instruction})

    # Add the question
    messages.append({'role': 'user', 'content': content})
    
    # Get the response
    res = get_llm_output(messages, functions=[])
    chat_key = st.session_state.chat_key
    # Add question to chat
    content = f"**Question to data agent:** {content}"
    st.session_state[chat_key].append({'role': 'assistant', 'content': content})
    # Add the response to the chat
    res = f"**Response from data agent:** {res}"
    st.session_state[chat_key].append({'role': 'assistant', 'content': res})

    # Set ask llm to true
    st.session_state.ask_llm = True
    return None

def from_requirements_to_code(chat_key, current_text="", prompt="", func_str=None):
    """
    This function loads the prompt to create everything from
    gathering requirements to generating code.

    It looks at the session state for the context, and adds
    that information to the system instruction.
    """

    selected_view = st.session_state.selected_view
    data_description = st.session_state[f"data_description_{selected_view}"]
        
    system_instruction = f"""You are helping in my software development process by creating:
    1.  Functional requirement
    2.  Detailed technical requirements that will be sent to the developer.
    3.  Changes: What is the the latest change to the requirements based on which code should be updated.

    The developer will only use the technical requirements and nothing else, and so it should have 
    very detailed instructions.

    Anytime I wish to make a change, write the new requirements for to the developer, making only the required change, keeping the rest as is.

    HERE IS INFORMATION ON THE DATA:
    {data_description}
    
    When you create requirements, be sure to mention the data source, selected fields, information about joins (if any), and any other information the developer should know about the data.
    Anytime you update requirements, be sure to provide the full requirement and add the latest change in the bottom.
    """

    # Add the technical requirements instructions
    system_instruction = f"""{system_instruction} {get_technical_requirements_instructions()}"""

    prompt = f"""{prompt}"""

    chat = st.session_state[chat_key]

    # If the chat is empty, add the system message
    if len(chat) == 0:
        chat.append({'role': 'system', 'content': system_instruction})
    else:
        # Replace the system message, since it may have been updated
        chat[0] = {'role': 'system', 'content': system_instruction}

    # Add the user message, if there is one
    if prompt:
        chat.append({'role': 'user', 'content': prompt})
    return None


def get_technical_requirements_instructions():
    return f"""You are helping me develop technical requirements for my project.
    Start by offering to help.

    Confirm function requirement if you know it, if not ask me what the functional requirement is.

    Next, Help me create step-by-step instructions for my young developer so that they have every detail they need to code.  Do not worry about basic technical details like libraries or loading data.  The developer knows that (FYI: The developer will use python, pandas and streamlit).  I just have to tell them what to do with the data without any scope for doubt.

    Before you write the instructions:

    1.  Look for ambiguities or missing information in my requirement.  If you need clarifications, wait for me to respond before going to step 2. Make sure you have something (table, chart, forms, etc.) to display on streamlit.
    2. Make sure you understand the data before you suggest anything.  Ask data_agent for help, if needed.  Do not proceed until you understand the data.
    3.  Write down step by step instructions for the developer.  Include file path, field names and other information.  Make sure only the necessary columns are loaded.  Loading unnecessary columns may lead to errors during joins.
    3a. It is very important to define each calculation step-by-step so that I can verify that.
    4.  Check the instructions to see if it will meet the functional requirement.  If not, revise.  
    5.  No step is unnecessary.  Specify everything the developer needs to do.  If you think the developer will need to do something, but you are not sure, ask me.
    6.  Write down the instructions before finalizing.  Critically evaluate the instructions first, address the issues and then finalize the instructions.
    7.  Make sure the steps are in non-technical language, so that I understand.  This should include data source, selected fields, information about joins (if any), and any other information the developer should know about the data.
    8.  Format the final instructions in markdown and give it to me within triple pipe. 

    The final instructions should be in the following format:
    |||
    FUNCTIONAL REQUIREMENT: <functional requirement>
    TECHNICAL REQUIREMENTS:
    <step by step instructions>
    |||

    When the I am happy with the requirements, offer to save the requirements to a file.
    """

def get_code_instructions(requirements=None, code=None):

    # If there is an error, get error message
    error_msg = ""
    if 'error' in st.session_state:
        error_msg = f"""GOT THIS ERROR MESSAGE IN THE CURRENT CODE.  PLEASE FIX IT:
        ```{st.session_state.error}```
        
        """
    if requirements:
        instructions = f"""USE THE INSTRUCTIONS BELOW TO GENERATE CODE:
        {requirements}
        """
    else:
        instructions = ""

    if code:
        code = f"""THIS IS THE CURRENT CODE:
        {code}
        """
    else:
        code = ""

    system_instruction_to_code = f"""
    You are the python developer with an expertise in packages like streamlit, pandas, altair, faker, faker-commerce
    Because of your expertise, a domain expert contacted you to create a streamlit app for them. 
    The expert has given you their requirements. 

    In your collection of functions, you have the following functions, ready to use. 

    AVAILABLE FUNCTIONS:

    - st.stop() - A streamlit function to stop the execution under the line
    - st.rerun() - A streamlit function to rerun the app
    - st.expander - A streamlit function to create an expander
    - st.columns - A streamlit function to create columns
    - st.download_button - A streamlit function to create a download button, this allows the user to download images, csv, binary files, text, etc.
    - st.session_state - A streamlit function to store data in the session state. This is useful when you want to store data across reruns. this is a dictionary. (make sure to import base64)
    
    approved_libraries = HERE ARE THE APPROVED LIBRARIES: {get_approved_libraries()}
    
    THINGS TO REMEMBER:
    - Do not create login or signup, even if requested.
    - Pay careful attention to the data description, especially to column types and names.
    - Use in-built streamlit methods to create charts if possible. Else, use altair.  Be sure to pass valid dataframe to altair, and specify column encoding.
    - Do not use index columns for calculations, if avoidable.
    - Try to use only the approved libraries.  If you need to use other libraries, check with me first.
    - You have been given one or more data files.  Load the files needed for this requirement and create a dataframe.
    - You can suggest creating synthetic data using faker and faker-commerce, and numpy, if needed.  Save new files to the '{st.session_state.project_folder}/data'.  Always show the data and confirm with the user before saving it to a parquet file.
    - Use the loaded the dataframe to fulfill the requirements. 
    - Use st.dataframe to display tablular data.  This is not editable.
    - If the user has to edit the data, you can use the function display_editable_data(df, file_name) to display and edit the data.  You can import the function 'display_editable_data' using the following import statement: |||from data_widgets import display_editable_data|||
    - Use st.info, st.warning, st.success for clarity, if needed.  You can also use emojis to draw attention.
    - Create one function per feature, passing necessary data so that data is not loaded again and again.
    - Create a function called "main" that calls all the other functions in the order they are needed.   Create it but do not call the main function.  It will be called by the system.
    - There should be only one code block and this should be the full code.  Explanations, tips, etc. should be in markdown and not in code blocks.
    {instructions}
    {error_msg}        
    {code}
    Write concise code based on the instructions above, fixing errors, if any.  Document it with detailed docstrings, and comments.
    """

    return system_instruction_to_code

