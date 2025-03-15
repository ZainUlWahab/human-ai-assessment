# GSoC Candidate Assessment Submission  

Hello Sir. This repository contains my submission for the GSoC Candidate Assessment Test for the project:  
**"AI-Powered Behavioral Analysis for Suicide Prevention, Substance Use, and Mental Health Crisis Detection with Longitudinal Geospatial Crisis Trend Analysis."**  

## How to Run  

### 1. Set Up Virtual Environment  
Before running any scripts, create a virtual environment:  

- Run `python -m venv venv`  
- Activate the virtual environment:  
  - **Windows**: `venv\Scripts\activate`  
  - **Mac/Linux**: `source venv/bin/activate`  

### 2. Install Dependencies  
- Run `pip install -r requirements.txt`  

**Important:** Make sure to use python version <3.13. Spacy does not work on python version 3.13

## Folder Structure & Task Descriptions  

### Task 1: Dataset Creation & Cleaning  
**Location:** `Task-1/script.py`  

This script fetches and processes Reddit posts, resulting in two JSON files:  

- `uncleaned_dataset.json` – Contains raw data.  
- `cleaned_dataset.json` – Processed dataset with cleaned text for NLP tasks.  

**Fields in Dataset:**  

- `subreddit` (str): Name of the subreddit.  
- `post_id` (str): Unique post ID.  
- `timestamp` (str): UTC time of post creation (`YYYY-MM-DD HH:MM:SS`).  
- `content` (str): Combined title and body text of the post.  
- `likes` (int): Upvote count.  
- `comments` (int): Number of comments.  
- `shares` (int): Crosspost count.  

**Important:** Before running, update `praw_details.txt` with your Reddit API credentials:  

1. First line → `client_id`  
2. Second line → `client_secret`  
3. Third line → `user_agent`  

Run the script with:  
`python Task-1/script.py`  


### Task 2: Sentiment Analysis & Risk Classification  
**Location:** `Task-2/script.py`  

- Uses **TextBlob** for sentiment classification.  
- Uses **TF-IDF vectors** from `scikit-learn` to determine risk levels.  
- Updates `Task-1/cleaned_dataset.json` with sentiment and risk level.  
- Stores the updated dataset in `Task-2/updated_dataset.json`
- Generates `distribution_of_posts.jpeg`, a visualization of sentiment and risk levels.  

Run the script with:  
`python Task-2/script.py`  


### Task 3: Geolocation Extraction & Crisis Mapping  
**Location:** `Task-3/script.py`  

**Important:** Run `script.py` with a user agent as a command-line argument.  
Example: `python Task-3/script.py "example@gmail.com"`  

This script:  
- Extracts locations from text using **spaCy**.  
- Updates `Task-2/updated_dataset.json` with location data, saving it as `updated_dataset_with_locations.json`.  
- Finds and stores the top 5 locations in a CSV file.  
- Generates an interactive crisis **heatmap** using Folium, saved as `crisis_heatmap.html`.  

**Important:** Do not worry if the script is taking long. It tends to take time due to the use of sleep statements so that we do not get timeout by the API. 
Run the script with:  
`python Task-3/script.py "your_user_agent"`  

Thank you!
