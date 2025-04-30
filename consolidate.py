import os
import pandas as pd

# Directory where your CSV files are stored
csv_directory = './runs'

# List of specific files to combine
csv_files = [
    f'results_run_{str(i).zfill(4)}.csv' for i in range(7, 27)
]

# Read and combine all CSV files
all_dfs = []
for file in csv_files:
    file_path = os.path.join(csv_directory, file)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        all_dfs.append(df)
    else:
        print(f"Warning: {file_path} not found.")

# Concatenate all dataframes into a single one
consolidated_df = pd.concat(all_dfs, ignore_index=True)

# Save the combined dataframe to a new CSV
output_path = './runs/consolidated_results.csv'
consolidated_df.to_csv(output_path, index=False)

print(f"Consolidated CSV saved to {output_path}")
