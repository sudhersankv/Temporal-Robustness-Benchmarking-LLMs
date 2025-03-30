import streamlit as st
import json
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
import openai
from groq import Groq
import google.generativeai as genai
from pathlib import Path

load_dotenv()

####################
# Session State Init
####################
if "testcase_data" not in st.session_state:
    st.session_state.testcase_data = None
if "current_question_idx" not in st.session_state:
    st.session_state.current_question_idx = 0
if "cached_responses" not in st.session_state:
    st.session_state.cached_responses = {}
if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}
if "cached_prompts" not in st.session_state:
    st.session_state.cached_prompts = {}
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "GPT-4"  # Default model
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

####################
# LLM Client
####################
class LLMClient:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        genai.configure(api_key=self.gemini_api_key)
        self.groq_client = Groq(api_key=self.groq_api_key)
        
        # Map model names to query methods
        self.model_to_function = {
            "GPT-4": self.query_gpt4,
            "Gemini": self.query_gemini,
            "LLaMA (Groq)": self.query_llama_groq
        }

    def query_model(self, model_name, prompt):
        """Unified method to query any model by name"""
        if model_name not in self.model_to_function:
            raise ValueError(f"Unknown model: {model_name}")
        return self.model_to_function[model_name](prompt)

    def query_gpt4(self, prompt):
        """Updated for openai>=1.0.0"""
        client = openai.OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    def query_gemini(self, prompt):
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()

    def query_llama_groq(self, prompt):
        response = self.groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()


####################
# Load Testcases
####################
def get_available_testcase_files():
    """Get list of all JSON files in processed_testcases directory"""
    testcase_dir = Path("processed_testcases")
    if not testcase_dir.exists():
        return []
    return sorted([f.name for f in testcase_dir.glob("*.json")])

def load_testcase_file(filename):
    """Load a specific testcase file from processed_testcases directory"""
    try:
        filepath = Path("processed_testcases") / filename
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Debug logging
            st.write(f"Debug - File Structure: {list(data.keys())}")
            
            # Ensure the data has the expected structure
            if "system_prompt" not in data or "fact_set" not in data or "questions" not in data:
                st.warning(f"Warning: The JSON file '{filename}' doesn't have the expected structure. Expected keys: 'system_prompt', 'fact_set', 'questions'")
                
                # Print the actual content for debugging
                st.json(data)
                
                # Try to adapt to the actual structure if possible
                return data
            return data
    except Exception as e:
        st.error(f"Error loading testcase file: {str(e)}")
        return None

####################
# Sidebar: Select Test Case File
####################
st.sidebar.header("Navigation")

available_files = get_available_testcase_files()
if not available_files:
    st.error("No testcase files found in 'processed_testcases' directory.")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Choose a Test Case File",
    options=available_files,
    index=available_files.index(st.session_state.selected_file) if st.session_state.selected_file in available_files else 0
)

# If user changed file, load the new file and reset question index
if selected_file != st.session_state.selected_file:
    st.session_state.selected_file = selected_file
    st.session_state.testcase_data = load_testcase_file(selected_file)
    st.session_state.current_question_idx = 0
    st.rerun()

# Load testcase data if not already loaded
if st.session_state.testcase_data is None:
    st.session_state.testcase_data = load_testcase_file(selected_file)
    
# Stop if testcase data couldn't be loaded
if st.session_state.testcase_data is None:
    st.error(f"Failed to load testcase file: {selected_file}")
    st.stop()

testcase_data = st.session_state.testcase_data

# Check if the correct structure exists
if "questions" not in testcase_data:
    st.error("The loaded testcase file does not contain a 'questions' key. Please check the JSON structure.")
    st.json(testcase_data)  # Display the actual structure
    st.stop()

questions = testcase_data["questions"]

####################
# Current Question
####################
if st.session_state.current_question_idx >= len(questions):
    st.success("All questions for this test case have been evaluated!")
    st.stop()

current_question = questions[st.session_state.current_question_idx]

####################
# Display Question & Facts
####################
st.header("Question & Context")
col_q, col_f = st.columns(2)

with col_q:
    st.subheader("Question")
    st.markdown(f"**Type:** {current_question.get('question_type', 'general')}")
    st.info(current_question["question"])

with col_f:
    st.subheader("Fact Set")
    st.text_area("Facts", testcase_data["fact_set"], height=150, disabled=True)

