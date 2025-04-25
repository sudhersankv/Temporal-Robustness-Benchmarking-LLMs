from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.generic.blank import Blank
from diagrams.aws.database import Database
from diagrams.aws.compute import EC2
from diagrams.aws.storage import S3
from diagrams.aws.general import Users
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SQS

# Define custom styles
graph_attr = {
    "fontsize": "20",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "spline",
    "nodesep": "0.60",
    "ranksep": "0.75",
    "fontname": "Sans-Serif",
    "fontcolor": "#2D3436",
    "fontsize": "12",
}

node_attr = {
    "fontsize": "14",
    "fontname": "Sans-Serif",
    "fontcolor": "#2D3436",
    "shape": "box",
    "style": "rounded,filled",
    "fillcolor": "#E6F3FF",
    "color": "#0066CC",
    "penwidth": "2",
}

edge_attr = {
    "color": "#0066CC",
    "penwidth": "2",
    "arrowhead": "normal",
    "arrowsize": "1",
}

# Create the diagram
with Diagram("Temporal Robustness Benchmarking System Architecture", 
            show=False, 
            direction="LR",
            graph_attr=graph_attr,
            node_attr=node_attr,
            edge_attr=edge_attr):

    # Event Library and Tuple Builder
    with Cluster("Timeline Generation"):
        event_lib = Database("Event Library")
        tuple_builder = EC2("Tuple Builder")
        event_lib >> tuple_builder

    # Fact Synthesis with ABS/REL variants
    with Cluster("Fact Synthesis"):
        fact_synth = S3("Fact Synthesiser")
        abs_facts = Users("ABS Facts")
        rel_facts = Users("REL Facts")
        
        tuple_builder >> fact_synth
        fact_synth >> [abs_facts, rel_facts]

    # Question Generation and Gold Answers
    with Cluster("Question & Gold Answer Generation"):
        question_gen = Cloudwatch("Question Generator")
        gold_engine = SQS("Gold Engine")
        
        [abs_facts, rel_facts] >> question_gen
        question_gen >> gold_engine

    # Evaluation and Results
    with Cluster("Evaluation & Results"):
        comparator = EC2("Comparator")
        dataset_writer = S3("Dataset Writer")
        
        gold_engine >> comparator
        comparator >> dataset_writer

    # Add explanatory notes
    with Cluster("Key Processes"):
        Blank("1. Timeline Generation") - Edge(style="invis") - Blank("2. Fact Synthesis")
        Blank("3. Question Generation") - Edge(style="invis") - Blank("4. Evaluation")