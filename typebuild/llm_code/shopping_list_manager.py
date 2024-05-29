import streamlit as st
import pandas as pd
import requests


def load_data():
    """Load shopping list data from a CSV file."""
    url = "http://localhost:8000/get_data"
    params = {"file_name": "shopping_list"}
    response = requests.get(url, params=params)
    return pd.read_json(response.json())

def add_item(df, item):
    """Add a new item to the shopping list."""
    return df.append(item, ignore_index=True)

def remove_item(df, index):
    """Remove an item from the shopping list by index."""
    return df.drop(index=index).reset_index(drop=True)

def view_items(df):
    """Display the shopping list items, sorted by category."""
    sorted_df = df.sort_values(by='category')
    st.dataframe(sorted_df)

def main():
    df = load_data()
    st.title('Shopping List Manager')

    with st.expander('Add New Item'):
        # Input fields for adding a new item
        new_item = {'product_name': st.text_input('Product Name'),
                    'quantity': st.number_input('Quantity', min_value=0, value=1, step=1),
                    'category': st.text_input('Category'),
                    'who_for': st.text_input('Who For (Optional)', ''),
                    'where_to_get': st.text_input('Where To Get (Optional)', ''),
                    'to_buy': st.checkbox('To Buy', value=True)}
        if st.button('Add Item'):
            df = add_item(df, new_item)
            # df.to_csv(FILE_NAME, index=False)
            st.success('Item added successfully!')
            st.rerun()

    if st.button('View Sorted Items'):
        view_items(df)

