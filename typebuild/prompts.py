"""
This file is used to generate all prompts to be sent to LLMs
"""

import os
import pandas as pd
from helpers import get_approved_libraries
import streamlit as st

def get_prompt_to_code(user_requirements, data_description=None, mod_requirements=None, current_code=None):

    """
    This function takes in the sample data and user requirements and creates the system instruction and prompt to code.
    # Args
    - user_requirements: A string with the user requirements
    - data_description: A dictionary with file names as keys and description of the data (including the column names) in each file as values
    - mod_requirements: A string with the modification requirements
    - current_code: A string with the current code

    # Returns
    - messages: A list of dictionaries with the system instruction and prompt to code

    """

    current_code_string = ""
    mod_requirements_string = ""
    if mod_requirements:
        mod_requirements_string = f"""
        
        YOU CREATED CODE BASED ON REQUIREMENTS GIVEN BELOW.  
        NOW THE USER WANTS TO MAKE THIS CHANGE:
        |||{mod_requirements}|||
        
        """
        current_code_string = f"""CURRENT CODE:
        MAKE THE REQUIRED CHANGES TO THE CODE BELOW, LEAVING OTHER PARTS OF THE CODE UNCHANGED:
        |||{current_code}|||"""


    if data_description is not None:
        df_string = f"""DATA DESCRIPTION:
        The following dictionary has the file names as keys and description of the data in each file as values:
        Use the column names and data types when you are writing the functions
        |||{data_description}|||"""
    else:    
        df_string = "NOTE: No data description is provided"

    system_instruction_to_code = f"""
You are the python developer with an expertise in packages like streamlit, pandas, altair. 
Because of your expertise, a domain expert contacted you to create a streamlit app for them. 
After your meeting with the domain expert, you have noted down their requirements. 

In your collection of functions, you have the following functions, ready to use. 

AVAILABLE FUNCTIONS:

[ st.stop() - A streamlit function to stop the execution under the line ]
    
{df_string}
{mod_requirements_string}
The Requirements are:
|||
{user_requirements}
|||
{current_code_string}

THINGS TO REMEMBER:
- The functions you are generating will be used in a larger scheme of things. so be responsible in generating functions
- If the user asks for a login page, sign up page. Ignore it, you are not responsible for that. There is a separate team for that.
- If a sample data is provided, use it to write better functions. You should be careful with the data types and column names
- If a sample data is provided, it is provided to you as a dictionary. The keys are the file names of the exisitng parquet files and the values are description of the data in each file. 
- The reason for providing dictionary of file names and description is, you need to identify what file to use for the given user requirements based on the description of the data in the file.
- Identify the file name and write a function to read the data from the particular parquet.
- Once you have the dataframe, you can use it to write the functions that the user is asking for. 
- If the user asks for a table, you should always use the function 'display_editable_data' to display the table. This function will take care of displaying the table and also editing the table.
- You can import the function 'display_editable_data' using the following import statement: |||from data_widgets import display_editable_data|||
- You need to return the full code of the functions you are generating.
- Do not write unnecessary print, st.write and success, info and warning messages in the functions.
- Do not return the available functions in the response. Your response should include only the newly generated functions
- You need to create one function for each feature in the app
- IMPORTANT: DO NOT USE STREAMLIT CACHE
- You must always provide a function called 'main' that calls all the other functions.  I will call this function, and so do not call it like 'main()'
    
based on the above requirements, write concise code and don't forget to write the detailed docstrings, including the args, return etc
"""
    prompt_to_code = """
    CODE:
    """

    messages =[
                {"role": "system", "content": system_instruction_to_code},
                {"role": "user", "content": prompt_to_code}]

    st.session_state.last_request = messages
    return messages

def blueprint_prompt_structure(df=None, prompt=''):
    """
    Prompt to help user generate the blueprint structure.
    """
    system_instruction = f"""You are an experienced software architect 
        helping the user to create a project plan for a software application. 
        Here is the draft project description:
        {st.session_state.project_description}

        Have a dialogue with the user to help them create a high quality project description
        so that they can create a feature rich app that is great to use.  Help them to
        think about various use cases, useful features, problems to look out for, etc.

        As an solution architect you should definetly think of:
        - What is the problem that the user is trying to solve?
        - The project is based on CSV files.  Recommend column changes or additional CSV files if needed.
        
        Document the user's response and create a final project description that is ready to use
        when the user requests it.
        """
    system_msg = {'role': 'system', 'content': system_instruction}
    st.session_state.project_description_chat.append(system_msg)
    msg = {'role': 'user', 'content': prompt}
    st.session_state.project_description_chat.append(msg)
    return None


def get_parameter_info(func_str):
    """
    Get the prompt to send a function string to 
    GPT and get information about 
    """
    
    system_instruction = """I'll give you some python functions.  
    Extract the parameters (args, kwargs) that the function takes and return the following for each parameter:
- name of parameter
- type (int, str, float, etc.)
- description of parameter
- options (A list of options, if the parameter accepts only certain values.  Empty list, if none)
- required (True/False)

If there are no parameters, return an empty list.
Return this as a well formatted python list of dicts within |||triple back ticks|||"""

    prompt = f"""EXTRACT INFORMATION ABOUT THE ARGS AND KWARGS FOR THIS FUNCTION:
    {func_str}"""

    messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}]
    return messages

