from plugins.llms import get_llm_output
import pandas as pd
import networkx as nx
import json
import traceback
import pickle as pk
import os

class CategoryGraph:
    def __init__(self, file_name):
        # Initialize a directed graph to store the category relationships
        self.file_name = file_name
        self.graph = self._load_graph()

    def save_graph(self):
        """
        Save the graph to a file.
        """
        with open(self.file_name, 'wb') as f:
            pk.dump(self.graph, f)
    
    def _load_graph(self):
        """
        Load the graph from a file.
        """
        if os.path.exists(self.file_name):
            with open(self.file_name, 'rb') as f:
                self.graph = pk.load(f)
        else:
            self.graph = nx.DiGraph()
    
    def add_category(self, category_dict, parent_dict=None):
        """
        Add a category to the graph. 
        If a parent is specified, add an edge from the parent to the category.

        Parameters:
        - category_dict (dict): A dictionary where key is the category and value is the description.
        - parent_dict (dict, optional): A dictionary where key is the parent category and value is the description.
        """
        category, description = list(category_dict.items())[0]
        self.graph.add_node(category, description=description, analyzed=False)  # Add category with 'analyzed' property set to False
        if parent_dict:
            parent, parent_description = list(parent_dict.items())[0]
            if parent not in self.graph.nodes:
                self.graph.add_node(parent, description=parent_description, analyzed=False)
            self.graph.add_edge(parent, category)

    def add_categories(self, categories, parent=None):
        """
        Add multiple categories to the graph. If a parent is specified, add edges from the parent to the categories.
        """
        for category in categories:
            self.add_category(category, parent)

    def set_analyzed(self, category, analyzed=True):
        """
        Set the 'analyzed' property of a node to True or False.
        """
        if category in self.graph.nodes:
            self.graph.nodes[category]['analyzed'] = analyzed
        else:
            print(f"Category '{category}' not found in the graph.")

    def get_leaf_nodes(self):
        """
        Identify all the leaf nodes without children.
        """
        return [node for node in self.graph.nodes if self.graph.out_degree(node) == 0]

    def get_unanalyzed_leaf_nodes(self):
        """
        Identify leaf nodes that have not been analyzed.
        """
        return [node for node in self.get_leaf_nodes() if not self.graph.nodes[node]['analyzed']]

#==========LLM Functions=================
def get_unique_categories(df, category_column):
    """
    Given a dataframe and a category column, this function returns a list of unique categories.
    """
    unique_categories = set()
    for categories in df[category_column]:
        unique_categories.update(categories)
    return list(unique_categories)

def chunk_text_by_words(text, max_words):
    """
    Chunk text into chunks of max_words.
    It makes sure that sentences are not split across chunks.
    Also, adds the last sentence of the previous chunk to the next chunk.
    """

    chunks = []
    chunk = ''
    # Split the text into sentences
    sentences = text.split('.')
    # Remove empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    # Chunk the sentences
    for s in sentences:
        words_in_chunk = len(chunk.split())
        words_in_sentence = len(s.split())

        if words_in_chunk + words_in_sentence <= max_words:
            chunk += f"{s}. " if s else ""
        else:
            chunks.append(chunk)
            chunk = f"{s}. " if s else ""

    if chunk:
        chunks.append(chunk)
    
    return [c.strip() for c in chunks if c.strip()]

def dedupe_topics(topics_str):
    """
    Given a string with topics, this function dedupes using an llm 
    and returns new topics with a detailed description.
    """
    dedup_instructions = """Remove duplicates in the topics and return a clean list with topic name and a detailed description as a valid json.
    Use this format:
    [
        {"topic name": "detailed description of the topic"}
    ]
    """
    messages = [
        {"role": "system", "content": dedup_instructions},
        {"role": "user", "content": topics_str}
    ]
    content = get_llm_output(messages, max_tokens=1000, temperature=0.4, model='gpt-4-turbo', functions=[], json_mode=True)
    # Parse the json before sending
    try:
        content = json.loads(content)
    except Exception as e:
        content = []
        print(f"Error parsing the json: {e}")
    return content
    

def identify_topics(full_text):
    """
    Given a text, this function identifies all the topics in the given text
    """
    chunks = chunk_text_by_words(full_text, 1000)

    # System instruction.
    system_instruction = """Please analyze the following text in detail. Your task is to identify and extract all the major and minor topics covered in the text. 
    For each topic identified, consider the context, relevance, and how it contributes to the overall message or narrative of the text. 
    After you have identified the topics, organize them into a list, ensuring that each topic is clearly articulated and distinct from the others.
    Once you have compiled the list of topics, your final step is to format this list as a valid JSON array using this format:

    [
        {"topic name": "description of the category"},
    ]
    """
    topics = []

    for chunk in chunks:
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": chunk}
        ]
        output = get_llm_output(messages, max_tokens=1000, temperature=0.4, model='gpt-3.5-turbo', functions=[], json_mode=True)
        # Parse the json
        try:
            output = json.loads(output)
        except Exception as e:
            output = []
            print(f"Error parsing the json: {e}")
        topics.extend(output)
    
    if len(chunks) > 1:
        # Send all the topics to the LLM and consolidate them
        topics_str = '\n- '.join(topics)
        topics = dedupe_topics(topics_str)
    return topics

