"""
Using this to manage tasks.
"""
import os
import streamlit as st
from collections import namedtuple, OrderedDict
import dill as dl
from agents import Agent, AgentManager

class ObjectivesCoordinator:
    """
    The Objective Coordinator maintains a list of ordered tasks and does the following:
    1. Adds a task to the list
    2. Removes a task from the list
    3. Saves the objective instance to a file
    4. Loads tasks belonging to an objective from a file
    5. Maintains the status of the tasks (scheduled, running, completed, failed)
    6. Maintains the status of the objective (scheduled, running, completed, failed)
    
    """

    def __init__(self, objective_name):
        """
        Initializes the coordinator.
        """
        self.objective_name = objective_name
        self.tasks = OrderedDict()
        self.possible_statuses = ['scheduled', 'running', 'completed', 'failed']
        self.status_first_task = 'scheduled'
        self.status_last_task = 'scheduled'

    def save_to_file(self, dir=None):
        """
        Saves tasks belonging to an objective to a file.
        """
        if dir:
            user_folder = dir
        else:
            user_folder = st.session_state.user_folder
        # Create a folder called objectives under user folder, if it doesn't exist
        objectives_folder = os.path.join(user_folder, 'objectives')
        if not os.path.exists(objectives_folder):
            os.makedirs(objectives_folder)
        print(f"Objectives folder: {objectives_folder}")
        # Save the current instance as a pickle file
        objective_file = os.path.join(objectives_folder, self.objective_name + '.dl')
        print(f"Objective file: {objective_file}")
        with open(objective_file, 'wb') as f:
            dl.dump(self, f)
        return None

    
    @classmethod
    def load_from_file(cls, objective_name, dir=None):
        """
        Loads an ObjectivesCoordinator instance from a file.
        """
        if dir:
            user_folder = dir
        else:
            user_folder = st.session_state.user_folder
        
        filename = os.path.join(user_folder, 'objectives', objective_name + '.dl')
        with open(filename, 'rb') as f:
            return dl.load(f)

    def add_task(self, task):
        """
        Adds a task to the list of tasks.
        
        Args:
            task: The task instance to be added.
        """
        self.tasks[task.task_name] = task
        # Update the status of the objective
        self.update_objective_status()
        return None
        
    
    def remove_task(self, task):
        """
        Removes a task from the list of tasks.
        
        Args:
            task: The task instance to be removed.
        """
        if task.task_name in self.tasks:
            del self.tasks[task.task_name]
        return None
        
        
      
    def update_task_status(self, task_name, status):
        """
        Updates the status of a task.
        
        Args:
            task_name: The name of the task to update the status for.  The task is a named tuple.
            status: The new status of the task.
        """
        if task_name in self.tasks:
            # Replace the task with the updated status
            # (We need replace because it is a named tuple)
            self.tasks[task_name] = self.tasks[task_name]._replace(status=status)
        return None
        
    
    def update_objective_status(self):
        """
        Sets the status of the first and last tasks as the statuses of the objective.
        """
        if len(self.tasks) > 0:
            self.status_first_task = self.tasks[list(self.tasks.keys())[0]].status
            self.status_last_task = self.tasks[list(self.tasks.keys())[-1]].status

        return None
