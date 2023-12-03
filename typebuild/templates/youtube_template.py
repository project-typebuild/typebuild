"""
Ask the user what they are looking for in youtube transcripts.
Create a task graph with the following tasks:
- `ask_user`: Ask the user what they are looking for in youtube transcripts.
- `search_youtube`: Search youtube for the user's query.
- `analyze_transcripts`: Analyze the transcripts of the videos returned by youtube.
"""
from task_graph import TaskGraph

def main():
    task = TaskGraph(name='youtube', description='Template to search youtube and analyze transcripts')
