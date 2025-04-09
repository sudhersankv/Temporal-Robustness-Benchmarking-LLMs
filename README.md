# Temporal Reasoning in LLMs

This project is designed to evaluate the temporal reasoning capabilities of large language models (LLMs) using a structured set of test cases. The project involves converting raw test cases into a JSON format, evaluating them using different LLMs, and displaying the results in a Streamlit app.

## Prerequisites

- **Python 3.7+**: Ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/).
- **API Keys**: You will need API keys for OpenAI, Gemini, and Groq. These should be stored in a `.env` file in the root directory of the project.

## Installation

1. **Clone the Repository:**

   Clone this repository to your local machine using:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies:**

   Install the required Python packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

   This will install the following packages:
   - `streamlit`: For creating the web app interface.
   - `python-dotenv`: For loading environment variables from a `.env` file.
   - `openai`, `groq`, `google-generativeai`: For interacting with different LLM APIs.

## Preparing Test Cases

1. **Format Raw Test Cases:**

   Ensure your raw test cases are placed in the `raw_testcases` directory. Each file should follow the naming convention `set_n.txt`, where `n` is a number representing the test set.

2. **Convert to JSON:**

   Use the `txt-to-json.py` script to convert the raw test cases into JSON format. This script processes the text files and saves the JSON files in the `processed_testcases` directory.

   ```bash
   python txt-to-json.py
   ```

   - **Input Format**: The raw test cases should be structured with clear delimiters for different sections (e.g., questions, facts).
   - **Output Format**: The JSON files will contain structured data with keys like `system_prompt`, `fact_set`, and `questions`.

## Running the Evaluation

1. **Start the Streamlit App:**

   Launch the Streamlit app to evaluate the test cases using different LLMs.

   ```bash
   streamlit run llm_evaluator_streamlit.py
   ```

   - **Interface**: The app provides a user-friendly interface to select test cases and models for evaluation.

2. **Select a Test Case:**

   Use the sidebar in the Streamlit app to select a test case file from the `processed_testcases` directory. The app will load the selected file and display the questions and context.

3. **Evaluate:**

   Choose a model (e.g., GPT-4, Gemini, LLaMA) to evaluate the test cases. The app will display the model's responses alongside the questions and context.

   - **Model Selection**: The app allows you to switch between different models to compare their responses.
   - **Response Display**: The responses are displayed in real-time, allowing for immediate analysis.

## Saving Results

- The evaluation results are automatically saved in the `evaluation_log.csv` file. This file contains a log of all evaluations, including the model used, the questions, and the responses.

## Usage

This project can be used to:
- Test and compare the temporal reasoning capabilities of different LLMs.
- Analyze how different models respond to structured test cases.
- Provide insights into the strengths and weaknesses of various LLMs in understanding temporal contexts.

## Environment Variables

Ensure you have a `.env` file with the necessary API keys:

OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key


Replace `your_openai_api_key`, `your_gemini_api_key`, and `your_groq_api_key` with your actual API keys.
