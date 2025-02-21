# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 18:55:00 2025

@author: josh
"""

import streamlit as st
import pickle
import re
from fuzzywuzzy import process
from openai import OpenAI
import json

# ---- CONFIGURATION ----
BENCHMARK_PATTERN = r'\b([A-Z]{2}\.(?:\d{1,3}|[A-Z])\.[A-Z]{1,3}\.\d+\.\d+)\b'
THRESHOLD = 80  # Fuzzy matching threshold
#OPENAI_MODEL = "gpt-4-turbo"
#model=OPENAI_MODEL

MODEL_PRICING = {
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},  # $0.01 per 1K input tokens, $0.03 per 1K output tokens
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}  # Cheaper model
}

# Load preprocessed data
with open("benchmark_lookup.pkl", "rb") as f:
    benchmark_to_doc = pickle.load(f)

# Initialize OpenAI API
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ---- FUNCTIONS ----
def normalize_benchmark_format(query):
    """Normalize user input format (replace dashes, underscores, spaces with dots)."""
    query = query.upper().strip()
    query = re.sub(r'[-_ ]', '.', query)  # Convert to dot notation
    return query if re.match(BENCHMARK_PATTERN, query) else None

def find_closest_benchmark(query, benchmark_list):
    """Finds the closest matching benchmark from dictionary."""
    best_match, score = process.extractOne(query, benchmark_list) if benchmark_list else (None, 0)
    return best_match if score >= THRESHOLD else None

def retrieve_benchmark_definition(query):
    """retrieval: first exact, then fuzzy"""
    normalized_benchmark = normalize_benchmark_format(query)

    if not normalized_benchmark:
        return None, "Invalid benchmark format."

    # 1. Exact lookup
    if normalized_benchmark in benchmark_to_doc:
        return benchmark_to_doc[normalized_benchmark], f"Exact match found for {normalized_benchmark}."

    # 2. Fuzzy matching
    closest_benchmark = find_closest_benchmark(normalized_benchmark, list(benchmark_to_doc.keys()))
    if closest_benchmark:
        return benchmark_to_doc[closest_benchmark], f"Did you mean {closest_benchmark}?"

    return None, "No matching benchmark found."

def generate_openai_response(user_query, retrieved_chunk):
    """Generates an AI-enhanced benchmark definition using OpenAI."""    
    system_prompt = (
    "You are an expert assistant providing benchmark definitions of education standards. "
    "Use the retrieved text to provide an accurate definition of the benchmark.\n\n"
    "Your response should be structured in JSON format with the following keys:\n"
    "- 'benchmark_code': The exact benchmark code being defined.\n"
    "- 'definition': A word-for-word definition based on the retrieved text.\n"
    "- 'in_other_words': A brief, casual explanation for better understanding that would allow someone with no background to understand.\n"
    "- 'example': A simple example problem a teacher could use to teach their students. Stay true to the word-for-word definition provided.\n\n"
    "Ensure clarity, consistency, and correctness."
)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Define the following benchmark: {user_query}"},
            {"role": "assistant", "content": f"Relevant context:\n{retrieved_chunk}"}
        ]
    )
    
    ai_response_text = response.choices[0].message.content  # Extract the AI response
    
    try:
        ai_response = json.loads(ai_response_text)  # Parse JSON response
    except json.JSONDecodeError:
        st.error("Error: The AI response was not in JSON format.")
        return None, None  # Return None to avoid further errors
    
    # Extract token usage
    token_usage = response.usage if hasattr(response, "usage") else None  # Handle missing usage field
    
    return ai_response, token_usage

def format_response(ai_response):
    """Formats the AI response with headers and spacing."""
    if not ai_response:
        return "Error: No valid response received."

    # Start with the Definition and In Other Words sections
    formatted_output = (
        f"**Definition:** {ai_response['benchmark_code']}: {ai_response['definition']}\n\n"
        f"**In Other Words:**\n{ai_response['in_other_words']}\n\n"
    )

    # Handle Example: Check if it's a dictionary with 'problem' and 'solution'
    example = ai_response.get('example')
    if isinstance(example, dict) and 'problem' in example and 'solution' in example:
        formatted_output += (
            f"**Example:**\n\n"
            f"**Problem:** {example['problem']}\n\n"
            f"**Solution:** {example['solution']}\n\n"
        )
    else:
        formatted_output += f"**Example:**\n{example}\n\n"
    return formatted_output


# ---- STREAMLIT UI ----
# Set up page title and description
st.title("FL DOE Standards Chatbot 💬 📚")
st.write("Enter a Florida B.E.S.T. benchmark (e.g., `MA.K.NSO.1.1`) to retrieve its definition.")

# Sidebar for model selection and token usage tracking
with st.sidebar:
    st.header("Settings ⚙️")
    st.markdown("🔗 [Link](https://www.fldoe.org/academics/standards/subject-areas/math-science/mathematics/) to Florida B.E.S.T. Mathematics standards")

    # Model selection
    model = st.selectbox("Choose a model:", ["gpt-3.5-turbo", "gpt-4-turbo"])

    # Initialize session state for cost tracking
    if "total_cost" not in st.session_state:
        st.session_state.total_cost = 0.0

    # Display accumulated token usage and cost
    st.subheader("💰 Token Usage & Cost")
    #st.write(f"**Total Session Cost:** ${st.session_state.total_cost:.6f}")

# Search bar for user input
user_query = st.text_input("Enter a benchmark:",placeholder="MA.K.NSO.1.1")

if user_query:
    retrieved_doc, message = retrieve_benchmark_definition(user_query)

    if retrieved_doc:
        st.success(message)
        #st.write(f"**Benchmark:** {retrieved_doc.metadata.get('benchmark')}")
        #st.write(f"**Retrieved Context:** {retrieved_doc.page_content}")

        # Generate OpenAI response
        st.info("Generating AI-enhanced definition...")
        ai_response, usage = generate_openai_response(retrieved_doc.metadata["benchmark"], retrieved_doc.page_content)
        #st.write(ai_response)
        # Display formatted response
        st.markdown(format_response(ai_response))
        
        # Create collapsible sections for Retrieved Content        
        with st.expander("Retrieved Context"):
            st.write(f"**Benchmark:** {retrieved_doc.metadata.get('benchmark')}")
            st.write(f"**Page:** {retrieved_doc.metadata.get('page')+13}")
            st.write(f"**Retrieved Context:** {retrieved_doc.page_content}")

        # Extract token usage details
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        # Calculate request cost
        input_cost = (prompt_tokens / 1000) * MODEL_PRICING[model]["input"]
        output_cost = (completion_tokens / 1000) * MODEL_PRICING[model]["output"]
        request_cost = input_cost + output_cost

        # Update session cost
        st.session_state.total_cost += request_cost

        # Display token usage and cost in the sidebar
        with st.sidebar:
            st.write(f"**Total Session Cost:** ${st.session_state.total_cost:.6f}")
            st.write(f"🔹 **Last Request Cost:** ${request_cost:.6f}")
            st.write(f"🔹 **Prompt Tokens:** {prompt_tokens}")
            st.write(f"🔹 **Completion Tokens:** {completion_tokens}")
            st.write(f"🔹 **Total Tokens:** {total_tokens}")
            #st.write(f"💰 **Updated Total Session Cost:** ${st.session_state.total_cost:.6f}")

    else:
        st.error(message)
