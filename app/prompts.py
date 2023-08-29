"""
This file is used to generate all prompts to be sent to LLMs
"""

import pandas as pd
import streamlit as st

def get_prompt_to_code(user_requirements, df=None, mod_requirements=None, current_code=None):

    """
    This function takes in the sample data and user requirements and creates the system instruction and prompt to code.
    # Args
    - user_requirements: A string with the user requirements
    - df_sample: A pandas dataframe with sample data
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
        ```{mod_requirements}```
        
        """
        current_code_string = f"""CURRENT CODE:
        MAKE THE REQUIRED CHANGES TO THE CODE BELOW, LEAVING OTHER PARTS OF THE CODE UNCHANGED:
        ```{current_code}```"""


    if df is not None:
        df_string = f"""SAMPLE DATA:
        The following dictionary contains the sample data. The keys are the table names of a database and the values are the sample rows of a pandas dataframe.
        Use the column names and data types when you are writing the functions
        ```{df}```"""
    else:    
        df_string = "NOTE: No sample data provided"

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
```
{user_requirements}
```
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
- You can import the function 'display_editable_data' using the following import statement: ```from data_widgets import display_editable_data```
- You need to return the full code of the functions you are generating.
- Do not write unnecessary print, st.write and success, info and warning messages in the functions.
- Do not return the available functions in the response. Your response should include only the newly generated functions
- You need to create one function for each feature in the app
- You need to have a main function that calls all the other functions
- Dont add the code 
    if __name__ == '__main__':
        main()
    
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