def from_requirements_to_code(chat_key, current_text="", prompt="", func_str=None):
    """
    This function loads the prompt to create everything from
    gathering requirements to generating code.

    It looks at the session state for the context, and adds
    that information to the system instruction.
    """

    # Get data description
    data_model_file = os.path.join(st.session_state.project_folder, "data_model.parquet")
    selected_view = st.session_state.selected_view
    data_description = st.session_state[f"data_description_{selected_view}"]
        
    current_text_string = ""
    if current_text:
        current_text_string = f"""
        THIS IS WHAT I HAVE SO FAR IN MY REQUIREMENTS FILE:
        file_name: {st.session_state.file_path}.txt
        |||{current_text}|||
        """

    if func_str:
        stage_info = f"Note: Requirement and Code has been generated.  You can explain or modify as per the user's request.\n"
        current_stage = 'code'

    elif 'technical requirement' in current_text.lower():
        stage_info = "Note: Requirement has been created but code has not been generated yet."
        current_stage = 'code'
    
    elif 'functional requirement' in current_text.lower():
        stage_info = "Note: Functional requirement has been created but step-by-step technical requirements has not been generated yet."
        current_stage = 'requirements'
    else:
        stage_info = "Note: Requirement and Code have not been generated yet.  Start by creating the functional requirement."
        current_stage = 'requirements'

    str_about_stages = ""
    if st.session_state.function_call:
        str_about_stages = """
        Work on one stage at a time.  When you move to a new stage call the set_the_stage function
    to get specific instructions for that stage.  It will give you the instructions and required assets such as the current code."""
    
    system_instruction = f"""You are helping me in two stages of my software development process:
    1.  Gathering functional and technical requirements
    2.  Generating code based on the technical requirements

    It is important that code is generated only on the basis of the technical requirements.
    {stage_info}

    You have to go through the stages in the order given above.  You cannot skip a stage.
    You can go back to a previous stage to make changes.
    If a change is made to one stage, we have to ensure that the changes are reflected in the other stages.
    Anytime a change is made to requirements, confirm it with me and then write it to file.

    {str_about_stages}
    {data_description}
    {current_text_string}"""

    # Get the current stage
    if f'current_stage_{st.session_state.stage_num}' in st.session_state:
        current_stage = st.session_state[f"current_stage_{st.session_state.stage_num}"]
    
    if current_stage == 'requirements':
        system_instruction += "WE ARE CURRENTLY IN THE REQUIREMENTS STAGE\n\n" + get_technical_requirements_instructions()

    elif current_stage == 'code':
        system_instruction += "WE ARE CURRENTLY IN THE CODE GENERATION STAGE\n\n" + get_code_instructions()
        system_instruction += f"\nTHIS IS THE CURRENT CODE: \n{func_str}\n"
        if st.session_state.show_developer_options:
            st.sidebar.info("Added code instructions")

    else:
        st.error(f"Invalid stage, {current_stage}")
    if st.session_state.show_developer_options:
        st.sidebar.info(f"Stage in prompt: {current_stage}")
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
    2.  Write down step by step instructions for the developer.  Include file path, field names and other information.
    3.  Check the instructions to see if it will meet the functional requirement.  If not, revise.  
    4.  Remove unnecessary or totally obvious steps.
    5.  Make sure the steps are in non-technical language, so that I understand.
    6.  Format the final instructions in markdown and give it to me within triple pipe. 

    The final instructions should be in the following format:
    |||
    FUNCTIONAL REQUIREMENT: <functional requirement>
    TECHNICAL REQUIREMENTS:
    <step by step instructions>
    |||

    When the I am happy with the requirements, offer to save the requirements to a file.
    """

def get_code_instructions():

    # If there is an error, get error message
    error_msg = ""
    if 'error' in st.session_state:
        error_msg = f"""GOT THIS ERROR MESSAGE IN THE CURRENT CODE.  PLEASE FIX IT:
        ```{st.session_state.error}```
        
        """

    data_folder = os.path.join(st.session_state.project_folder, 'data')

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
    - You can suggest creating synthetic data using faker and faker-commerce, and numpy, if needed.  Save new files to the '{data_folder}'.  Always show the data and confirm with the user before saving it to a parquet file.
    - Use the loaded the dataframe to fulfill the requirements. 
    - Use st.dataframe to display tablular data.  This is not editable.
    - If the user has to edit the data, you can use the function display_editable_data(df, file_name) to display and edit the data.  You can import the function 'display_editable_data' using the following import statement: |||from data_widgets import display_editable_data|||
    - Use st.info, st.warning, st.success for clarity, if needed.  You can also use emojis to draw attention.
    - Create one function per feature, passing necessary data so that data is not loaded again and again.
    - Create a function called "main" that calls all the other functions in the order they are needed.   Create it but do not call the main function.  It will be called by the system.
    - There should be only one code block and this should be the full code.  Explanations, tips, etc. should be in markdown and not in code blocks.
    {error_msg}        
    Write concise code based on the instructions above, fixing errors, if any.  Document it with detailed docstrings, and comments.
    """

    return system_instruction_to_code

