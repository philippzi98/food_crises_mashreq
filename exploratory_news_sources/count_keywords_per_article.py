# Loading libraries
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import argparse

# Loading the input arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input_file_path", help="Path to the input file containing downloaded articles", required=True)
parser.add_argument("--output_file_folder", help="Folder in which the output files will be saved", required=True)
parser.add_argument("--language", help="Either Arabic or English", required=True)

args = parser.parse_args()

if args.input_file_path:
    input_file_path = args.input_file_path
if args.output_file_folder:
    output_file_folder = args.output_file_folder
if args.language:
    language = args.language
    assert language in ["Arabic", "English"], "Language must be either Arabic or English"
    
    
# Input paths
keywords_and_location_names_path = "../../data/final/keywords_and_location_names/"


#################
# 1. Loading Input 
#################

# 1. Loading dictionaries containing relevant keywords and location names
if language == "English":
    keywords_dict = pd.read_pickle(keywords_and_location_names_path + 'id_english_keyword.pkl')
    location_names_dict = pd.read_pickle(keywords_and_location_names_path + 'id_english_location_name.pkl')

if language == "Arabic":
    keywords_dict = pd.read_pickle(keywords_and_location_names_path + 'id_arabic_keyword.pkl')
    location_names_dict = pd.read_pickle(keywords_and_location_names_path + 'id_arabic_location_name.pkl')

print("Keyword and location dictionaries loaded.")


# 2. Loading the articles downloaded from NewsAPI
news_articles = pd.read_csv(input_file_path)

if "userHasPermissions" in news_articles.columns:
    news_articles = news_articles.drop(columns=['userHasPermissions'])

print(f"Input file loaded from {input_file_path}.")


#################
# 2. Processing
#################

def article_length_lower_case(df:pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the length of each article in terms of characters and words, and converts the body of each article to lowercase.
    Args:
        df (pandas.DataFrame): The input DataFrame containing the articles.
    Returns:
        pandas.DataFrame: The modified DataFrame with additional columns for article length and lowercase body.
    """
    df["body_len"] = df["body"].apply(lambda x: len(x))
    df["body_len_str"] = df["body"].apply(lambda x: len(x.split(" ")))

    # Converting the body to lowercase (does not change anything for Arabic)
    df["body"] = df["body"].apply(lambda x: x.lower())
    
    return df


def get_all_names_variants_in_value_lists(dictionary:dict) -> list:
    """
    Retrieves the names from a dictionary where the values corresponds to lists of names (e.g. id1:[name_1, name_2]).

    Args:
        dictionary (dict): A dictionary containing ids as keys and lists of strings as values.

    Returns:
        list: A list of all strings that appear in values of the dicitonary.
    """
    ids = [key for key in dictionary.keys()]
    names = np.concatenate([dictionary[id] for id in ids])
    return list(names)


def count_keyword_and_location(df:pd.DataFrame, keyword_dict:dict, location_dict:dict) -> pd.DataFrame:
    """
    Keywords and locations can have multiple values (e.g. different spellings). 
    This function creates a dataframe that per dictionary key sums over the dataframe columns corresponding to the different strings in the value list
    that represent the same key.
    Args:
        df (pd.DataFrame): The input dataframe containing the counts for all possible spellings.
        keyword_dict (dict): A dictionary mapping keyword IDs to the corresponding list of keyword spellings (important for Arabic).
        location_dict (dict): A dictionary mapping location IDs to the corresponding list of location name spellings.
    Returns:
        pd.DataFrame: A dataframe with columns representing the keyword IDs and location IDs, and the values
                        representing the sum of the count of occurrences of different spellings.
    """
    # Create columns for the different keyword IDs by summing over all the columns 
    # containing words representing the same keyword
    keyword_id_column_list = []
    for keyword_id in keyword_dict.keys():
        keyword_id_column_list.append(df[keyword_dict[keyword_id]].sum(axis=1))
        
    # Sum over the counts of all possible variants of how the location names are written
    location_id_column_list = []
    for key in location_dict.keys():
        location_id_column_list.append(df[location_dict[key]].sum(axis=1))
        
    column_list = keyword_id_column_list + location_id_column_list
    location_keyword_df = pd.concat(column_list, axis=1)
    location_keyword_df.columns = np.concatenate([list(keyword_dict.keys()), list(location_dict.keys())])
    
    return location_keyword_df


# Getting the names of the different spellings of keywords and locations to create the vocabulary
keyword_names = get_all_names_variants_in_value_lists(keywords_dict)
location_names = get_all_names_variants_in_value_lists(location_names_dict)
vocabulary = np.unique(np.concatenate([keyword_names, location_names]))

# The CountVectorizer requires as input the numbers of ngrams to consider, so we need to find the maximum number of ngrams required
ngrams_upper_bound_eng = np.max([len(word.split(" ")) for word in vocabulary])
print(f"The upper bound for the n-grams is {ngrams_upper_bound_eng}")

# Lowercasing the articles and adding columns for the length of the articles
news_articles = article_length_lower_case(news_articles)

# Count vectorization
count_output = CountVectorizer(vocabulary=vocabulary, ngram_range=(1, ngrams_upper_bound_eng)).fit_transform(news_articles["body"].values).toarray()
count_df = pd.DataFrame(count_output, columns=vocabulary)

# Summing the counts of the different spellings of the keywords and locations
keyword_location_df = count_keyword_and_location(count_df, keywords_dict, location_names_dict)

# Merge the article data with the keyword counts
news_articles = news_articles.merge(keyword_location_df, left_index=True, right_index=True)

# Add a column that sums over the mentions of all keywords
news_articles["kw_all"] = news_articles[list(keywords_dict.keys())].sum(axis=1)

print(f"Articles processed and keyword counts added.")



#################
# 3. Saving Output
#################

output_file_name = input_file_path.split("/")[-1].split(".")[0] + "_counts.csv"

news_articles.to_csv(output_file_folder + output_file_name, index=False)

print(f"Output saved to {output_file_folder + output_file_name}")