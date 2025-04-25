from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.generic.blank import Blank
from diagrams.aws.database import Database
from diagrams.aws.compute import EC2
from diagrams.aws.storage import S3
from diagrams.aws.general import Users
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SQS
from diagrams.aws.analytics import Kinesis
from diagrams.aws.security import SecretsManager
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.aws.general import GenericSDK
from diagrams.aws.management import SystemsManagerParameterStore
from diagrams.aws.analytics import Athena
from diagrams.aws.management import CloudwatchEventTimeBased
from diagrams.aws.analytics import Quicksight
from diagrams.aws.integration import StepFunctions

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
        fact_synthesizer = S3("Fact Synthesiser")
        abs_facts = SimpleStorageServiceS3Bucket("ABS Facts")
        rel_facts = StepFunctions("REL Facts")
        
        tuple_builder >> fact_synthesizer
        fact_synthesizer >> [abs_facts, rel_facts]

    # Question Generation and Gold Answers
    with Cluster("Question & Gold Answer Generation"):
        question_generator = Cloudwatch("Question Generator")
        gold_engine = SQS("Gold Engine")
        templates = SecretsManager("Question Templates")
        
        [abs_facts, rel_facts] >> question_generator
        templates >> question_generator
        question_generator >> gold_engine

    # Evaluation and Results
    with Cluster("Evaluation & Results"):
        comparator = EC2("Comparator")
        dataset_writer = S3("Dataset Writer")
        metrics = Quicksight("Metrics")
        
        gold_engine >> comparator
        comparator >> [dataset_writer, metrics]

    # Add process flow visualization
    with Cluster("Process Flow"):
        process_timeline = CloudwatchEventTimeBased("1. Timeline Generation")
        process_fact = SystemsManagerParameterStore("2. Fact Synthesis")
        process_question = GenericSDK("3. Question Generation")
        process_eval = Athena("4. Evaluation")
        
        # Connect processes in sequence
        process_timeline >> process_fact >> process_question >> process_eval
        
        # Connect to actual components
        process_timeline - Edge(style="dashed", color="#666666") - tuple_builder
        process_fact - Edge(style="dashed", color="#666666") - fact_synthesizer
        process_question - Edge(style="dashed", color="#666666") - question_generator
        process_eval - Edge(style="dashed", color="#666666") - comparator