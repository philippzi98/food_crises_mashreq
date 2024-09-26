# Loading libraries
import pandas as pd
from tqdm import tqdm
import numpy as np
import argparse

# Loading the input arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input_file_path", help="Path to the input file containing downloaded articles", required=True)
parser.add_argument("--output_file_path", help="Path where the output file will be saved", required=True)
parser.add_argument("--language", help="Either Arabic or English", required=True)

args = parser.parse_args()

input_file_path = args.input_file_path
output_file_path = args.output_file_path
language = args.language
assert language in ["Arabic", "English"], "Language must be either Arabic or English"
    
    
# Input paths
keywords_and_location_names_path = "../data/final/keywords_and_location_names/"


#################
# 1. Loading Input 
#################

print(f"\nLoading inputs:")

# 1. Loading dictionaries containing relevant keywords and location names
if language == "English":
    keywords_dict = pd.read_pickle(keywords_and_location_names_path + 'id_english_keyword.pkl')
    location_names_dict = pd.read_pickle(keywords_and_location_names_path + 'id_english_location_name.pkl')

if language == "Arabic":
    keywords_dict = pd.read_pickle(keywords_and_location_names_path + 'id_arabic_keyword.pkl')
    location_names_dict = pd.read_pickle(keywords_and_location_names_path + 'id_arabic_location_name.pkl')

print(f"Keyword dictionary loaded.")
print(f"Location dictionary loaded.")


# 2. Loading the articles downloaded from NewsAPI
news_articles_with_keyword_counts = pd.read_csv(input_file_path)

print(f"News articles with keywords loaded from specified file path.")



#################
# 2. Processing
#################

print(f"\nProcessing articles:")

def create_keyword_to_category_dict(keywords_dict:dict) -> dict:
    """
    Create a dictionary mapping keyword categories to their corresponding keywords.
    Adding a keyword category "kw" containing as keyword ["kw_all"].
    
    Args:
        keywords_dict (dict): A dictionary containing keywords as keys.
        The keys must have the format "category_keyword".
    
    Returns:
        dict: A dictionary mapping keyword categories to lists of keywords.
    """
    keyword_to_category_dict = {}

    keyword_categories = np.unique([key.split("_")[0] for key in keywords_dict.keys()])
    for category in keyword_categories:
        keyword_to_category_dict[category] = [key for key in keywords_dict.keys() if key.startswith(category + "_")]
        
    keyword_to_category_dict["kw"] = ["kw_all"]
    
    return keyword_to_category_dict


def create_summary_df(news_articles_with_keyword_counts: pd.DataFrame, keyword_to_category_dict: dict, location_names_dict: dict) -> pd.DataFrame:
    """
    Create a summary dataframe of daily counts of articles mentioning keywords.
    Important: The output dataframe counts articles mentioning keywords and not keywords themselves.
    
    Args:
        news_articles_with_keyword_counts (pd.DataFrame): A dataframe containing the counts of articles mentioning keywords.
        keyword_to_category_dict (dict): A dictionary mapping keyword group codes to their corresponding column names.
        location_names_dict (dict): A dictionary mapping location IDs to their corresponding names.
    
    Returns:
        pd.DataFrame: A summary dataframe with daily counts of articles mentioning keywords per location and keyword group.
    """
    
    # Get all dates from the language dataframe
    unique_dates = news_articles_with_keyword_counts["date"].sort_values().unique()

    date_dfs = []
    
    # Iterate over all country codes
    for location_id in tqdm(location_names_dict.keys()):
                                
        # Create a dataframe with all unique dates, province names and country names
        date_df = pd.DataFrame(data={"date":unique_dates})
        date_df["location"] = location_id
            
        # Count the number of articles mentioning a certain province for each date, name the columns of this dataframe "date" and "count_articles"
        no_articles = news_articles_with_keyword_counts.loc[(news_articles_with_keyword_counts[location_id] > 0),].groupby("date").size().reset_index()
        no_articles.columns = ["date", "count_articles"]
        
        # Merge the count information with the date dataframe
        date_df = date_df.merge(no_articles, on="date", how="left")
        
        # Iterate over the Keyword Groups
        for keyword_group_code in list(keyword_to_category_dict.keys()):

            # Extract the column names for all columns of the keyword group
            keyword_group_columns = keyword_to_category_dict[keyword_group_code]

            # Count the number of articles mentioning a certain province and a certain keyword group for each date, name the columns of this dataframe "date" and the keyword group code
            date_count_df = news_articles_with_keyword_counts.loc[(news_articles_with_keyword_counts[location_id] > 0) & (news_articles_with_keyword_counts[keyword_group_columns].sum(axis=1) > 0),].groupby("date")[keyword_group_columns].count().iloc[:,0]
            date_count_df = pd.DataFrame(date_count_df).reset_index()
            date_count_df.columns = ["date", keyword_group_code]
            
            # Merge the count information with the date dataframe
            date_df = date_df.merge(date_count_df, on="date", how="left")
            
            for keyword_group_column in keyword_group_columns:
                date_count_df = news_articles_with_keyword_counts.loc[(news_articles_with_keyword_counts[location_id] > 0) & (news_articles_with_keyword_counts[keyword_group_column] > 0),].groupby("date")[keyword_group_column].count()
                date_count_df = pd.DataFrame(date_count_df).reset_index()
                date_count_df.columns = ["date", keyword_group_column]
                
                # Merge the count information with the date dataframe
                date_df = date_df.merge(date_count_df, on="date", how="left")
                   
        date_dfs.append(date_df)
            
    # Concatenate the date dataframes for all the provinces
    daily_count_of_articles_mentioning_keyword_per_location = pd.concat(date_dfs).reset_index(drop=True)
    daily_count_of_articles_mentioning_keyword_per_location["date"] = pd.to_datetime(daily_count_of_articles_mentioning_keyword_per_location["date"])
    daily_count_of_articles_mentioning_keyword_per_location.set_index("date", inplace=True)

    daily_count_of_articles_mentioning_keyword_per_location.drop(columns="kw_all", inplace=True)
    return daily_count_of_articles_mentioning_keyword_per_location


# Create a dictionary mapping keyword categories to their corresponding keywords
keyword_to_category_dict = create_keyword_to_category_dict(keywords_dict)

# Create a summary dataframe with daily counts of articles mentioning keywords per location
daily_count_of_articles_mentioning_keyword_per_location = create_summary_df(news_articles_with_keyword_counts, keyword_to_category_dict, location_names_dict)

# Fill missing values with 0
daily_count_of_articles_mentioning_keyword_per_location = daily_count_of_articles_mentioning_keyword_per_location.fillna(0)

# Create a new admin level column indicating the level of the administrative division (0: Country, 1: Province, 2: District)
daily_count_of_articles_mentioning_keyword_per_location.insert(2, "admin_level", 0, allow_duplicates=False)
daily_count_of_articles_mentioning_keyword_per_location["admin_level"] = daily_count_of_articles_mentioning_keyword_per_location["location"].str.split("_").apply(lambda x: len(x)) -1

# Insert a column for the language
daily_count_of_articles_mentioning_keyword_per_location.insert(3, "language", language, allow_duplicates=False)

print(f"Articles processed and keyword counts added.")



#################
# 3. Saving Output
#################

daily_count_of_articles_mentioning_keyword_per_location.to_csv(output_file_path, index=False)

print(f"\nOutput saved to: \n{output_file_path}")