import streamlit as st
from vector_utils import VectorManager
from typing import List, Dict
import pandas as pd
import json
import logging

class ContentManager:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def validate_context_data(self, data):
        """Validate the structure of context data"""
        required_fields = ['text', 'source', 'keywords']
        for item in data:
            if not all(field in item for field in required_fields):
                return False
        return True

    def load_context_data(self, filename):
        """Load and validate context data from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            if self.validate_context_data(data):
                return data
            else:
                logging.error("Invalid context data structure")
                return None
        except Exception as e:
            logging.error(f"Error loading context data: {e}")
            return None

def main():
    st.set_page_config(
        page_title="Vector Database Content Manager",
        page_icon="🗄️",
        layout="wide"
    )

    st.title("Vector Database Content Manager")
    st.markdown("---")

    # Initialize VectorManager
    try:
        vector_manager = VectorManager()
        st.success("Successfully connected to vector database")
    except Exception as e:
        st.error(f"Error connecting to vector database: {e}")
        st.warning("Please make sure you have set up the correct API keys in .env file")
        return

    # Sidebar
    st.sidebar.title("Operations")
    operation = st.sidebar.radio(
        "Select Operation",
        ["Add Single Content", "Add Batch Content", "Search Content", "Delete Content"]
    )

    if operation == "Add Single Content":
        st.header("Add Single Content")
        
        content = st.text_area("Enter content", height=200)
        
        # Optional metadata
        st.subheader("Metadata (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            key = st.text_input("Metadata Key")
        with col2:
            value = st.text_input("Metadata Value")
        
        if st.button("Add Content"):
            if content:
                metadata = {key: value} if key and value else None
                vector_id = vector_manager.add_content(content, metadata)
                if vector_id:
                    st.success(f"Content added successfully! Vector ID: {vector_id}")
                else:
                    st.error("Failed to add content")
            else:
                st.warning("Please enter some content")

    elif operation == "Add Batch Content":
        st.header("Add Batch Content")
        
        uploaded_file = st.file_uploader("Upload CSV file", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df.head())
            
            if "content" not in df.columns:
                st.error("CSV must contain a 'content' column")
                return
            
            if st.button("Add Batch Content"):
                contents = df["content"].tolist()
                
                # Extract metadata if present
                metadata_list = []
                metadata_columns = [col for col in df.columns if col != "content"]
                for _, row in df.iterrows():
                    metadata = {col: row[col] for col in metadata_columns}
                    metadata_list.append(metadata)
                
                vector_ids = vector_manager.add_batch_content(contents, metadata_list)
                if vector_ids:
                    st.success(f"Added {len(vector_ids)} items successfully!")
                else:
                    st.error("Failed to add batch content")

    elif operation == "Search Content":
        st.header("Search Content")
        
        query = st.text_input("Enter search query")
        top_k = st.slider("Number of results", 1, 10, 3)
        
        if st.button("Search"):
            if query:
                results = vector_manager.search_similar(query, top_k)
                if results:
                    for i, result in enumerate(results, 1):
                        st.subheader(f"Result {i} (Score: {result['score']:.4f})")
                        st.text_area("Content", result["content"], height=100, key=f"content_{i}")
                        if result["metadata"]:
                            st.json(result["metadata"])
                        st.markdown("---")
                else:
                    st.warning("No results found or error occurred")
            else:
                st.warning("Please enter a search query")

    elif operation == "Delete Content":
        st.header("Delete Content")
        
        vector_ids = st.text_area("Enter vector IDs (one per line)")
        
        if st.button("Delete"):
            if vector_ids:
                ids = [id.strip() for id in vector_ids.split("\n") if id.strip()]
                if vector_manager.delete_vectors(ids):
                    st.success(f"Successfully deleted {len(ids)} vectors")
                else:
                    st.error("Failed to delete vectors")
            else:
                st.warning("Please enter vector IDs")

if __name__ == "__main__":
    main()
