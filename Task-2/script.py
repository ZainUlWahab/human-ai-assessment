# importing libraries
from textblob import TextBlob
import json
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text using TextBlob.
    
    Args:
        text (str): The input text for sentiment analysis.

    Returns:
        str: The sentiment classification ('Positive', 'Negative', 'Neutral').
    """
    sentiment_score = TextBlob(text).sentiment.polarity

    if sentiment_score > 0:
        return "Positive"
    elif sentiment_score < 0:
        return "Negative"
    else:
        return "Neutral"
    
def categorize_risk_level(text,high_risk_terms):
    """
    Categorizes a post into risk levels based on its content.
    
    Args:
        text (str): The input text of the post.

    Returns:
        str: Risk level ('High-Risk', 'Moderate Concern', 'Low Concern').
    """
    text_lower = text.lower()

    # High-Risk: Contains direct crisis phrases
    # This can be extended to be more phrases
    high_risk_phrases = ["dont want to be here", "cant do this anymore","dont want to live"
                          "no reason to live", "ending it all", "want to die","want to kill"]
    
    if any(phrase in text_lower for phrase in high_risk_phrases):
        return "High-Risk"

    # Moderate Concern: Seeking help or discussing struggles
    if any(term in text_lower for term in high_risk_terms):
        return "Moderate Concern"

    # Otherwise, it's Low Concern
    return "Low Concern"

def read_dataset(file_name):
    """
    Reads a JSON dataset from a file and loads it into a Python dictionary.

    This function opens a JSON file, reads its contents, and parses it 
    into a dictionary or list, depending on the file structure.

    Args:
        file_name (str): The name of the JSON file to read.

    Returns:
        dictionary: The loaded dataset from the JSON file.
    """
    
    with open(file_name, 'r') as f:
        dataset = json.load(f)
    return dataset

def classify_posts(all_posts,high_risk_terms):
    """
    Classifies posts based on sentiment and risk level.

    This function analyzes the sentiment of each post and categorizes 
    its risk level based on predefined high-risk terms.

    Args:
        all_posts (list): A list of post contents (strings).
        high_risk_terms (set): A set of high-risk words/phrases to detect crisis situations.

    Returns:
        list: A list of tuples containing (sentiment, risk_level) for each post.
    """
    analysis = []
    for post in all_posts:
        sentiment = analyze_sentiment(post)
        risk_level = categorize_risk_level(post,high_risk_terms)
        analysis.append((sentiment,risk_level))
    return analysis

def make_table(analysis,file_name):
    """
    Generates a summary table of post classifications and saves it as a CSV file.

    This function takes the list of classified posts, creates a DataFrame, 
    counts the occurrences of each (sentiment, risk_level) combination, 
    and saves the result to a CSV file.

    Args:
        analysis (list): A list of tuples (sentiment, risk_level).
        file_name (str): The name of the CSV file to save the table.

    Returns:
        pd.DataFrame: The dataframe containing analysis.
    """
    # Convert list of tuples to DataFrame
    df = pd.DataFrame(analysis, columns=["sentiment", "risk_level"])

    # Create summary table: Count of posts by Sentiment & Risk Level
    summary_table = df.value_counts().reset_index(name="count")

    summary_table.to_csv(file_name,index=False)
    print(f"Table saved to {file_name}")
    return df

def make_plot(df,file_name):
    """
    Creates and saves a bar plot visualizing post distribution by sentiment and risk level.

    This function generates a count plot using Seaborn, displaying the number of posts
    categorized by sentiment and risk level, and saves the visualization to a file.

    Args:
        df (pd.DataFrame): The DataFrame containing analysis(sentiment and risk levels).
        file_name (str): The file name to save the plot.

    Returns: None
    """
    # Set plot style
    sns.set_style("whitegrid")

    # Plot: Distribution of Posts by Sentiment & Risk Level
    plt.figure(figsize=(10, 6))
    ax = sns.countplot(data=df, x="risk_level", hue="sentiment", palette="pastel")

    # Add labels
    plt.title("Distribution of Posts by Sentiment & Risk Level")
    plt.xlabel("Risk Level")
    plt.ylabel("Number of Posts")
    plt.legend(title="Sentiment")

    # Save the plot
    plt.savefig(file_name)
    print(f"Plot saved to {file_name}")

def update_dataset(dataset,df):
    """
    Updates the dataset by adding 'sentiment' and 'risk_level' from the DataFrame.

    Args:
        dataset (list): List of Reddit posts stored as dictionaries.
        df (pd.DataFrame): DataFrame containing 'sentiment' and 'risk_level'.

    Returns:
        list: Updated dataset with sentiment and risk levels added.
    """
    # Iterate through the dataset and update each post with sentiment & risk level
    for i, post in enumerate(dataset):
        if i < len(df):
            post["sentiment"] = df.iloc[i]["sentiment"]
            post["risk_level"] = df.iloc[i]["risk_level"]
    
    return dataset

def save_posts_to_json(posts, filename="filtered_reddit_posts.json", pretty=True):
    """Saves filtered Reddit posts to a JSON file.

    Args:
        posts (list): A list of dictionaries containing Reddit post data.
        filename (str, optional): The name of the JSON file to save. Defaults to "filtered_reddit_posts.json".
        pretty (bool, optional): Whether to format the JSON for readability (default: True). 
                                 If False, it reduces file size by not adding extra whitespace.
    
    Returns:
        None
    """
    with open(filename, 'w') as json_file:
        json.dump(posts, json_file, indent=4 if pretty else None)
def main():
    # Read the dataset stored in Task 1 folder
    dataset = read_dataset(file_name='../Task-1/cleaned_dataset.json')

    # Extract only the post contents from the dataset
    all_posts = [post["content"] for post in dataset]

    # Make a Tfidf Vectorizer for analysis
    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)

    # Fit it according to our text
    tfidf_matrix = vectorizer.fit_transform(all_posts)

    # Extract the terms
    feature_names = vectorizer.get_feature_names_out()

    # Extract the high risk terms
    high_risk_terms = set(feature_names[:30]) # top 30 high risk terms

    # Classify the posts by sentiment and risk level
    analysis = classify_posts(all_posts=all_posts,high_risk_terms=high_risk_terms)

    # Make a summary table of the analysis
    df = make_table(analysis=analysis,file_name='summary_table.csv')

    # Make a plot of the analysis
    make_plot(df=df,file_name="distribution_of_posts.jpeg")

    # Update dataset with sentiment and risk levels.
    final_dataset = update_dataset(dataset=dataset,df=df)

    # Save updated dataset
    filename="updated_dataset.json"
    save_posts_to_json(posts=final_dataset,filename=filename)
    print(f"Updated posts with sentiment and risk levels saved to {filename}")
    
if __name__ == "__main__":
    main()