"""
File: utilities.py

Author: Dominik Wielath (dominik.wielath@gmail.com)
DIME Artificial Intelligence (DIME AI) - World Bank Group
Date: 2024-07-04

Description:
This file contains utility functions used to explore the capabilities of different APIs for news data retrieval.
In particular, section 1 contains functions to fetch news data using the GNews API, while section 2 contains functions
to clean and save Factiva most mentioned sources data.
"""

from gnews import GNews
import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import os
import re


# -------------------------
# 1. GNews API Functions
# -------------------------
def get_news_data(query_word: str, start_date: dt.date, end_date_last: dt.date, country: str = None, language: str = 'english', delta: str = None) -> pd.DataFrame:
    '''    
    Fetches news article metadata for a given query_word within a specified date range.

    This function retrieves news data using the GNews API for the specified query_word
    within the given start and end dates. It constructs a pandas DataFrame from the
    collected metadata and extracts relevant publisher information.

    Parameters:
    -----------
    query_word : str
        The name of the query_word to search for news articles.
    start_date : dt.date
        The start date for the news search range.
    end_date_last : dt.date
        The final end date for the news search range.
    country : str, optional
        The country from which to fetch news articles. If not provided, fetches news articles from all countries.
    language : str, optional
        The language of the news articles to fetch. Defaults to 'english'.
    delta : str, optional
        The time increment for the search range. Must be one of None, 'd', 'm', or 'y'. 
        If not provided, defaults to one day.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the metadata of the news articles.

    Notes:
    ------
    - The function asserts that the number of articles retrieved in any single call does not exceed 100. 
      If this happens, the timedelta should be reduced.
    - The GNews API is used to fetch the news data.
    - The `pub_title` and `pub_href` columns are extracted from the nested 'publisher' field in the metadata.
    '''
    
    # Set start_date_first to the original start_date
    start_date_first = start_date
    
    # Check if a correct value for delta is provided
    allowed_deltas = {None, "d", "m", "y"}
    if delta not in allowed_deltas:
        raise ValueError(f"delta must be one of {allowed_deltas}")

    # Select correct increment and initialize the first end_date accordingly
    if delta is None:
        end_date = end_date_last
        increment = dt.timedelta(days=1)
    elif delta == "d":
        increment = dt.timedelta(days=1)
        end_date = start_date + increment
    elif delta == "m":
        increment = relativedelta(months=1)
        end_date = start_date + increment        
    elif delta == "y":
        increment = relativedelta(years=1)
        end_date = start_date + increment
       
    # Initialize the GNews object
    google_news = GNews()
    if country is not None:
        google_news.country = country  # News from a specific country 
    
    if language is not None:
        google_news.language = language  # News in a specific language
    
    article_metadata_list = []
    last_period = False
    
    while end_date <= end_date_last:

        # Set the date and period of the GNews object
        google_news.end_date = (end_date.year, end_date.month, end_date.day)
        google_news.start_date = (start_date.year, start_date.month, start_date.day)

        # Get the news article_metadata for the query_word
        article_metadata = google_news.get_news(query_word)
        
        # Check if the number of articles retrieved equals 100.
        # This would indicate that there were more than 100 articles retrieved in a single call,
        # but the function can only handle 100 articles per call.
        # Hence, the timedelta should be reduced if possible.
        # assert len(article_metadata) != 100, f"Reduce the timedelta, from {start_date} to {end_date} over 100 observations"
        
        if len(article_metadata) == 100:
            print(f"Reduce the timedelta, from {start_date} to {end_date} over 100 observations")

        article_metadata_list.append(article_metadata)
        
        print(f"{start_date} to {end_date}: {len(article_metadata)} articles retrieved.")

        # Increment start and end date by one period, keep the end date of the current period as end_date_last
        start_date += increment
        end_date_prev = end_date
        end_date += increment
        
        # Check if the last period is reached, if so, set end_date to end_date_last
        if (last_period == False) & (end_date > end_date_last) & (end_date_prev != end_date_last):
            last_period = True
            end_date = end_date_last
    
    # Create a dataframe from the list of article_metadata
    article_metadata = list(np.concatenate(article_metadata_list))
    article_metadata = pd.DataFrame(article_metadata)
    
    # Extract the publisher title and href to the dataframe
    article_metadata["pub_title"] = article_metadata["publisher"].apply(lambda x: x["title"])
    article_metadata["pub_href"] = article_metadata["publisher"].apply(lambda x: x["href"])
    article_metadata.drop(columns=["publisher"], inplace=True)
    article_metadata.rename(columns={"published date": "date"}, inplace=True)
    
    # Convert date column from String to date
    article_metadata['date'] = pd.to_datetime(article_metadata['date'], format='%a, %d %b %Y %H:%M:%S %Z', errors='coerce')
    
    # Drop duplicates
    article_metadata.drop_duplicates(inplace=True)
    print(f"\nRemoving duplicates...")
    print(f"Total articles retrieved: {article_metadata.shape[0]} for query word '{query_word}' from {start_date_first} to {end_date_last}")

    return article_metadata


