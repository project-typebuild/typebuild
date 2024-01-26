"""
- TODO: Assign task to Dhruv to serialize to JSON.
- Add decision nodes and logic.
- Figure out which task will respond to the user.
- How do we model orchestration (between each transition).
- Tasks can be completed via UI or chat.
- How do we add tasks dynamically during a task (not setting a new node under a completed node).
- Allow users to revisit tasks, undo completion.  (Find next only provides the next task to complete, not the next task to visit.)
- Allow users to navigate to previous steps at any time via the UI or chat.
"""

import os
import time
import networkx as nx
import pickle
import dill as dl
import json
import streamlit as st
from messages import Messages
from task import Task


class TaskGraph:
    def __init__(self, name=None, objective=None):
        self.graph = nx.DiGraph()
        self.graph.add_node('root', sequence=0, completed=False)
        self.name = name
        # Description of the objective
        self.objective = objective

        # Templates with name and instruction
        self.templates = {}
        # An instance of the message class to hold all the 
        # messages for this task graph
        self.messages = Messages(name)
        # If true, this conversation is sent to the planner.
        self.send_to_planner = True
    
    def add_task(self, task_name, task_description, agent_name, parent_task=None, sequence=None, available_agents=[], decision_function=None, **kwargs):
        """
        Adds a node to the graph. The node can be a regular task or a decision node,
        depending on the 'decision' flag and additional keyword arguments.

        Args:
            task_name: The name of the task to add.
            task: Text describing the task to be given to the language model.
            sequence: The sequence number of the node.
            completed: Whether the node is completed.
            decision_function: The function to call if this is a decision node.
            **kwargs: Additional keyword arguments for decision nodes.
        """
        if kwargs.get('before_task') and not parent_task:
            parent_task = self.find_parent(kwargs['before_task'])
        
        if kwargs.get('after_task') and not parent_task:
            parent_task = self.find_parent(kwargs['after_task'])

        if not parent_task:
            parent_task = 'root'
        if not sequence:
            sequence = self.calculate_sequence_number(parent_task)
        node_attributes = {
            'sequence': sequence,
            'completed': False,
            'decision_function': decision_function,
            'task': Task(
                task_name=task_name, 
                task_description=task_description,
                agent_name=agent_name, 
                available_agents=available_agents
                ),
        }

        if decision_function and not kwargs.get('branches', None):
            raise Exception("Decision nodes must have branches.")
        # Add additional attributes for decision nodes
        if kwargs:
            node_attributes.update(kwargs)

        self.graph.add_node(task_name, **node_attributes)
        # Add a parent task. If there's no parent, add a root node.
        self.add_parent(task_name, parent_task)
        # Provide confirmation
        st.success(f"Added task '{task_name}' to the graph.")
        return None

    def calculate_sequence_number(self, parent_task, before_node=None, after_node=None):
        """
        Calculates a non-conflicting sequence number for a new node based on the specified parameters.
        """
        def find_gap(sequences, start, increment):
            seq = start
            while seq in sequences:
                seq += increment
            return seq

        sibling_sequences = [self.graph.nodes[sib]['sequence'] for sib in self.graph.successors(parent_task)]

        if not sibling_sequences:
            return 1
        elif before_node and before_node in self.graph:
            before_sequence = self.graph.nodes[before_node]['sequence']
            return find_gap(sibling_sequences, before_sequence - 0.1, -0.01)
        elif after_node and after_node in self.graph:
            after_sequence = self.graph.nodes[after_node]['sequence']
            return find_gap(sibling_sequences, after_sequence + 0.1, 0.01)
        else:
            return max(sibling_sequences, default=0) + 1


    def find_parent(self, node_name):
        """
        Finds the parent of the given node. Returns the parent node's name,
        or None if the node has no parent or does not exist.
        """
        if node_name in self.graph:
            for parent, child in self.graph.edges():
                if child == node_name:
                    return parent
        return None

    def _get_successors_and_predecessors(self, node_name):
        """
        Returns the successors and predecessors of the given node,
        and that node itself in a list.
        """
        successors = list(self.graph.successors(node_name))
        predecessors = list(self.graph.predecessors(node_name))
        return [node_name] + successors + predecessors

    def get_messages_for_task(self, task_name):
        """
        Returns the messages for the given task.
        """
        return self.messages.get_messages_for_task(task_name)
    
    def get_messages_for_task_family(self, task_name):
        """
        Returns the messages for the given task and its ancestors and descendants.
        """
        if task_name in self.graph:
            task_family = self._get_successors_and_predecessors(task_name)
            return self.messages.get_messages_for_task_family(task_family)
        else:
            return []


    def add_dependency(self, parent_task, child_task):
        if parent_task in self.graph and child_task in self.graph:
            self.graph.add_edge(parent_task, child_task)
        else:
            st.warning("Both tasks must exist in the graph to add a dependency.")
    
    def add_parent(self, child_task, parent_task=None):
        if child_task in self.graph:
            if parent_task:
                self.graph.add_edge(parent_task, child_task)
            else:
                self.graph.add_edge('root', child_task)
        else:
            st.warning("The child task must exist in the graph to add a parent.")
        return None

    def update_task(self, task_name, sequence=None, completed=None, other_attributes={}):
        if task_name in self.graph:
            if sequence is not None:
                self.graph.nodes[task_name]['sequence'] = sequence
            if completed is not None:
                self.graph.nodes[task_name]['completed'] = completed
            for key in other_attributes:
                self.graph.nodes[task_name][key] = other_attributes[key]
        else:
            st.warning("Task not found in the graph.")

    # TODO: Document why we need this and get_next_task.
    def _find_next_task(self, node):
        """
        Helper method to recursively find the next task to complete.
        """
        # If the current node is not completed, check its children
        if not self.graph.nodes[node]['completed']:
            children = sorted(self.graph.neighbors(node), key=lambda x: self.graph.nodes[x]['sequence'])
            for child in children:
                next_task = self._find_next_task(child)
                # If a child or its descendant is incomplete, return it
                if next_task:
                    # Return the first incomplete child that is found
                    return next_task
            # If all children are complete, return the current node
            return node
        # If the current node is completed, return None
        return None

    def _find_next_task(self, node):
        if not self.graph.nodes[node]['completed']:
            if self.graph.nodes[node].get('decision', None):
                condition = self.graph.nodes[node]['condition']
                outcome = condition()
                next_branch = self.graph.nodes[node]['branches'][outcome]
                return self._find_next_task(next_branch)
            else:
                for neighbor in sorted(self.graph.neighbors(node), key=lambda x: self.graph.nodes[x]['sequence']):
                    next_task = self._find_next_task(neighbor)
                    if next_task:
                        return next_task
                return node
        return None

    def _find_next_incomplete_child(self, current_node=None):
        """
        This checks if the current node is complete. If it is, it checks its children.
        It returns the first incomplete child that it finds, or None if all children are complete.
        Uses a depth-first search.

        Args:
            current_node: The node to start the search from. If not given, start from the root.

        Returns:
            next_node: The next node to complete or None
        """
        if not current_node:
            current_node = 'root'
        
        graph = self.graph
        # Check if current node task is incomplete and is not root
        if not graph.nodes[current_node]['completed'] and current_node != 'root':
            return current_node
        
        # Sort children by sequence
        children = list(graph.successors(current_node))
        children.sort(key=lambda x: graph.nodes[x]['sequence'])
        
        # Check each child recursively
        for child in children:
            next_task = self._find_next_incomplete_child(child)
            if next_task:
                return next_task
        return None

    def get_next_task(self, start_node=None):
        """
        Public method to find the next task to complete. 
        If start_node is given, start from there, else start from the root.

        Args:
            start_node: The node from which to start the search. If not given, start from the root.

        Returns:
            next_node: The next node to complete or None
        """
        if not start_node:
            start_node = 'root'

        if start_node and start_node in self.graph:
            # next_task = self._find_next_task(start_node)
            next_task = self._find_next_incomplete_child(start_node)
            if next_task:
                return next_task
            else:
                
                return None

        st.warning("All tasks are completed or no tasks are available.")
        return None

    def get_next_task_node(self, start_node=None):
        """
        Public method to find the next task to complete. 
        If start_node is given, start from there, else start from the root.

        Args:
            start_node: The node from which to start the search. If not given, start from the root.

        Returns:
            next_node: The next node to complete or None
        """
        # next_task = self.get_next_task(start_node)
        next_task = self._find_next_incomplete_child(start_node)
        if next_task:
            return self.graph.nodes[next_task]
        else:
            return None
        

    def convert_dicts_to_tasks(self, graph_dict):
        """
        Converts the dictionaries in a graph to Task instances.
        """
        # Create a new DiGraph
        new_graph = nx.DiGraph()

        # Iterate over the nodes in the graph_dict
        for node, data in graph_dict.items():
            # Check if the 'task' key is a dictionary
            if isinstance(data.get('task'), dict):
                # Check if the dictionary contains the required keys
                if all(key in data['task'] for key in ['task_name', 'task_description', 'agent_name', 'available_agents']):
                    # Convert the dictionary to a Task instance
                    data['task'] = Task(**data['task'])

            # Add the node to new_graph
            new_graph.add_node(node, **data)

        # Return the new DiGraph
        return new_graph

    def convert_tasks_to_dict(self):
        """
        Converts all the Task instances in a graph to dictionaries.
        """
        # Create a new dictionary
        new_graph_dict = {}

        # Iterate over the nodes in the graph
        for node, data in self.graph.nodes(data=True):
            data_copy = data.copy()
            # Check if the 'task' key is a Task instance
            if isinstance(data_copy.get('task'), Task):
                # Convert the Task instance to a dictionary
                data_copy['task'] = data_copy['task'].__dict__

            # Add the node to new_graph_dict
            new_graph_dict[node] = data_copy

        # Return the new dictionary
        return new_graph_dict


    def _get_file_path(self):
        """
        Returns the file path of the graph.
        """
        path = os.path.join(st.session_state.user_folder, 'objectives', f'{self.name}.dl')
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        return path
    
    def _get_file_path_json(self):
        """
        Returns the file path of the graph.
        """
        path = os.path.join(st.session_state.user_folder, 'objectives', f'{self.name}.json')
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        return path
    
    def _save_to_json(self):
        """
        Saves the graph to a json file.
        """
        # Can save only if the graph has a name
        if not self.name:
            st.warning("The graph must have a name to save.  Let's try again once we start the task.")
            
        else:
            file_path = self._get_file_path_json()
            graph_dict = self.convert_tasks_to_dict()

            messages_dict = self.messages.export_all_messages()
            attributes = {
                'name': self.name,
                'objective': self.objective,
                'graph': graph_dict,
                'messages': messages_dict,
                'templates': self.templates,
                'send_to_planner': self.send_to_planner
            }

            with open(file_path, 'w') as file:
                # Dump the data to the file
                json.dump(attributes, file)
                
        return None
    
    def _save_to_file(self):
        """
        Saves the graph to a file.
        """
        # Can save only if the graph has a name
        if not self.name:
            st.warning("The graph must have a name to save.  Let's try again once we start the task.")
            
        else:
            file_path = self._get_file_path()
            # Save with dill to preserve functions
            with open(file_path, 'wb') as file:
                # Get all the attributes as a dict
                attributes = self.__dict__
                # Save it as dill
                dl.dump(attributes, file)
                
        return None

    # TODO: add a version that saves to json

    def _load_from_json(self):
        """
        Loads a graph from a json file.
        """
        # Get a list of files in the objectives folder
        path = os.path.join(st.session_state.user_folder, 'objectives')
        # check if the folder exists and create it if it doesn't
        if not os.path.exists(path):
            os.makedirs(path)
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        # Filter out files that don't end with .json
        files = [f for f in files if f.endswith('.json')]
        if files:
            st.header("Load task graph")
            # Add a blank option to the list
            files.insert(0, 'SELECT')
            # Display a selectbox to choose the file
            file_name = st.selectbox("Select to load", files)
            if file_name == 'SELECT':
                st.warning("Please select a file to load.")
                return None
            else:
                file_path = os.path.join(path, file_name)
                if st.button("Load"):
                    # Load with json
                    with open(file_path, 'r') as file:
                        attributes = json.load(file)
                    # Assign the attributes to the current graph
                    for key, value in attributes.items():
                        if key == 'graph':
                            # Convert the dictionaries in the graph to Task instances
                            value = self.convert_dicts_to_tasks(value)
                        elif key == 'messages':
                            # Create a new Messages instance without specifying a task name
                            messages = Messages(self.name)

                            # Iterate over the list of dictionaries
                            dicts = value
                            for dict_obj in dicts:
                                # Create a message_tuple instance
                                message = messages.message_tuple(**dict_obj)
                                # Append the message_tuple instance to the messages attribute
                                messages.messages.append(message)
                            
                            # Assign the messages attribute to the current graph
                            value = messages
                        setattr(self, key, value)

                    st.success(f"Loaded graph from '{file_name}'.")
                    st.rerun()
        return None

    # Deprecated
    def _load_from_file(self):
        """
        Loads a graph from a file.
        """
        # Get a list of files in the objectives folder
        path = os.path.join(st.session_state.user_folder, 'objectives')
        # check if the folder exists and create it if it doesn't
        if not os.path.exists(path):
            os.makedirs(path)
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if files:
            st.header("Load task graph")
            # Add a blank option to the list
            files.insert(0, 'SELECT')
            # Display a selectbox to choose the file
            file_name = st.selectbox("Please select file to load", files)
            if file_name == 'SELECT':
                st.warning("Please select a file to load.")
                return None
            else:
                file_path = os.path.join(path, file_name)
                if st.button("Load"):
                    # Load with dill to preserve functions
                    with open(file_path, 'rb') as file:
                        attributes = dl.load(file)
                    # Assign the attributes to the current graph
                    self.__dict__.update(attributes)
                    st.success(f"Loaded graph from '{file_name}'.")
                    st.rerun()
        return None

    def rename(self, new_name):
        """
        Renames the graph and the file, if it exists.
        """
        if new_name:
            # Rename the file and graph
            old_file_path = self._get_file_path()
            self.name = new_name
            new_file_path = self._get_file_path()
            if os.path.exists(old_file_path):
                os.rename(old_file_path, new_file_path)
            st.success(f"Renamed graph to '{new_name}'.")
            time.sleep(2)

        return None

    def generate_markdown(self):
        """
        Generates a markdown text from the task graph with hierarchical tasks.
        """
        md_text = f'# {self.name}\n\n'
        def format_task(node, level=0):
            task_info = self.graph.nodes[node]
            md_line = f"{'  ' * level}- **{node}**: {task_info.get('task', {})}\n"
            for child in sorted(self.graph.successors(node), key=lambda x: self.graph.nodes[x]['sequence']):
                md_line += format_task(child, level + 1)
            return md_line

        for node in [n for n, d in self.graph.in_degree() if d == 0]:  # Root nodes
            md_text += format_task(node)
        return md_text

    def get_attributes_of_ancestors(self, current_task):
        """
        Returns the attributes of the ancestors of the current task
        as a flattened dictionary.
        """
        ancestors = list(nx.ancestors(self.graph, current_task))
        if current_task not in ancestors:
            ancestors.append(current_task)
        attributes = {}
        for ancestor in ancestors:
            attributes.update(self.graph.nodes[ancestor])
        return attributes