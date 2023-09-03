"""
These are the functions that are available for function calling
"""
def funcs_available():
    """
    Returns a list of functions available for the user to call.
    """
    f = [
        {
            "name": "save_requirements_to_file",
            "description": "Saves the user requirements to a file, given the file name and the content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to save the requirements to."
                        },
                    "content": {
                        "type": "string",
                        "description": "The content to save to the file."
                        },
                    },
                
                "required": ["file_name", "content"]

            }

        },
        {
            "name": "save_code_to_file",
            "description": "Saves the based on the user requirement to the file.  \nFile name and path is taken from the selected view, and so only \nthe file content is needed.\n\nParameters:\n-----------\ncode_str: str\n    The code based on user requirements to save to the file.\nReturns:\n--------\nSuccess message: str",
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
            "name": "send_code_to_llm",
            "description": "Call this to explain or modify the current code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dummy_arg": {
                        "type": "string",
                        "description": "A dummy argument to make the function signature"
                    }
            }},
            "required": []
        },
        {
            "name": "set_the_stage",
            "description": "Sets the name of the stage to the session state so that the LLM\ncan get appropriate instructions.\n\nParameters:\n-----------\nstage_name: str\n    The name of the stage.  Possible values are: 'functional', 'technical', 'code'.\nReturns:\n--------\nSuccess message: str",
            "parameters": {
                "type": "object",
                "properties": {
                "stage_name": {
                    "type": "str",
                    "description": "The name of the stage. Possible values are: 'functional', 'technical', 'code'.",
                    "enum": [
                    "functional",
                    "technical",
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
