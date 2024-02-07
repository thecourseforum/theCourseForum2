import boto3
from botocore.exceptions import NoCredentialsError
import pandas as pd
import numpy as np
import difflib
from io import BytesIO
from django.shortcuts import get_object_or_404, redirect, render



N = 5
access_key = 'DO00YNY32DLHVFM9BY7V'
secret_key = 'AOtDYKQLo8btebbC45EeZ/oMUr+oqgeVt7lc08Xbe/c'

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
        print("Credentials not available or not valid.")

def recommend_classes(similarity_matrix, spring_data, course_name):
    # creating a list with all the movie names given in the dataset
    list_of_all_titles = spring_data['Title'].tolist()

    # finding the close match for the movie name given by the user
    find_close_match = difflib.get_close_matches(course_name, list_of_all_titles)

    close_match = find_close_match[0]

    # finding the index of the movie with title
    index_of_the_class = spring_data[spring_data.Title == close_match].index[0]

    # getting a list of similar movies
    similarity_score = list(enumerate(similarity_matrix[index_of_the_class]))

    # sorting the movies based on their similarity score
    sorted_similar_courses = sorted(similarity_score, key=lambda x: x[1], reverse=True)


    i = 1
    displayedSuggestions = []
    inputCourseMnemonic = spring_data[spring_data.index == index_of_the_class]['Mnemonic'].values[0]
    for movie in sorted_similar_courses:
        index = movie[0]
        title_from_index = spring_data[spring_data.index == index]['Title'].values[0]
        mnemonic_from_index = spring_data[spring_data.index == index]['Mnemonic'].values[0]
        if (i < N+1):
            if (title_from_index not in displayedSuggestions and title_from_index != close_match
                    and mnemonic_from_index == inputCourseMnemonic):
                displayedSuggestions.append(title_from_index)
                i += 1
    # Example: Return top N recommendations
    return displayedSuggestions

def getRecommendationsHelper(course_name):
    # Replace with your DigitalOcean Space name, access key, and secret key
    space_name = 'recommender'

    # Replace with the key (path) of the similarity matrix object in your DigitalOcean Space
    object_key = 'similarity_matrix.npy'

    # Load similarity matrix from Spaces
    similarity_matrix = load_similarity_matrix_from_spaces(space_name, object_key)

    # Load data
    spring_data = pd.read_csv('../management/commands/semester_data/csv/2024_spring.csv')

    # For testing python file individually
    # course_name = input('Enter your course name: ')

    # Get recommendations
    recommendations = recommend_classes(similarity_matrix, spring_data, course_name)

    # Print for debugging
    # for i, recommendation in enumerate(recommendations):
    #     print(f"{i + 1}. {recommendation}")
    return recommendations

def get_recommendations(request, mnemonic, course_number):
    course = get_object_or_404(
        Course, subdepartment__mnemonic=mnemonic.upper(), number=course_number)
    request.session['course_code'] = course.code()
    recommendations = getRecommendationsHelper(course)
    return render(request, 'course/course.html',
                  {
                      'recommendations': recommendations
                  })

# For Testing:
# if __name__ == "__main__":
#     print(getRecommendationHelpers("Data Structures and Algorithms 1"))