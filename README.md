# Temporal-Robustness-Benchmarking-LLMs
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Temporal Robustness Benchmarking for LLMs</title>
</head>
<body>
  <h1>Temporal Robustness Benchmarking for LLMs</h1>

  <p>This repository provides a modular framework to evaluate temporal reasoning capabilities of Large Language Models (LLMs). The goal is to assess consistency and robustness of model responses across various time-sensitive question formats using the ComplexTempQA dataset.</p>

  <h2>Project Structure</h2>
  <ul>
    <li><strong>data_sampling/</strong> - Scripts for random sampling from ComplexTempQA.</li>
    <li><strong>clustering/</strong> - TF-IDF and KMeans-based clustering pipeline for grouping semantically similar questions.</li>
    <li><strong>fact_extraction/</strong> - Few-shot prompt-based fact extraction using LLM APIs.</li>
    <li><strong>question_generation/</strong> - Generation of question variations from base facts.</li>
    <li><strong>evaluation/</strong> - Scripts to evaluate accuracy and consistency of model responses.</li>
    <li><strong>api_calls/</strong> - Optional scripts to use external LLM APIs (e.g., Groq) for fact and question generation.</li>
    <li><strong>utils/</strong> - Helper functions and shared utilities.</li>
  </ul>

  <h2>Getting Started</h2>
  <ol>
    <li>Clone this repository.</li>
    <li>Ensure Python 3.8+ and install dependencies from <code>requirements.txt</code>.</li>
    <li>Run sampling script to generate a working dataset subset.</li>
    <li>Use the clustering pipeline to assign cluster labels.</li>
    <li>Extract representative facts per cluster manually or via few-shot prompting.</li>
    <li>Generate question variations and proceed with model testing.</li>
  </ol>

  <h2>Example Workflow</h2>
  <pre>
    1. Sample → data_sampling/sampling_script.py
    2. Cluster → clustering/clustering_from_pickle.py
    3. Extract facts → fact_extraction/few_shot_fact_generator.py
    4. Generate variations → question_generation/question_variation_generator.py
    5. Evaluate models → evaluation/model_response_analysis.ipynb
  </pre>

  <h2>Outputs</h2>
  <ul>
    <li>Clustered datasets (pickle/CSV)</li>
    <li>Distribution plots per cluster</li>
    <li>Fact and question sets per cluster</li>
    <li>Evaluation reports on model consistency</li>
  </ul>

  <h2>License</h2>
  <p>This repository is provided for academic use under a permissive open-source license. Please cite relevant sources if reused.</p>

</body>
</html>
