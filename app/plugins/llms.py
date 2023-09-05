from glob import glob
import streamlit as st
import openai
openai.api_key = st.secrets.openai.key
import pandas as pd

def get_llm_output(input, max_tokens=800, temperature=0, model='gpt-4'):

    """
    Given an input, get the output from the LLM.  Default is openai's gpt-4.

    Args:
    - input (list): A list of messages in the format                 
                messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}],

                system_instruction is the instruction given to the system to generate the response using the prompt.
                prompt is the input given by the user.

    - model (str): The model to use.  Default is gpt-4.
    - max_tokens (int): The maximum number of tokens to generate, default 800
    - temperature (float): The temperature for the model. The higher the temperature, the more random the output

    """
    if 'gpt' in model:
        res = get_gpt_output(messages=input, max_tokens=max_tokens, temperature=temperature, model=model)
    else:
        res = "Unknown model"
    return res

def get_gpt_output(messages, model='gpt-4', max_tokens=800, temperature=0):
    """
    Gets the output from GPT models. default is gpt-4. 

    Args:
    - messages (list): A list of messages in the format                 
                messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}],

                system_instruction is the instruction given to the system to generate the response using the prompt.
                prompt is the input given by the user.

    - model (str): The model to use.  Default is gpt-4.
    - max_tokens (int): The maximum number of tokens to generate, default 800
    - temperature (float): The temperature for the model. The higher the temperature, the more random the output
    """

    response = openai.ChatCompletion.create(
                model=model,
                messages = messages,
                max_tokens=max_tokens,
                temperature=temperature,
                n=1
            )
    return response.choices[0].message.content

def add_data_with_llm():
    """
    This function allows the user to extract insights 
    from existing data using an LLM.  It can be used to
    summarize, classify, answer questions, or to extract specific information
    from a given column of the source dataframe.

    The results will be written to a new dataframe that 
    will connect to the primary key of the source dataframe.

    Args:
    None: User will select the source dataframe and column(s) to use with widgets.

    Returns:
    None    
    """

    # Select the source dataframe and column
    st.write("### Select the source data and column(s)")

    tables = glob('data/*.parquet')
    # If there is more than one table, allow the user to select the table
    if len(tables) == 0:
        st.error("There should be some uploaded data for this to work.  Please upload some data from the project settings area.")
        st.stop()
    if len(tables) == 1:
        source_df = tables[0]
    else:
        source_df = st.selectbox("Select the source dataframe", tables)
    
    # Read the source dataframe
    df = pd.read_parquet(source_df)

    # Get the column names
    columns = df.columns
    # Select the column to use
    how_to_select = """If more than one column is selected, the text from each column will be 
    appended with paragraphs in-between and used as the input to the LLM.  The sequence
    of the text will be based on the order of the columns selected.
    """
    st.info(how_to_select)
    columns = st.multiselect("Select the column(s) to use", columns)

    # Get the text from the columns
    df["text_for_llm"] = df[columns].apply(lambda x: '\n'.join(x), axis=1)

    # RANU: Add filtering options here.


    # Name the destination dataframe
    dest_df = st.text_input("Name the destination table", value='llm_output')
    
    # RANU: Save the new data information to the data model

    # RANU: Add system instruction and looping here, saving the results to the destination dataframe



    
