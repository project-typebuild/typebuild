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
import networkx as nx
import pickle
import streamlit as st

class TaskGraph:
    def __init__(self, name):
        self.graph = nx.DiGraph()
        self.name = name
    
    # TODO: Add other arguments to the constructor
    # TODO: Some nodes are just categories with children tasks that don't need to be done themselves.
    def add_task(self, task_name, sequence, completed=False):
        self.graph.add_node(task_name, sequence=sequence, completed=completed)

    def add_dependency(self, parent_task, child_task):
        if parent_task in self.graph and child_task in self.graph:
            self.graph.add_edge(parent_task, child_task)
        else:
            st.warning("Both tasks must exist in the graph to add a dependency.")

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
            next_task = self._find_next_task(start_node)
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
        with open(file_path, 'rb') as file:
            self.graph = pickle.load(file)
        return None

