#!/bin/bash

# Define the folder to search in
input_folder="../../data/monthly-updates/1_downloads_newsapi"  
output_processing_1_folder="../../data/monthly-updates/2_processing-counts-per-article"  
output_processing_2_folder="../../data/monthly-updates/3_processing-counts-per-day"  
final_output_folder="../../data/monthly-updates/4_final-output"  


#################################################
# 1. Check for unprocessed files
#################################################

# List to store files that need to be processed
files_to_process_step1=()
files_to_process_step2=()

# Get all file names in the input folder
for file in "$input_folder"/*; do
  # Extract the file name (without the folder path)
  filename=$(basename "$file")

  # Check if file already processed in step 1
  filename_processed_step1="${filename/.csv/_counts_per_article.csv}"
  # Check if the processed version exists in the processed folder
  if [ ! -f "$output_processing_1_folder/$filename_processed_step1" ]; then
   # If not, add the file to the list for processing
    files_to_process_step1+=("$filename")
  fi
  

  # Check if file already processed in step 2
  filename_processed_step2="${filename/.csv/_counts_per_day.csv}"
  # Check if the processed version exists in the processed folder
  if [ ! -f "$output_processing_2_folder/$filename_processed_step2" ]; then
   # If not, add the file to the list for processing
    files_to_process_step2+=("$filename")
  fi

done


#################################################
# 2. Count keywords per article 
#################################################

# Processing step 1 each file in the list
for filename in "${files_to_process_step1[@]}"; do
  echo "Count keywords per article for $filename..."

  # Initialize the language variable
  language=""

  # Check if the file name contains "eng" or "ara"
  if [[ "$filename" == *"eng"* ]]; then
    language="English"
  elif [[ "$filename" == *"ara"* ]]; then
    language="Arabic"
  else
    echo "File '$filename' must contain either 'eng' or 'ara'. Skipping..."
    continue  # Skip this file and move to the next
  fi

  # Output the determined language for the file
  echo "File '$filename' is in language: $language"
  
  # Combine the file name with the folder path
  input_file_path="$input_folder/$filename"

  # Replace .csv with _counts_per_article.csv and create new file path
  counts_per_article_file_name="${filename/.csv/_counts_per_article.csv}"
  counts_per_article_file_name_file_path="${output_processing_1_folder}/${counts_per_article_file_name}"

  python3 count_keywords_per_article.py --input_file_path $input_file_path --output_file_path $counts_per_article_file_name_file_path  --language $language

done


#####################################################
# 3. Accumulate keyword counts per day and location
#####################################################

# Process each file in the list
for filename in "${files_to_process_step2[@]}"; do
   echo "Accumulate keyword counts per day and location for $filename..."

  # Initialize the language variable
  language=""

  # Check if the file name contains "eng" or "ara"
  if [[ "$filename" == *"eng"* ]]; then
    language="English"
  elif [[ "$filename" == *"ara"* ]]; then
    language="Arabic"
  else
    echo "File '$filename' must contain either 'eng' or 'ara'. Skipping..."
    continue  # Skip this file and move to the next
  fi

  # Output the determined language for the file
  echo "File '$filename' is in language: $language"
  
  # Replace .csv with _counts_per_article.csv and create new file path
  counts_per_article_file_name="${filename/.csv/_counts_per_article.csv}"
  counts_per_article_file_name_file_path="${output_processing_1_folder}/${counts_per_article_file_name}"

  # Replace .csv with _counts_per_article.csv and create new file path
  counts_per_day_file_name="${filename/.csv/_counts_per_day.csv}"
  counts_per_day_file_name_file_path="${output_processing_2_folder}/${counts_per_day_file_name}"

  python3 count_keywords_per_day_location.py --input_file_path $counts_per_article_file_name_file_path --output_file_path $counts_per_day_file_name_file_path  --language $language

done


#####################################################
# 3. Concatenate all processed files
#####################################################

# Check if the array files_to_process has any elements
if [ ${#files_to_process_step2[@]} -gt 0 ]; then
  echo "There were ${#files_to_process_step2[@]} files for which the daily counts were created in this update."

  python3 concatenate_files.py --input_file_path $output_processing_2_folder --output_file_path $final_output_folder

else
  echo "No files to process."
fi

echo "Monthly update processing complete."