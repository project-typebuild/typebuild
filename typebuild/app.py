import os
import subprocess

def run():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    subprocess.call(['streamlit', 'run', os.path.join(dir_path, 'main.py')])
