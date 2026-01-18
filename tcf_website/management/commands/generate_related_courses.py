from sentence_transformers import SentenceTransformer
import pandas as pd
from django.core.management.base import BaseCommand

# Import the Django models
from tcf_website.models import Course, Semester, Section

class Command(BaseCommand):
    help = "Generate related courses using content fingerprints"
    
    def handle(self, *args, **options):
        ####### Phase 1: Content Fingerprint #######

        # Get Spring 2025 semester
        try:
            spring_2025 = Semester.objects.get(year=2025, season='SPRING')
            self.stdout.write(f"Found semester: {spring_2025}")
        except Semester.DoesNotExist:
            self.stdout.write(self.style.ERROR("Spring 2025 semester not found in database"))
            return

        # Load current semester course data from database
        # Get all courses that have sections in Spring 2025
        courses = Course.objects.select_related('subdepartment').filter(
            section__semester=spring_2025
        ).distinct()
        
        # Convert to DataFrame with the features you need
        course_data = []
        for course in courses:
            # Get sections for additional info like topic
            sections = Section.objects.filter(course=course, semester=spring_2025)
            topic = sections.first().topic if sections.exists() and sections.first().topic else ""
            
            course_data.append({
                'Mnemonic': course.subdepartment.mnemonic,
                'Number': course.number,
                'Title': course.title,
                'Topic': topic,
                'Description': course.description or ""
            })

        df = pd.DataFrame(course_data)
        self.stdout.write(f"Loaded {len(df)} courses from database")
        
        # Filter out courses without descriptions
        df_with_desc = df[df['Description'].str.strip() != '']
        self.stdout.write(f"Found {len(df_with_desc)} courses with descriptions")

        if len(df_with_desc) == 0:
            self.stdout.write(self.style.ERROR("No courses with descriptions found"))
            return

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
        embeddings = model.encode(df_with_desc["Description"].tolist(), normalize_embeddings=True)

        self.stdout.write(f"Generated embeddings with shape: {embeddings.shape}")

        ####### Phase 2: Reranking #######
        #Based on pre-req connection, department (Mnemonic), and level (Number)

        #formula? weighted highest to lowest: pre-req connection, department (Mnemonic), and level (Number)
        
        # TODO: Implement similarity calculations and reranking
        # For now, just report success
        self.stdout.write(self.style.SUCCESS("Successfully generated course embeddings!"))
