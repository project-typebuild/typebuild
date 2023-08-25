import re
import streamlit as st
import pandas as pd

def parse_code_from_response(response):

    pattern = r"```python([\s\S]*?)```"
    matches = re.findall(pattern, response)
    return matches

def parse_modified_user_requirements_from_response(response):
    
    pattern = r"\|\|\|([\s\S]*?)\|\|\|"
    matches = re.findall(pattern, response)
    
    return matches