####################
# Build Prompt 
####################
prompt = (
    f"{testcase_data['system_prompt']}\n\n"
    f"{testcase_data['fact_set']}\n\n"
    f"Q: {current_question['question']}"
)

####################
# Model Selection & Display
####################
st.header("Model Responses")

model_list = ["GPT-4", "Gemini", "LLaMA (Groq)"]
model_choice = st.selectbox(
    "Select Model to Evaluate", 
    model_list,
    index=model_list.index(st.session_state.selected_model) if st.session_state.selected_model in model_list else 0
)

# Save selected model in session state
st.session_state.selected_model = model_choice

# Now define cached_key after model_choice is set
cached_key = (selected_file, st.session_state.current_question_idx, model_choice)

####################
# Model Testing Section
####################
test_col1, test_col2 = st.columns([2, 8])
with test_col1:
    if st.button("🧪 Test Model"):
        try:
            llm_client = LLMClient()
            # Use the unified query_model method
            response = llm_client.query_model(model_choice, prompt)
            
            # Cache the response
            st.session_state.cached_prompts[cached_key] = response
            st.rerun()
            
        except Exception as e:
            st.error(f"Error testing {model_choice}: {str(e)}")

####################
# Response Display
####################
# Show model response
st.subheader("Model Response")
response_text = st.session_state.cached_prompts.get(cached_key, "Click 'Test Model' to get response")
st.text_area("Response", response_text, height=150, disabled=True)

# Show expected answer
st.subheader("Expected Answer")
st.text_area("Expected", current_question["expected_answer"], height=150, disabled=True)

####################
# Evaluation
####################
st.header("Evaluation")
feedback = st.text_input("Enter feedback if marking as incorrect:")

col_correct, col_wrong = st.columns(2)
with col_correct:
    if st.button("✅ Mark Correct"):
        st.session_state.evaluations[model_choice] = {
            "verdict": "Correct",
            "feedback": "",
            "timestamp": datetime.now().isoformat()
        }
        st.success(f"Marked {model_choice} as Correct")

with col_wrong:
    if st.button("❌ Mark Incorrect"):
        st.session_state.evaluations[model_choice] = {
            "verdict": "Wrong",
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        st.error(f"Marked {model_choice} as Incorrect")

####################
# Navigation Controls
####################
nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    if st.button("⏮ Previous Question") and st.session_state.current_question_idx > 0:
        st.session_state.current_question_idx -= 1
        st.rerun()

with nav_col2:
    if st.button("▶️ Next Question"):
        # Save evaluations to CSV
        try:
            if st.session_state.evaluations:
                for model, eval_data in st.session_state.evaluations.items():
                    # Only log if model was actually tested
                    model_cache_key = (selected_file, st.session_state.current_question_idx, model)
                    if model_cache_key in st.session_state.cached_prompts:
                        model_name_clean = model.replace(" ", "_").replace("(", "").replace(")", "")
                        filename = f"eval_log_{model_name_clean}.csv"
                        
                        # Safely write to CSV
                        try:
                            with open(filename, "a", newline="", encoding="utf-8") as f:
                                fieldnames = [
                                    'TestCaseID', 'QuestionID', 'QuestionType', 'Question',
                                    'LLM Response', 'Expected Answer', 'Verdict', 'Feedback',
                                    'Timestamp', 'ModelType'
                                ]
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                
                                if f.tell() == 0:
                                    writer.writeheader()
                                
                                writer.writerow({
                                    "TestCaseID": selected_file,
                                    "QuestionID": current_question["id"],
                                    "QuestionType": current_question.get("question_type", "general"),
                                    "Question": current_question["question"],
                                    "LLM Response": st.session_state.cached_prompts[model_cache_key],
                                    "Expected Answer": current_question["expected_answer"],
                                    "Verdict": eval_data["verdict"],
                                    "Feedback": eval_data["feedback"],
                                    "Timestamp": eval_data["timestamp"],
                                    "ModelType": model
                                })
                        except Exception as e:
                            st.error(f"Error writing to CSV: {str(e)}")
        except Exception as e:
            st.error(f"Error during evaluation logging: {str(e)}")

        # Clear evaluations and move to next question
        st.session_state.evaluations.clear()
        
        if st.session_state.current_question_idx < len(questions) - 1:
            st.session_state.current_question_idx += 1
            st.rerun()
        else:
            st.success("All questions in this test case have been evaluated!")
