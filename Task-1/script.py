# Importing necessary libraries
import praw
import json
from datetime import datetime, timezone
import re
import string
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

def read_app_details_for_authentication(file_name):
    """Reads Reddit authentication details from a file.
    
    This function opens the specified file, reads its contents line by line, 
    and returns a list where each element is a line from the file.
    
    Args:
        file_name (str): The name of the file containing authentication details.
    
    Returns:
        list: A list of strings, each representing a line from the file.
    """
    with open(file_name, 'r') as f:
        praw_details = f.read().splitlines()
    return praw_details

def fetch_relevant_posts(reddit, subreddits, keywords, limit=1000):
    """Fetches relevant posts from specified subreddits based on keywords.
    
    This function retrieves hot posts from the given list of subreddits, checks if 
    the post's title or body contains any of the specified keywords, and stores 
    relevant posts in a structured format.

    Args:
        reddit (praw.Reddit): An authenticated Reddit instance.
        subreddits (list): A list of subreddit names to fetch posts from.
        keywords (list): A list of keywords to filter relevant posts.
        limit (int, optional): The number of posts to fetch from each subreddit. Defaults to 10.

    Returns:
        list: A list of dictionaries containing details of relevant posts, including:
              - subreddit (str): The name of the subreddit.
              - post_id (str): The unique ID of the post.
              - timestamp (str): The post creation time in UTC (YYYY-MM-DD HH:MM:SS).
              - content (str): The combined title and body text of the post.
              - likes (int): The number of upvotes (score) the post received.
              - comments (int): The number of comments on the post.
              - shares (int): The number of times the post was crossposted.
    """
    filtered_posts = []
    
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)

        try:
            for post in subreddit.hot(limit=limit):  # Fetch hot posts
                full_content = f"{post.title} {post.selftext or ''}".casefold()  # Handle missing selftext
                if any(keyword.casefold() in full_content for keyword in keywords):
                    filtered_posts.append({
                        "subreddit": f"r/{sub}",
                        "post_id": post.id,
                        "timestamp": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                        "content": full_content,
                        "likes": post.score,
                        "comments": post.num_comments,
                        "shares": post.num_crossposts
                    })
        except Exception as e:
            print(f"Error fetching posts from r/{sub}: {e}")  # Handle API errors

    return filtered_posts

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

def clean_text(text,stopwords):
    """
    Cleans the given text by removing emojis, punctuation, special characters, 
    and stopwords for NLP preprocessing.

    Args:
        text (str): The input text to be cleaned.
        STOPWORDS (set): A set of stopwords to be removed from the text.

    Returns:
        str: The cleaned text with stopwords, emojis, and special characters removed.
    """
    # Remove emojis
    text = re.sub(r'[^\w\s,]', '', text)  

    # Remove punctuation and special characters
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Tokenize text and remove stopwords
    words = text.split()
    cleaned_words = [word for word in words if word.lower() not in stopwords]

    # Return cleaned text
    return " ".join(cleaned_words)
def main():
    # Read authentication details
    praw_details = read_app_details_for_authentication('praw_details.txt')

    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=praw_details[0],
        client_secret=praw_details[1],
        user_agent=praw_details[2]
    )

    # Define keywords and subreddits
    keywords = [
        "depressed", "depression", "suicidal", "suicide", "self-harm",
        "addiction", "relapse", "overwhelmed", "hopeless", "anxiety",
        "panic attack", "substance abuse", "mental breakdown", "therapy help"
    ]
    subreddits = ["depression", "mentalhealth", "suicidewatch", "addiction"]

    # Fetch relevant posts
    filtered_posts = fetch_relevant_posts(reddit, subreddits, keywords)

    # Save uncleaned posts to JSON
    uncleaned_file_name = 'uncleaned_dataset.json'
    save_posts_to_json(filtered_posts,uncleaned_file_name)

    print(f"Original Posts details read and saved! ({uncleaned_file_name})")

    STOPWORDS = set(stopwords.words('english'))
    for post in filtered_posts:
        post['content'] = clean_text(text=post['content'],stopwords=STOPWORDS)
    
    # Save cleaned posts to JSON
    cleaned_file_name = 'cleaned_dataset.json'
    save_posts_to_json(posts=filtered_posts,filename=cleaned_file_name)

    print(f"Cleaned Posts details read and saved! ({cleaned_file_name})")
    
if __name__ == "__main__":
    main()
