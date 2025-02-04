import os
import ssl
import time

import nltk  # type: ignore
import numpy as np
import pandas as pd
import torch
from nltk.tokenize import sent_tokenize  # type: ignore
from transformers import (  # type: ignore
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

ssl._create_default_https_context = ssl._create_unverified_context

# Ensure nltk sentence tokenizer is downloaded
nltk.download("punkt")
nltk.download("punkt_tab")

# Load the RoBERTa sentiment model and tokenizer
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Locate the file dynamically using the provided directory structure
current_directory = os.path.dirname(os.path.abspath(__file__))
reviews_data_path = os.path.join(current_directory, "reviews_data", "reviews_data.csv")

# Verify if the file exists before proceeding
if os.path.exists(reviews_data_path):
    print(f"✅ File found: {reviews_data_path}")
else:
    print(f"❌ File not found: {reviews_data_path}")
    exit(1)  # Exit script if file is missing


def split_text(text, max_tokens=512):
    """Splits long text into chunks of max 512 tokens logically using sentence boundaries."""
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        tokenized_sentence = tokenizer.tokenize(sentence)
        sentence_length = len(tokenized_sentence)

        if current_length + sentence_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def get_sentiment_score(text):
    """Runs sentiment analysis on a given text and returns the raw sentiment score."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    scores = outputs.logits.softmax(dim=1).numpy()[
        0
    ]  # Probabilities for [Negative, Neutral, Positive]

    # Compute a weighted sentiment score instead of labels
    sentiment_score = (
        (scores[0] * -1) + (scores[1] * 0) + (scores[2] * 1)
    )  # Negative * -1, Neutral * 0, Positive * 1
    return round(sentiment_score, 4)  # Return raw score rounded to 4 decimals


def compute_average_sentiment(sentiment_scores):
    """Computes the average sentiment score for a review based on all chunk scores."""
    return round(np.mean(sentiment_scores), 4)  # Compute the mean score


# Load the dataset
print(f"📂 Loading dataset from {reviews_data_path}...")
df = pd.read_csv(reviews_data_path)
print(f"✅ Dataset loaded successfully! Total rows: {len(df)}")

# Process each text entry with logging
sentiment_scores_list = []
start_time = time.time()  # Track start time
progress_interval = 100  # Log progress every N rows

for index, text in enumerate(df["text"].astype(str)):
    text_chunks = split_text(text)  # Split long text into chunks
    chunk_scores = [
        get_sentiment_score(chunk) for chunk in text_chunks
    ]  # Get sentiment score for each chunk
    average_sentiment_score = compute_average_sentiment(chunk_scores)  # Compute average score

    sentiment_scores_list.append(average_sentiment_score)

    # Logging progress every 100 rows
    if (index + 1) % progress_interval == 0:
        elapsed_time = time.time() - start_time
        avg_time_per_row = elapsed_time / (index + 1)
        estimated_remaining = avg_time_per_row * (len(df) - index - 1)
        print(
            f"🟢 Processed {index + 1}/{len(df)} rows. Estimated time left: {estimated_remaining:.2f} sec"
        )

# Add the new sentiment score column to the dataframe
df["sentiment_score"] = sentiment_scores_list  # Numerical sentiment score

# Save the updated CSV file in the same directory
updated_file_path = os.path.join(
    current_directory, "reviews_data", "reviews_data_with_sentiment.csv"
)
print(f"💾 Saving updated dataset to {updated_file_path}...")
df.to_csv(updated_file_path, index=False)
print(
    f"✅ Dataset saved successfully! Processed {len(df)} rows in {time.time() - start_time:.2f} seconds."
)
