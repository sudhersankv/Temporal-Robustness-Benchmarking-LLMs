# Temporal Reasoning in LLMs

This project is designed to test temporal reasoning capabilities in large language models (LLMs) using a set of test cases. The project involves converting raw test cases into JSON format, evaluating them using different LLMs, and displaying the results in a Streamlit app.

## Requirements

Before running the project, ensure you have the necessary Python packages installed. You can install them using the following command:

```bash
pip install -r requirements.txt
```

## Preparing Test Cases

1. **Format Raw Test Cases:**
   - Ensure your raw test cases are in the `raw_testcases` directory and follow the naming convention `set_n.txt`.

2. **Convert to JSON:**
   - Run the `txt-to-json.py` script to convert the raw test cases into JSON format.
   - This script will process the text files and save the JSON files in the `processed_testcases` directory.

   ```bash
   python txt-to-json.py
   ```

## Running the Evaluation

1. **Start the Streamlit App:**
   - Use the following command to start the Streamlit app, which will allow you to evaluate the test cases using different LLMs.

   ```bash
   streamlit run llm_evaluator_streamlit.py
   ```

2. **Select a Test Case:**
   - Use the sidebar in the Streamlit app to select a test case file from the `processed_testcases` directory.

3. **Evaluate:**
   - Choose a model (e.g., GPT-4, Gemini, LLaMA) to evaluate the test cases.
   - The app will display the questions, context, and model responses.

## Saving Results

- The evaluation results are saved automatically in the `evaluation_log.csv` file for further analysis.

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

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements.

## License

This project is licensed under the MIT License.
