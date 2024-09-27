#!/bin/bash

# Setting variables
input_file_path="../../data/final/downloads_newsapi/Mashreq_2024-06-23_2024-07-24_articles_eng.csv"
output_file_folder="../../data/final/keyword_location_counts/"
language="English"

# Extract the file name from the input path (basename removes the directory path)
input_file_name=$(basename "$input_file_path")


#################################################
# 1. count_keywords_per_article.py 
#################################################

# Replace .csv with _keyword_location_counts.csv
keyword_location_counts_file_name="${input_file_name/.csv/_keyword_location_counts.csv}"
# Combine the output folder with the new file name
keyword_location_counts_file_name_file_path="${output_file_folder}${keyword_location_counts_file_name}"

echo "Running count_keywords_per_article.py"
python3 count_keywords_per_article.py --input_file_path $input_file_path --output_file_path $keyword_location_counts_file_name_file_path  --language $language


#################################################
# 2. daily_count_articles_mentioning_keywords.py
#################################################

# Replace .csv with _articles_mentioning_count.csv
articles_mentioning_count_file_name="${input_file_name/.csv/_articles_mentioning_count.csv}"
# Combine the output folder with the new file name
articles_mentioning_count_file_path="${output_file_folder}${articles_mentioning_count_file_name}"

echo "Running daily_count_articles_mentioning_keywords.py"
python3 daily_count_articles_mentioning_keywords.py --input_file_path $keyword_location_counts_file_name_file_path --output_file_path $articles_mentioning_count_file_path  --language $language