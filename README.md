# Temporal Robustness Benchmarking System

This repository contains a comprehensive system for benchmarking the temporal reasoning capabilities of Large Language Models (LLMs).

## System Architecture

The system consists of several interconnected components that work together to:

1. Generate synthetic timelines using real-world events
2. Create fact statements in both absolute and relative temporal formats
3. Generate test questions and compute gold answers
4. Evaluate LLM performance on temporal reasoning tasks

### Key Components

1. **Main Pipeline** (`main.py`)

   - Orchestrates the entire benchmarking process
   - Coordinates data flow between components

2. **Event Library** (`event_library.py`)

   - Manages a curated collection of real-world events
   - Provides event data with historical dates and themes

3. **Tuple Builder** (`tuple_builder.py`)

   - Creates synthetic timelines from real events
   - Supports both chronological and shuffled event sequences

4. **Fact Synthesiser** (`fact_synthesiser.py`)

   - Generates fact statements in two variants:
     - Absolute: Using ISO-8601 dates
     - Relative: Using temporal references to previous events

5. **Question Generator** (`question_generator.py`)

   - Creates test questions based on fact sets
   - Supports multiple question templates
   - Can use either deterministic or LLM-based generation

6. **Gold Engine** (`gold_engine.py`)

   - Computes correct answers for all question types
   - Implements deterministic answer functions

7. **Evaluation Harness** (`eval_harness.py`)

   - Runs LLM evaluations
   - Records responses and metrics
   - Manages API interactions

8. **Comparator** (`comparator.py`)

   - Compares model answers against gold answers
   - Supports fuzzy matching for string answers
   - Handles numeric comparisons

9. **Dataset Writer** (`dataset_writer.py`)

   - Persists generated datasets
   - Records evaluation results
   - Maintains metadata

10. **Prompt Builder** (`prompt_builder.py`)
    - Constructs evaluation prompts
    - Ensures consistent prompt formatting

## Generating the Architecture Diagram

To generate the system architecture diagram:

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the visualization script:
   ```bash
   python system_architecture.py
   ```

This will generate `system_architecture.png` showing the component relationships and data flow.

## Data Flow

1. Events are loaded from the event library
2. Synthetic timelines are created using the tuple builder
3. Fact statements are generated in both absolute and relative formats
4. Questions are created based on the fact sets
5. Gold answers are computed for all questions
6. LLM evaluations are performed using the evaluation harness
7. Results are compared and persisted

## Usage

The system can be run using the main pipeline:

```bash
python main.py --theme <theme_name> --model <llm_model> --variant <direct|relative>
```

Where:

- `theme_name`: Filter events by theme (e.g., "history", "tech", "sports")
- `llm_model`: Name of the LLM to evaluate
- `variant`: Whether to use direct (absolute) or relative temporal references