def categorize_row_by_row(selected_rows, categories):
    """
    Given a dataframe, a category column and a text column, this function
    helps with categorization.  It takes all the text with a selected cateogry.
    The new categories replace the selected category. 

    Parameters:
    - selected_rows (str): List of text to be categorized.
    - categories (list of dict): List of categories with description, where key is the category and value is the description.

    Returns:
    - categorized_rows (list of list): List of categories for each row.
    """
    # Identify the topics in the text
    out = []
    system_instruction = """You are helping me with a multiclass classification task.  Please categorize the following text into the given categories.  
    Return a valid JSON with the following format:

    {
        "category1": "description of the category",
        "category2": "description of the category",
        "category3": "description of the category",
        ...    
    }
    """
    for row in selected_rows:
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": row}
        ]
        output = get_llm_output(messages, max_tokens=1000, temperature=0.4, model='gpt-3.5-turbo', functions=[], json_mode=True)
        # Parse the json
        try:
            output = json.loads(output)
        except Exception as e:
            output = []
            print(f"Error parsing the json: {e}")
        out.append(output)
    return out


def categorize_selection(df, category_column, text_column, selected_category=None, graph_file=None):
    """
    Given a dataframe, a category column and a text column, this function
    helps with categorization.  It takes all the text with a selected cateogry.
    The new categories replace the selected category. 

    Parameters:
    - df (pd.DataFrame): The dataframe.
    - category_column (str): The name of the category column.  Cateogries are lists representing multiple classes.
    - text_column (str): The name of the text column.
    - selected_category (str): The category to be replaced.
    """
    
    # Identify rows that have the selected category
    if selected_category:
        selected_rows = df[df[category_column].apply(lambda x: selected_category in x)]
    # If selected category is None, select rows with no categories
    else:
        selected_rows = df[df[category_column].apply(lambda x: len(x) == 0)]

    # Identify the topics in the text, removing duplicates where necessary
    full_text = ' '.join(selected_rows[text_column].values)
    topics = identify_topics(full_text)
    # Load the graph and save the topics
    category_graph = CategoryGraph(graph_file)
    category_graph.add_categories(topics, parent=selected_category)
    category_graph.save_graph()

    # Categorized the selected rows
    row_categories = categorize_row_by_row(selected_rows[text_column].values, topics)
    
    # Replace the categories with the new categories
    # Start by getting the index of the selected rows
    selected_rows_index = list(selected_rows.index)
    for n,ind in enumerate(selected_rows_index):
        new_categories = row_categories[n]
        # Remove the selected category and replace with the new categories
        current_categories = df.at[ind, category_column]
        if selected_category:
            current_categories.remove(selected_category)
        current_categories.extend(new_categories)
        df.at[ind, category_column] = list(set(current_categories))
    
    return df

def process_dataframe(data_file, category_column, text_column, graph_file, selected_category=None):
    """
    Given a dataframe, a category column and a text column, this function
    helps with categorization.  It takes all the text with a selected cateogry (or all if selected category is None).
    The new categories replace the selected category. 

    Parameters:
    - data_file (str): The name of the file containing the dataframe.
    - category_column (str): The name of the category column.  Cateogries are lists representing multiple classes.
    - text_column (str): The name of the text column.
    - graph_file (str): The name of the file to save the graph.
    - selected_category (str): If not none, only the text with selected category is processed.
    """
    # Initialize the category graph
    category_graph = CategoryGraph(file_name=graph_file)
    df = pd.read_parquet(data_file)
    # If the category column does not exist, add it to the dataframe
    add_root_categories = False
    if category_column not in df.columns:
        df[category_column] = [[] for _ in range(len(df))]
        add_root_categories = True

    # If there are no categories, start by adding the root categories
    if add_root_categories:
        df = categorize_selection(df, category_column, text_column, selected_category=None, graph_file=graph_file)    

    # Analyze the text for unanalyzed leaf nodes
    while True:
        # Load the graph for possible updates
        category_graph = CategoryGraph(file_name=graph_file)
        leaf_nodes = category_graph.get_unanalyzed_leaf_nodes()
        if not leaf_nodes:
            print("No more leaf nodes to analyze.")
            break
        for category in leaf_nodes:
             df = categorize_selection(df, category_column, text_column, selected_category=category, graph_file=graph_file)
                
    return df    

