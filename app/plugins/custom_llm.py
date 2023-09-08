import streamlit as st
import openai
openai.api_key = st.secrets.openai.key
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 

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

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
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

