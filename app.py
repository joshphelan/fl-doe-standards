"""
FL DOE Standards Chat Application
A Streamlit app for exploring Florida B.E.S.T. education benchmarks.
"""

import streamlit as st
from openai import OpenAI
import json
import logging
from src.excel_processor import process_excel_benchmarks, ExcelProcessingError
from src.utils import find_closest_benchmark, format_benchmark_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
EXCEL_PATH = "data/raw/BEST Math Extract.xlsx"
MODEL_PRICING = {
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
}

def load_benchmarks():
    """Load benchmarks from Excel file."""
    try:
        benchmarks = process_excel_benchmarks(EXCEL_PATH)
        logger.info(f"Successfully loaded {len(benchmarks)} benchmarks")
        return benchmarks
    except Exception as e:
        logger.error(f"Error loading benchmarks: {e}")
        st.error(f"Failed to load benchmarks: {str(e)}")
        return None

def generate_openai_response(benchmark_data, client):
    """Generate an AI-enhanced benchmark definition using OpenAI."""
    try:
        system_prompt = (
            "You are an expert assistant providing benchmark definitions of education standards. "
            "Use the provided benchmark data to provide an accurate definition.\n\n"
            "Your response should be structured in JSON format with the following keys:\n"
            "- 'benchmark_code': The exact benchmark code being defined.\n"
            "- 'definition': A word-for-word definition based on the benchmark data.\n"
            "- 'in_other_words': A brief, casual explanation for better understanding.\n"
            "- 'example': A simple example problem a teacher could use.\n\n"
            "Ensure clarity, consistency, and correctness."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Define the following benchmark: {benchmark_data.id}"},
                {"role": "assistant", "content": f"Relevant context:\n{benchmark_data.definition}"}
            ]
        )
        
        ai_response_text = response.choices[0].message.content
        ai_response = json.loads(ai_response_text)
        
        return ai_response, response.usage
        
    except Exception as e:
        logger.error(f"Error generating OpenAI response: {e}")
        return None, None

# ---- STREAMLIT UI ----
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

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Load benchmarks
benchmarks = load_benchmarks()

if benchmarks:
    # Search bar for user input
    user_query = st.text_input("Enter a benchmark:", placeholder="MA.K.NSO.1.1")

    if user_query:
        # Find matching benchmark
        matched_id, message = find_closest_benchmark(user_query, list(benchmarks.keys()))

        if matched_id:
            st.success(message)
            benchmark_data = benchmarks[matched_id]

            # Generate OpenAI response
            st.info("Generating AI-enhanced definition...")
            ai_response, usage = generate_openai_response(benchmark_data, client)

            if ai_response:
                # Display formatted response
                st.markdown(format_benchmark_response(ai_response))
                
                # Create collapsible section for source data
                with st.expander("Source Data"):
                    st.write(f"**Benchmark:** {benchmark_data.id}")
                    st.write(f"**Grade Level:** {benchmark_data.grade_level}")
                    st.write(f"**Definition:** {benchmark_data.definition}")

                # Update token usage and cost if available
                if usage:
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

        else:
            st.error(message)
