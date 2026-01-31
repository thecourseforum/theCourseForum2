import json
import os
import sys
from pathlib import Path

import django

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
sys.path.insert(0, project_root)

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcf_core.settings.ci")
django.setup()

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Import the Django models
from tcf_website.models import Course, Section, Semester


def generate_related_courses_for_semester(semester):
    """
    Generate related courses for all courses in a given semester.
    Updates the Course model with top 5 related courses.

    Args:
        semester: Semester object to generate related courses for
    """
    # Get all courses that have sections in this semester
    courses = (
        Course.objects.select_related("subdepartment")
        .filter(section__semester=semester)
        .distinct()
    )

    # Convert to DataFrame with the features you need
    course_data = []
    course_id_map = {}  # Map index to course object
    for course in courses:
        # Get sections for additional info like topic
        sections = Section.objects.filter(course=course, semester=semester)
        topic = (
            sections.first().topic
            if sections.exists() and sections.first().topic
            else ""
        )

        idx = len(course_data)
        course_id_map[idx] = course
        course_data.append(
            {
                "Mnemonic": course.subdepartment.mnemonic,
                "Number": course.number,
                "Title": course.title,
                "Topic": topic,
                "Description": course.description or "",
                "Prerequisites": course.prerequisites,
            }
        )

    df = pd.DataFrame(course_data)
    print(f"Loaded {len(df)} courses from database")

    # Filter out courses without descriptions
    df_with_desc = df[df["Description"].str.strip() != ""]
    print(f"Found {len(df_with_desc)} courses with descriptions")

    if len(df_with_desc) == 0:
        print("No courses with descriptions found")
        return

    # Load a pre-trained model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate embeddings
    embeddings = model.encode(
        df_with_desc["Description"].tolist(), normalize_embeddings=True
    )

    print(f"Generated embeddings with shape: {embeddings.shape}")

    # Calculate pairwise cosine similarity between all courses
    similarity_matrix = cosine_similarity(embeddings)
    print(f"Calculated similarity matrix: {similarity_matrix.shape}")

    # Generate related courses for each course
    TOP_N = 5  # Store only top 5 related courses

    for idx, row in df_with_desc.iterrows():
        # Get similarity scores for this course
        similarities = similarity_matrix[idx]

        # Get indices of top N similar courses (excluding the course itself)
        top_similar_indices = np.argsort(similarities)[::-1][1 : TOP_N + 1]

        # Rerank with metadata (department, course level)
        reranked_indices = _rerank_with_metadata(
            idx, top_similar_indices, df_with_desc, similarity_matrix
        )

        related_courses = []
        for rank, sim_idx in enumerate(reranked_indices, 1):
            related_row = df_with_desc.iloc[sim_idx]
            sim_score = similarity_matrix[idx][sim_idx]
            related_courses.append(
                {
                    "rank": rank,
                    "mnemonic": related_row["Mnemonic"],
                    "number": int(related_row["Number"]),
                    "title": related_row["Title"],
                    "similarity_score": float(sim_score),
                }
            )

        # Update the course with related courses
        course = course_id_map[idx]
        course.related_courses = related_courses
        course.save()

    print(f"Successfully generated related courses for {len(df_with_desc)} courses")


def _rerank_with_metadata(course_idx, top_similar_indices, df, similarity_matrix):
    """
    Rerank similar courses by adding weights for:
    - Same department (Mnemonic): +0.15 bonus
    - Close course level (Number within 100): +0.1 bonus (decaying with distance)
    - Prerequisities: +0.3 bonus
    """
    course_mnemonic = df.iloc[course_idx]["Mnemonic"]
    course_number = df.iloc[course_idx]["Number"]
    course_prerequisites = df.iloc[course_idx]["Prerequisites"]

    rescored = []
    for sim_idx in top_similar_indices:
        base_sim = similarity_matrix[course_idx][sim_idx]
        bonus = 0.0

        # Same department bonus
        if df.iloc[sim_idx]["Mnemonic"] == course_mnemonic:
            bonus += 0.15

        # Close course level bonus (within 100 levels)
        level_diff = abs(df.iloc[sim_idx]["Number"] - course_number)
        if level_diff <= 100:
            bonus += 0.1 * (1 - level_diff / 100)  # decay as distance increases

        # Prerequisite bonus
        # Check if related course is a prerequisite for current course
        related_course_code = (
            f"{df.iloc[sim_idx]['Mnemonic']} {df.iloc[sim_idx]['Number']}"
        )
        if course_prerequisites and related_course_code in course_prerequisites:
            bonus += 0.3

        final_score = min(1.0, base_sim + bonus)
        rescored.append({"index": sim_idx, "final_score": final_score})

    # Re-sort by final score
    rescored.sort(key=lambda x: x["final_score"], reverse=True)
    return [item["index"] for item in rescored]
