import streamlit as st

def get_nodes_data():
        
    G = st.session_state['menu'].G

    nodes = G.nodes()

    # convert to list
    nodes = list(nodes)

    nodes_string = "The nodes in the graph are down below:\n\n"
    # Join the nodes into a string
    nodes_string += ', '.join(nodes)

    return {'nodes': nodes}