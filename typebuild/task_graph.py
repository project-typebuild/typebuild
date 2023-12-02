"""
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
import streamlit as st
from messages import Messages
from task import Task
class TaskGraph:
    def __init__(self, name=None, objective=None):
        self.graph = nx.DiGraph()
        self.graph.add_node('root', sequence=0, completed=False)
        self.name = name
        self.objective = objective
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
        time.sleep(2)
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
        # Check if current node task is incomplete
        if not graph.nodes[current_node]['complete']:
            return current_node
        
        # Sort children by sequence
        children = list(graph.successors(current_node))
        children.sort(key=lambda x: graph.nodes[x]['sequence'])
        
        # Check each child recursively
        for child in children:
            next_task = self.find_next_task(child)
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
        if start_node and start_node in self.graph:
            # next_task = self._find_next_task(start_node)
            next_task = self._find_next_incomplete_child(start_node)
            if next_task:
                return next_task
            else:
                st.warning(f"All tasks under '{start_node}' are completed or no tasks are available.")
                return None

        # Find the root node(s) (nodes with no predecessors)
        roots = [node for node in self.graph.nodes if self.graph.in_degree(node) == 0]
        for root in sorted(roots, key=lambda x: self.graph.nodes[x]['sequence']):
            next_task = self._find_next_task(root)
            if next_task:
                return next_task
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
    
    def _get_file_path(self):
        """
        Returns the file path of the graph.
        """

        return os.path.join(st.session_state.user_folder, 'objectives', f'{self.name}.pk')
    
    def _save_to_file(self):
        """
        Saves the graph to a file.
        """
        file_path = self._get_file_path()
        with open(file_path, 'wb') as file:
            pickle.dump(self.graph, file)
        return None

    def _load_from_file(self):
        """
        Loads a graph from a file.
        """
        file_path = self._get_file_path()
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, 'rb') as file:
            self.graph = pickle.load(file)
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
