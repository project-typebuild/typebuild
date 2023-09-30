import streamlit as st
import genstudiopy

    
def custom_llm_output(input, max_tokens=1000, temperature=0, model='gpt-4', functions=[]):
    res = genstudiopy.ChatCompletion.create(
    model="gpt-4",
    messages=input,
    )
    out = res['choices'][-1]['message']['content']
    return out


