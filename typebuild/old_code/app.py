import os
import subprocess

def run():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    main_script_path = os.path.join(dir_path, 'main.py')
    subprocess.call(['streamlit', 'run', main_script_path])

if __name__ == '__main__':
    run()
