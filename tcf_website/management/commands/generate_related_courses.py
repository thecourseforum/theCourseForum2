import os
import sys
from pathlib import Path

import django

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
sys.path.insert(0, project_root)

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcf_core.settings.dev")
django.setup()

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Import the Django models
from tcf_website.models import Course, Section, Semester


class Command(BaseCommand):
    help = "Generate related courses using content fingerprints"

    def handle(self, *args, **options):
        ####### Phase 1: Content Fingerprint #######

        # Get Spring 2025 semester
        try:
            spring_2025 = Semester.objects.get(year=2025, season="SPRING")
            self.stdout.write(f"Found semester: {spring_2025}")
        except Semester.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Spring 2025 semester not found in database")
            )
            return

        # Load current semester course data from database
        # Get all courses that have sections in Spring 2025
        courses = (
            Course.objects.select_related("subdepartment")
            .filter(section__semester=spring_2025)
            .distinct()
        )

        # Convert to DataFrame with the features you need
        course_data = []
        for course in courses:
            # Get sections for additional info like topic
            sections = Section.objects.filter(course=course, semester=spring_2025)
            topic = (
                sections.first().topic
                if sections.exists() and sections.first().topic
                else ""
            )

            course_data.append(
                {
                    "Mnemonic": course.subdepartment.mnemonic,
                    "Number": course.number,
                    "Title": course.title,
                    "Topic": topic,
                    "Description": course.description or "",
                    "Prerequisites": course.prerequisites
                }
            )

        df = pd.DataFrame(course_data)
        self.stdout.write(f"Loaded {len(df)} courses from database")

        # Filter out courses without descriptions
        df_with_desc = df[df["Description"].str.strip() != ""]
        self.stdout.write(f"Found {len(df_with_desc)} courses with descriptions")

        if len(df_with_desc) == 0:
            self.stdout.write(self.style.ERROR("No courses with descriptions found"))
            return

        # relevant columns:
        """
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
        """

        # Load a pre-trained model
        model = SentenceTransformer("all-MiniLM-L6-v2")

        # Generate embeddings
        # use only description or title + description for embeddings?
        embeddings = model.encode(
            df_with_desc["Description"].tolist(), normalize_embeddings=True
        )

        self.stdout.write(f"Generated embeddings with shape: {embeddings.shape}")

        ####### Phase 2: Similarity Calculations #######

        # Calculate pairwise cosine similarity between all courses
        similarity_matrix = cosine_similarity(embeddings)
        self.stdout.write(f"Calculated similarity matrix: {similarity_matrix.shape}")

        ####### Phase 3: Reranking #######
        # Based on pre-req connection, department (Mnemonic), and level (Number)

        TOP_N = 10  # Number of related courses to find per course
        related_courses_list = []

        for idx, row in df_with_desc.iterrows():
            course_code = f"{row['Mnemonic']} {row['Number']}"

            # Get similarity scores for this course
            similarities = similarity_matrix[idx]

            # Get indices of top N similar courses (excluding the course itself at index 0)
            top_similar_indices = np.argsort(similarities)[::-1][1 : TOP_N + 1]

            # Rerank with metadata (department, course level)
            reranked_indices = self._rerank_with_metadata(
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
                        "number": related_row["Number"],
                        "title": related_row["Title"],
                        "similarity_score": float(sim_score),
                    }
                )

            related_courses_list.append(
                {
                    "course_code": course_code,
                    "course_title": row["Title"],
                    "related_courses": related_courses,
                }
            )

        self.stdout.write(
            f"\nFound related courses for {len(related_courses_list)} courses"
        )

        # Show sample output for first 5 courses
        self.stdout.write("\n=== Sample Results ===")
        for i, item in enumerate(related_courses_list[:5]):
            self.stdout.write(f"\n{item['course_code']}: {item['course_title']}")
            for rel in item["related_courses"][:5]:
                self.stdout.write(
                    f"  {rel['rank']}. {rel['mnemonic']} {rel['number']}: {rel['similarity_score']:.4f}"
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully generated and ranked related courses!")
        )

    def _rerank_with_metadata(
        self, course_idx, top_similar_indices, df, similarity_matrix
    ):
        """
        Rerank similar courses by adding weights for:
        - Same department (Mnemonic): +0.15 bonus
        - Close course level (Number within 100): +0.1 bonus (decaying with distance)
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
            if df.iloc[sim_idx]["Prerequisites"] in course_prerequisites:
                bonus += 0.3

            final_score = min(1.0, base_sim + bonus)
            rescored.append({"index": sim_idx, "final_score": final_score})

        # Re-sort by final score
        rescored.sort(key=lambda x: x["final_score"], reverse=True)
        return [item["index"] for item in rescored]
