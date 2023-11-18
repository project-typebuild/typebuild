import time
import networkx as nx
import streamlit as st
from streamlit_elements import elements, mui, html, sync
import streamlit as st


# set Streamlit page layout to wide
def display_menu_bar(menu_options):
    # create_dynamic_functions(menu_options)
    for index, option in enumerate(menu_options):
        # Create the function if it doesn't exist in locals
        # lower case and replace spaces with underscores and ~ with _
        clean_option = option.lower().replace(' ', '_').replace('~', '_').replace('.', '_').replace('-', '_').replace(',','_')
        if f"menu_button_function_{clean_option}" not in locals():
            myfunc = f"""def menu_button_function_{clean_option}(event):
                st.session_state.activeStep = "{option}"
                st.session_state.should_rerun = True
                return None
            """            
            exec(myfunc)
    if 'activeStep' not in st.session_state:
        st.session_state.activeStep = 'HOME'     
    
    unique_labels = []
    for option in menu_options:
        label = option.split('~')[0]
        if label not in unique_labels:
            unique_labels.append(label)

    with elements(st.session_state.activeStep):
        with mui.AppBar(position="relative", sx = {'borderRadius': 10}, key=f"{st.session_state.activeStep}_appbar"):
            with mui.Toolbar(disableGutters=True, variant="dense"):
                for index, option in enumerate(menu_options):
                    # lower case and replace spaces with underscores and ~ with _
                    clean_option = option.lower().replace(' ', '_').replace('~', '_').replace('.', '_').replace('-', '_').replace(',','_')
                    with mui.Grid(container=True, spacing=0):
                        mui.Button(color="inherit", onClick= eval(f'menu_button_function_{clean_option}'))(option.split('~')[0])
                        st.session_state.menu_displayed = True
    return None

class GraphicalMenu:
    # menu_edges = []
    # menu_sources = []
    # source_functions = []
    G = None

    def __init__(self):
        # Create the Graph
        self.G = nx.DiGraph()
        self.G.add_node("HOME", node_name="HOME", func_name="home_page", module_name="home_page")
        return None

    def add_edges(self, menu_edges_data):
        """
        This adds nodes and edges to a graph.
        For uniqueness, the node names is done as "node_name~source"
        """

        G = self.G
        # revised_menu_edges_data = []

        for edge in menu_edges_data:
            source = edge[-1]  # Get the source from the last item in the sublist
            # if source not in self.menu_sources:
            #     self.menu_sources.append(source)

            if edge[0] == "HOME":
                node_0 = "HOME"
            else:
                node_0 = f"{edge[0]}~{source}"

            if edge[1] == "HOME":
                node_1 = "HOME"
            else:
                node_1 = f"{edge[1]}~{source}"

            # Add the edge to the graph with the function name and module name as properties
            if node_1 not in G.nodes:
                G.add_node(node_1, node_name=edge[1], func_name=edge[2], module_name=source)
            G.add_edge(node_0, node_1)
            # revised_menu_edges_data.append([node_0, node_1])

        return None


    def add_functions(self, edges):
        
        run = False
        for edge in edges:
            if len(edge) == 3:
                src, dst, func_name = edge
            else:
                dst = 'HOME'
                func_name = 'home_page'
                source = 'home_page'

            node_name = f"{dst}~{source}"
            # Append if the node name is not already in the source functions
            if node_name not in [func[0] for func in self.source_functions]:
                self.source_functions.append([node_name, source, func_name, run])

    def add_menu_items(self, menu_data, source):
        if source not in self.menu_sources:
            self.menu_sources.append(source)
            self.menu_edges += menu_data
        return None
    
    def top_level_nodes(self):
        """
        Get the top level nodes from a list of edges.  These are the nodes that have no parents.
        """
        G = self.G
        # Get children of "HOME"
        roots = [n for n in G.successors("HOME")]
        return roots

    def get_nodes_from_edges(self):
        nodes = set()
        for edge in self.menu_edges:
            # Get the source and destination nodes only.  
            # The third element is the function name
            edge = edge[:2]
            for node in edge:
                if node != "HOME":
                    nodes.add(node)
        return list(nodes)


    def get_children_and_parent(self, selected_node):
        G = self.G
        children = list(G.successors(selected_node))

        parent = "HOME" if not list(G.predecessors(selected_node)) else list(G.predecessors(selected_node))[0]
        return parent, children

    def get_ancestors(self, selected_node):
        G = self.G
        ancestors = list(nx.ancestors(G, selected_node))
        # Reverse the ancestors
        ancestors.reverse()
        # Add the current node name
        current_node_name = G.nodes[selected_node].get('node_name')
        ancestors.append(current_node_name)
        return ancestors

    def get_module_and_function(self, selected_node):
        """
        Get the module and function name from the selected node.
        """
        # Get the list with the selected node from the menu
        node_info = [node for node in self.source_functions if node[0] == selected_node][0]
        module_name = node_info[1].split('~')[1]
        func_name = node_info[2]
        return module_name, func_name

    def create_menu(self):
        if 'selected_node' not in st.session_state:
            st.session_state['selected_node'] = 'HOME'

        
        # If selected_node is HOME, get top level nodes
        options = ['HOME']
        if st.session_state['selected_node'] == 'HOME':
            options += self.top_level_nodes()

            # display_children = [option.split('~')[0] for option in options]
        else:
            parent, children = self.get_children_and_parent(st.session_state['selected_node'])
            options += children
        # Display the options
        display_menu_bar(options)
        
        selected_option = st.session_state.activeStep

        if selected_option == 'HOME':
            st.session_state['selected_node'] = 'HOME'
        elif selected_option == 'SELECT':
            st.session_state.should_rerun = False
        else:
            st.session_state['selected_node'] = selected_option
        

        if st.session_state.selected_node != 'HOME':
            ancestors = self.get_ancestors(st.session_state['selected_node'])
            
            # Show breadcrumbs
            breadcrumbs = " > ".join(ancestors)
            st.markdown(f"**{breadcrumbs}**")
        
        if st.session_state.should_rerun == True:
            st.session_state.should_rerun = False
            st.rerun()