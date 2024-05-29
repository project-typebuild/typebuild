"""
This is the new approach to tools that I am trying in April 2024.
Here, the code agent is nothing but a tool that can be called by the LLM to get the required code.
It uses a high quality LLM model to generate the code.
"""

import json
import requests

def tool_main(objective, file_name, description):
    """
    Takes the given objective and sends the code to the server.

    Parameters:
    objective (str): The objective the code is supposed to achieve.
    file_name (str): The name of the file to save the code in.
    description (str): The description of the code.
    """

    # First get the schema of current data
    schema_url = "https://general.viveks.info/get_data"
    data = {'raw_data_schema': True}
    response = requests.get(schema_url, params=data)
    data_schema = response.text

    system_instruction = """You are helping me write python code to be deployed in a flask server.  
    Think carefully about the requirement given by the user.  Ask clarifying questions, if any needed."""


    prompt = f"""This is the requirement given by the user: {objective}

    Create well documented python code using pandas to achieve the objective.
    All the data is in parquet format in the data folder (e.g. data/tasks.parquet).

    Given below are the schema of each of the data files:
    {data_schema}

    When the code is ready, send it to the server.
    """

    tools = [
        {
    "type": "function",
    "name": "code_creator",
    "description": "Returns python code based on the given objective.  The code should have one function called main, and it should return the desired result as a string or as a dataframe",
    "parameters": {
      "type": "object",
      "required": ["code"],
      "properties": {
        "code": {
          "description": "Python code based on the given objective",
          "type": "string"
        },
      }
    }
  }
    ]

    # The URL of the endpoint
    url = "https://general.viveks.info/generate"

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "system", "content": prompt}
    ]
    # The data to be sent to the endpoint
    data = {
        "messages": messages,
        "functions": tools,
        "model": "gpt-4.5-turbo-preview",
    }

    # The headers for the request, including the Authorization token
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer llm_token"  # Replace with your actual token
    }

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    return response.text