def save_metadata_table(article_metadata: pd.DataFrame, query_word: str, start_date: dt.date, end_date_last: dt.date, country:str = "", data_path: str = ""):
    """
    Saves the article metadata table to a CSV file.

    Parameters:
    - article_metadata (pd.DataFrame): The DataFrame containing the article metadata.
    - query_word (str): The query word used to retrieve the articles.
    - start_date (dt.date): The start date of the query.
    - end_date_last (dt.date): The end date of the query.
    - data_path (str): The path where the CSV file will be saved.

    Returns:
    None
    """
    query_word_joined = "_".join(query_word.split(" "))
    query_specification = f"{query_word_joined}_{country}_{start_date.month}_{start_date.day}_{start_date.year}__{end_date_last.month}_{end_date_last.day}_{end_date_last.year}"
    article_metadata.to_csv(data_path + "meta_" + query_specification + ".csv", index=False)
    print(f"Metadata successfully saved to {data_path + 'meta_' + query_specification + '.csv'}")

# -------------------------
# 2. Factiva API Functions
# -------------------------
def clean_factiva_most_mentioned_sources_expoert(data_path_raw, data_path_clean):
    """
    Cleans and saves Factiva most mentioned sources data.

    Parameters:
    - data_path_raw (str): The path to the directory containing the raw data files.
    - data_path_clean (str): The path to the directory where the cleaned data files will be saved.

    Returns:
    None

    The cleaning operations include:
    - Loading the dataframe from the raw data file
    - Extracting metadata from the header and excluding the header
    - Resetting the index and renaming the columns based on the extracted metadata
    - Extracting additional metadata from the footer
    - Checking if the number of results in the header matches the number of results in the footer
    - Setting the file name based on the extracted metadata
    - Excluding footer metadata from the table
    - Saving the cleaned dataframe as a CSV file

    Note: This function assumes that the raw data files are in CSV format and have a specific structure 
    with metadata in the header and footer.
    """
    
    raw_files = [f for f in os.listdir(data_path_raw) if not f.startswith('.')]
    
    for file in raw_files:
        
        # Load the dataframe
        print(f"Cleaning file: {file}")
        df = pd.read_csv(data_path_raw + file, sep=',', skiprows=1)

        # Extract the metadata from the header, exclude the header and reset the index
        no_results_header = int(re.findall(r'\d+', df.columns[0])[0])
        df.reset_index(inplace=True)
        df.columns = df.iloc[0].values
        df = df[1:].reset_index(drop=True)

        # Exclude the metadata from the footer
        language = df.loc[df["Source"] == "Language", "Document Count"].values[0].lower()[:3]
         
        region = df.loc[df["Source"] == "Region", "Document Count"].values[0]
        region = region.replace(" ", "_")
        
        date = df.loc[df["Source"] == "Date", "Document Count"].values[0]
        from_date = date.split(" to ")[0].replace("/", "")
        to_date = date.split(" to ")[1].replace("/", "")

        text = df.loc[df["Source"] == "Text", "Document Count"].values[0]

        no_results = df.loc[df["Source"] == "Results Found", "Document Count"].values[0]
        no_results = int(no_results.replace(",", ""))

        # Check if the number of results in the header is the same as in the footer
        assert no_results == no_results_header, f"The number of results is the not the same as in the header for {file} ({region}). \n Make sure you select all results on Factiva before downloading!"

        # Set the file name based on the extracted metadata
        if np.isnan(text): 
            file_name = f"{region}_{from_date}_{to_date}_{language}_{no_results}.csv"
        else:
            file_name = f"{region}_{text}_{from_date}_{to_date}_{language}_{no_results}.csv"

        # Exclude footer metadata from table    
        df = df.iloc[:-13]

        # Sace the dataframe as a csv file
        df.to_csv(data_path_clean + file_name, index=False)
        print(f"File saved: {file_name}\n")
    
    print(f"\n All files cleaned and saved under {data_path_clean}!")