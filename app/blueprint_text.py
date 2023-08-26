"""
Blueprints consist of text and code.
This file deals with all aspects of text including:

- Creating, editing, deleting the text
- Layout of the text
- Helping the user to create high quality text instructions
"""

import re
import streamlit as st
from streamlit_quill import st_quill

import os

