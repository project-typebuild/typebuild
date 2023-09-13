"""
These are the functions that are available for function calling
"""

stage_description = """Tells the app what stage we are in so that the app
can send required information to the LLM. 
requirements stage: Sends detailed information on how to create the requirements.
code stage: Sends the current code, if any. Also sends information on how create or modify the code.
""" 

def funcs_available():
    """
    Returns a list of functions available for the user to call.
    """
    f = [
        {
            "name": "save_requirements_to_file",
            "description": "Saves the user requirements to a file, given the content.  System knows the file name",
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
                Code should only be sent to this function.
                """,
            "parameters": {
                "type": "object",
                "properties": {
                    "code_str": {
                        "type": "string",
                        "description": "The code based on user requirements to save to the file."
                    }
            }},
            "required": ["code_str"]
            },
        {
            "name": "set_the_stage",
            "description": stage_description,
            "parameters": {
                "type": "object",
                "properties": {
                "stage_name": {
                    "type": "string",
                    "description": "The name of the stage. Possible values are: 'requirements', 'code'.",
                    "enum": [
                    "requirements",
                    "code"
                    ]
                }
                }
            },
            "required": [
                "stage_name"
            ]
            }
    ]
    return f
