import boto3
from botocore.exceptions import NoCredentialsError
import pandas as pd
import numpy as np
import difflib
from io import BytesIO
from django.shortcuts import get_object_or_404, redirect, render
import os
# from dotenv import load_dotenv

# load_dotenv()

N = 4  # number of similar courses to print
CHUNKS = 30  # number of chunks in digital ocean
access_key = os.getenv("DO_ACCESS_KEY")
secret_key = os.getenv("DO_SECRET_KEY")

from ..models import (
    Course,
)


def load_similarity_matrix_from_spaces(space_name, object_key):
    try:
        # Create an S3 client
        s3 = boto3.client('s3',
                          region_name="nyc3",
                          endpoint_url='https://nyc3.digitaloceanspaces.com',
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key,
                          config=boto3.session.Config(signature_version='s3v4', retries={
                              'max_attempts': 2,
                              'mode': 'standard'
                          },
                                                      s3={'addressing_style': "virtual"}, ))

        response = s3.get_object(Bucket=space_name, Key=object_key)
        body_content = response['Body'].read()
        buffer = BytesIO(body_content)

        similarity_matrix = np.load(buffer, allow_pickle=True)

        return similarity_matrix

    except NoCredentialsError:
        return []
        # print("Credentials not available or not valid.")

def load_mapping_from_spaces(space_name, object_key, object_key2):
    try:
        # Create an S3 client
        s3 = boto3.client('s3',
                          region_name="nyc3",
                          endpoint_url='https://nyc3.digitaloceanspaces.com',
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key,
                          config=boto3.session.Config(signature_version='s3v4', retries={
                              'max_attempts': 2,
                              'mode': 'standard'
                          },
                                                      s3={'addressing_style': "virtual"}, ))

        response = s3.get_object(Bucket=space_name, Key=object_key)
        response2 = s3.get_object(Bucket=space_name, Key=object_key2)
        body_content = response['Body'].read()
        body_content2 = response2['Body'].read()
        buffer = BytesIO(body_content)
        buffer2 = BytesIO(body_content2)

        row_to_class_mapping = np.load(buffer, allow_pickle=True).item()  # .item() to load as dictionary
        class_to_index_map = np.load(buffer2, allow_pickle=True).item()  # .item() to load as dictionary
        return [row_to_class_mapping, class_to_index_map]

    except NoCredentialsError:
        return []
        # print("Credentials not available or not valid.")

def recommend_classes(similarity_matrix, adjusted_index_of_the_class, index_to_course_map, og_index_of_class):
    # getting a list of similar movies
    similarity_score = list(enumerate(similarity_matrix[adjusted_index_of_the_class]))

    # sorting the classes based on their similarity score
    sorted_similar_courses = sorted(similarity_score, key=lambda x: x[1], reverse=True)
    # print(sorted_similar_courses)

    i = 1
    displayedSuggestions = []
    course_mnemonics = []
    course_numbers = []
    course_titles = []
    inputCourseMnemonic = index_to_course_map[og_index_of_class][0]
    inputCourseNumber = index_to_course_map[og_index_of_class][1] 
    displayedSuggestions.append(str(inputCourseMnemonic) + str(inputCourseNumber))
    for course in sorted_similar_courses:
        index = course[0]
        mnemonic_from_index = index_to_course_map[index][0]
        number_from_index = index_to_course_map[index][1]
        # print(mnemonic_from_index, number_from_index)

        identifier = str(mnemonic_from_index)+str(number_from_index)
        if(identifier in displayedSuggestions):
            continue
        try:
            similar_course = get_object_or_404(
            Course, subdepartment__mnemonic=mnemonic_from_index.upper().strip(), number=int(number_from_index)
            )   
        except:
            continue

        title_from_index = similar_course.title
        if (i < N + 1):
            if (identifier not in displayedSuggestions
                    and mnemonic_from_index == inputCourseMnemonic and number_from_index >= inputCourseNumber):
                displayedSuggestions.append(identifier)
                course_mnemonics.append(mnemonic_from_index)
                course_numbers.append(number_from_index)
                course_titles.append(title_from_index)
                i += 1
        else:
            break
            # Example: Return top N recommendations
    # print(course_titles, course_mnemonics, course_numbers)
    return [course_titles, course_mnemonics, course_numbers]


def get_recommendations_helper(course_name, course_mnemonic, course_number):
    # Replace with your DigitalOcean Space name, access key, and secret key
    space_name = 'recommender'

    # Load data
    # spring_data = pd.read_csv('tcf_website/management/commands/semester_data/csv/2024_spring.csv')
    # Load data for testing python file individually
    # spring_data = pd.read_csv('../management/commands/semester_data/csv/2024_spring.csv')

    # list_of_all_titles = spring_data['Title'].tolist()
    mapping_key1 = 'row_to_class_mapping.npy'  # Provide the correct object key for the mapping file
    mapping_key2 = 'class_to_index.npy'

    row_to_class_mapping, class_to_index_map = load_mapping_from_spaces(space_name, mapping_key1, mapping_key2)

    # finding the close match for the class name given by the user
    find_close_match = difflib.get_close_matches(course_mnemonic + str(course_number), class_to_index_map.keys())

    if(len(find_close_match) < 1):
        return []
    
    close_match = find_close_match[0]

    # finding the index of the class with title
    index_of_the_class = class_to_index_map[close_match]

    # load chunk from digital ocean that contains similarities for specified class
    chunk_size = int(len(row_to_class_mapping.keys()) / CHUNKS)
    chunk_val = int(index_of_the_class / chunk_size)
    object_key = f'chunk_{chunk_val}.npy'
    adjusted_index_of_class = int(index_of_the_class % chunk_size)

    # Load similarity matrix from Spaces
    similarity_matrix = load_similarity_matrix_from_spaces(space_name, object_key)

    # Get recommendations
    recommendations = recommend_classes(similarity_matrix, adjusted_index_of_class, row_to_class_mapping, index_of_the_class)
    
    return recommendations

# For Testing:
# Instructions: uncomment main below, comment out "from modules import" segment, and comment out "get_recommendations" function, comment correct load_csv function
# if __name__ == "__main__":
#     print(get_recommendations_helper("Data Structures and Algorithms 1", "CS", 2100))
