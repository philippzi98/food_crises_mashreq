# Loading libraries
import pandas as pd
import argparse
import os
from datetime import date

# Loading the input arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input_file_path", help="Path to the input file containing daily keyword counts", required=True)
parser.add_argument("--output_file_path", help="Path where the output file will be saved", required=True)

args = parser.parse_args()

input_file_path = args.input_file_path
output_file_path = args.output_file_path

#%%
input_file_path = "/home/dominik/Documents/wb2024/implementations/data/monthly-updates/3_processing-counts-per-day"
output_file_path = "/home/dominik/Documents/wb2024/implementations/data/monthly-updates/4_final-output"

# Concatenate all files with daily counts that were saved so far
list_of_files = []

for file in os.listdir(input_file_path):
    if file.endswith(".csv"):
        list_of_files.append(pd.read_csv(input_file_path + "/" + file))
        
output_file = pd.concat(list_of_files)

# Create a new output file with the concatenated data
today = date.today()
updated_output_file_path = output_file_path + "/" + str(today) + "_output_file.csv"

# Save output data
output_file.to_csv(updated_output_file_path, index=False)

# %%

