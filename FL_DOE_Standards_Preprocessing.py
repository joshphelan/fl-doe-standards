# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 16:40:37 2024

@author: josh
"""

import re
import pickle
import os
import sys
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import streamlit as st

# Set path
sys.path.append('../..')
path = "C:/Users/josh/OneDrive/Documents/Projects/fl-doe-standards"
os.chdir(path)

# Set open AI API key
#os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["api_key"]


# ---- CONFIGURATION ----
PDF_PATH = "data/mathbeststandardsfinal_standards.pdf"
BENCHMARK_PATTERN = r'\b([A-Z]{2}\.(?:\d{1,3}|[A-Z])\.[A-Z]{1,3}\.\d+\.\d+)\b'

# ---- FUNCTIONS ----
def extract_benchmark(text):
    """Extracts the first valid benchmark from a text chunk."""
    matches = re.findall(BENCHMARK_PATTERN, text)
    return matches[0] if matches else None

# Load and chunk the document
loader = PyPDFLoader(PDF_PATH)
documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

# Create lookup dictionary and metadata
benchmark_to_doc = {}
docs_with_metadata = []

for chunk in chunks:
    benchmark = extract_benchmark(chunk.page_content)
    if benchmark:
        chunk.metadata["benchmark"] = benchmark
        benchmark_to_doc[benchmark] = chunk
        docs_with_metadata.append(chunk)

# Save processed data
with open("benchmark_lookup.pkl", "wb") as f:
    pickle.dump(benchmark_to_doc, f)