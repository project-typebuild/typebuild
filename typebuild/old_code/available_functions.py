"""
These are the functions that are available for function calling
"""

stage_description = """Tells the app what stage we are in so that the app
can send required information to the LLM. 
requirements stage: Sends detailed information on how to create the requirements.
code stage: Sends the current code, if any. Also sends information on how create or modify the code.
""" 

data_agent =  {
                "name": "data_agent",
                "description": "The data agent understands the data structure and\ncan answer questions about the data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    "content": {
                        "type": "string",
                        "description": """A detailed question about existing data that the data assistant can answer.  
                            The question should convey what the user is trying to do so that the data agent can fetch table names, fields, and other information."""
                    },
                    "function_name": {
                        "type": "string",
                        "description": "The name of the data agent."
                    }
                    }
                },
                "required": [
                    "content"
                ]
                }

def funcs_available():
    """
    Returns a list of functions available for the user to call.
    """
    f = [
        {
            "name": "save_requirements_to_file",
            "description": """Saves the user requirements to a file, given the content.  
                System knows the file name.  If I ask you to save the requirements, you can call this function.""",
            "parameters": {
                "type": "object",
                "properties": {

                    "content": {
                        "type": "string",
                        "description": "The content to save to the file."
                        },
                    },
                
                "required": ["content"]

            }

        },
        {
            "name": "save_code_to_file",
            "description": """
                Call this function to save generated code to file. The system knows the file name.
                If I ask you to save the code to file, you can call this function.
                """,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The code based on user requirements to save to the file."
                    }
            }},
            "required": ["content"]
            },
        
    ]
    return f

