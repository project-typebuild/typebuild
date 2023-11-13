import time
import networkx as nx
import streamlit as st
from streamlit_elements import elements, mui, html, sync
import streamlit as st




menu_edges_data = [
        ["HOME", "Users", "print_success"],
        ["Users", "User List", "print_success"],

        ["HOME", "Projects", "print_success"],
        ["Projects", "Project List", "print_success"],
        ["Project List", "View Projects", "print_success"],
        
        ["HOME", "Settings", "print_success"],
        ["Settings", "General Settings", "print_success"],

    ]




# set Streamlit page layout to wide
def display_menu_bar(menu_options):
    # create_dynamic_functions(menu_options)
    for index, option in enumerate(menu_options):
        # Create the function if it doesn't exist in locals
        # lower case and replace spaces with underscores and ~ with _
        clean_option = option.lower().replace(' ', '_').replace('~', '_').replace('.', '_').replace('-', '_').replace(',','_')
        if f"menu_button_function_{clean_option}" not in locals():
            myfunc = f"""def menu_button_function_{clean_option}(event):
                st.sidebar.warning(f"Button {option} clicked")
                st.session_state.activeStep = "{option}"
                st.session_state.should_rerun = True
                st.sidebar.info(f"Re-run is {st.session_state.should_rerun}")
                return None
            """            
            exec(myfunc)
    if 'activeStep' not in st.session_state:
        st.session_state.activeStep = 'HOME'        
    

    st.sidebar.info(f'Active step is {st.session_state.activeStep}')
    with elements("App Bar"):
        with mui.AppBar(position="relative", sx = {'borderRadius': 10}):
            with mui.Toolbar(disableGutters=True, variant="dense"):
                for index, option in enumerate(menu_options):
                    # lower case and replace spaces with underscores and ~ with _
                    clean_option = option.lower().replace(' ', '_').replace('~', '_').replace('.', '_').replace('-', '_').replace(',','_')
                    with mui.Grid(container=True, spacing=0):
                        mui.Button(color="inherit", onClick= eval(f'menu_button_function_{clean_option}'))(option.split('~')[0])
                        st.session_state.menu_displayed = True
    return None

class GraphicalMenu:
    menu_edges = []
    menu_sources = []
    source_functions = []
    G = None

    def __init__(self):
        return None

    def add_edges(self, menu_edges_data, source):
        """
        This adds nodes and edges to a graph.
        For uniqueness, the node names is done as "node_name~source"
        """
        if source not in self.menu_sources:
            self.menu_sources.append(source)
            revised_menu_edges_data = []
            for edge in menu_edges_data:
                if edge[0] == "HOME":
                    edge[0] = "HOME"
                else:
                    edge[0] = f"{edge[0]}~{source}"
                if edge[1] == "HOME":
                    edge[1] = "HOME"
                else:
                    edge[1] = f"{edge[1]}~{source}"
                revised_menu_edges_data.append([edge[0], edge[1]])
            self.menu_edges += menu_edges_data
            self.add_functions(revised_menu_edges_data, source)
            self.create_update_graph()
        return None

    def add_functions(self, edges, source):
        
        run = False
        for edge in edges:
            if len(edge) ==3:
                src, dst, func_name = edge
            else:
                dst = 'HOME'
                func_name = 'main'
                source = 'main'

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
        nodes = self.get_nodes_from_edges()
        
        roots = []
        for node in nodes:
            if node not in [edge[1] for edge in self.menu_edges if edge[0] != "HOME"]:
                roots.append(node)
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

    def create_update_graph(self):

        if self.G is None:
            G = nx.DiGraph()
        else:
            G = self.G
        # Add nodes
        G.add_nodes_from(self.get_nodes_from_edges())
        # Add edges if they exist
        menu_edges = [edge[:2] for edge in self.menu_edges if "HOME" not in edge]
        
        G.add_edges_from(menu_edges)
        # Add it to class variable
        self.G = G
        return None

    def get_children_and_parent(self, selected_node):
        G = self.G
        children = list(G.successors(selected_node))

        parent = "HOME" if not list(G.predecessors(selected_node)) else list(G.predecessors(selected_node))[0]
        return parent, children

    def get_ancestors(self, selected_node):
        G = self.G
        ancestors = list(nx.ancestors(G, selected_node))
        return ancestors
    
    def create_menu(self):
        if 'selected_node' not in st.session_state:
            st.session_state['selected_node'] = 'HOME'

        
        # If selected_node is HOME, get top level nodes
        options = ['HOME']
        if st.session_state['selected_node'] == 'HOME':
            options += self.top_level_nodes()

            st.sidebar.info('Here 1')
            # display_children = [option.split('~')[0] for option in options]
        else:
            st.error(st.session_state['selected_node'])
            parent, children = self.get_children_and_parent(st.session_state['selected_node'])
            # We will display the children without the ~ source
            # display_children = [child.split('~')[0] for child in children]
            # Add children to options
            st.sidebar.info('Here 2')
            st.sidebar.info(f'Children are {children}')
            options += children

        # RANU: THIS IS WHERE YOU PUT YOUR MENU SYSTEM
        # I am assuming that there will be parent and selected node
        st.sidebar.info(f'Options are {[i.split("~") for i in options]}')
        
        display_menu_bar(options)
        
        selected_option = st.session_state.activeStep

        if selected_option == 'HOME':
            st.session_state['selected_node'] = 'HOME'
        elif selected_option == 'SELECT':
            st.session_state.should_rerun = False
        else:
            st.session_state['selected_node'] = selected_option
        st.sidebar.warning(f"Re-run is {st.session_state.should_rerun}")
        

        if st.session_state.selected_node != 'HOME':
            ancestors = self.get_ancestors(st.session_state['selected_node'])
            # Show breadcrumbs
            breadcrumbs = " > ".join(ancestors + [st.session_state['selected_node']])
            st.markdown(f"**{breadcrumbs}**")
        
        if st.session_state.should_rerun == True:
            st.balloons()
            
            st.session_state.should_rerun = False
            st.rerun()