import subprocess
import os

# Step 1: Define environment and location
conda_env_name = "nlp_finaltest"
project_dir = r"D:\Coursework\cse576-topics_in_nlp\FullyAutomated"

# Step 2: Commands to run
commands = []

# 7 times with max_events 11
commands += [
    f"python main.py --theme all --max_events 11 --shuffle_abs --shuffle_rel"
] * 7

# 7 times with max_events 15
commands += [
    f"python main.py --theme all --max_events 15 --shuffle_abs --shuffle_rel"
] * 7

# 6 times with max_events 21
commands += [
    f"python main.py --theme all --max_events 21 --shuffle_abs --shuffle_rel"
] * 6

# Step 3: Full execution
for idx, cmd in enumerate(commands, start=1):
    print(f"▶️ Running command {idx}/{len(commands)}: {cmd}")
    full_cmd = f"conda run -n {conda_env_name} {cmd}"
    subprocess.run(full_cmd, cwd=project_dir, shell=True)

print("✅ All runs completed.")
