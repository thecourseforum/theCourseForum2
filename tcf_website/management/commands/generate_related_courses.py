from sentence_transformers import SentenceTransformer
import pandas as pd

####### Phase 1: Content Fingerprint #######

#Load current semester course data
df = pd.read_csv('semester_data/csv/2025spring.csv')

features = ["Mnemonic", "Number", "Title", "Topic", "Description"]
df = df[features]

#relevant columns:
'''
## Must haves
Description
Mnemonic
Number
Title
Pre-requisites (can we extract this easily?)

## Optional
Instructor
Topic
Disciplines
'''

# Load a pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
# use only description or title + description for embeddings?
embeddings = model.encode(df["Description"], normalize_embeddings=True)

print(embeddings.shape)

####### Phase 2: Reranking #######
#Based on pre-req connection, department (Mnemonic), and level (Number)

#formula? weighted highest to lowest: pre-req connection, department (Mnemonic), and level (Number)
