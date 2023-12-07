"""
LLM Access without any streamlit use for testing.
"""
from openai import OpenAI

def get_openai_output(messages, max_tokens=3000, temperature=0.4, model='gpt-4', functions=[]):
    """
    Gets the output from GPT models. default is gpt-4. 

    Args:
    - messages (list): A list of messages in the format                 
                messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}],

                system_instruction is the instruction given to the system to generate the response using the prompt.

    - model (str): The model to use.  Default is gpt-4.
    - max_tokens (int): The maximum number of tokens to generate, default 800
    - temperature (float): The temperature for the model. The higher the temperature, the more random the output
    """
    # Enable adding the key here.
    client = OpenAI()
    if '4' in model:
        model = "gpt-4-1106-preview"
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "n": 1,
        "messages": messages
    }
    if functions:
        params['functions'] = functions
    
    # If the word "json" is found in the content, ask for a json object as response
    json_found = False
    for i in messages:
        if "json" in i['content'].lower():
            json_found = True
            break
    if json_found:
        params['response_format'] = {"type": "json_object"}

    response = client.chat.completions.create(**params)
    msg = response.choices[0].message.content
    
    return msg
