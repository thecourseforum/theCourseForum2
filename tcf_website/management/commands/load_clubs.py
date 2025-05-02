"""
Import club data from CSV into the database.
This module handles processing and categorization of club data.
"""

import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from tqdm import tqdm

from tcf_website.models import Club, ClubCategory


# ── fine-grained → broad buckets ────────────────────────────────────────────
SQUASH_MAP = {
    # Greek Life
    "Fraternity or Sorority": "Greek Life",
    "Inter-Fraternity Council (IFC)": "Greek Life",
    "Inter-Sorority Council (ISC)": "Greek Life",
    "Multicultural Greek Council (MGC)": "Greek Life",
    "National Pan-Hellenic Council (NPHC)": "Greek Life",
    # Identity & Culture
    "Cultural & Ethnic": "Identity & Culture",
    "Black Presidents Council": "Identity & Culture",
    "L2K": "Identity & Culture",
    "International": "Identity & Culture",
    "FGLI": "Identity & Culture",
    # Academic & Professional
    "Academic & Professional": "Academic & Professional",
    "Commerce/Business": "Academic & Professional",
    "Data Sciences": "Academic & Professional",
    "Leadership Development": "Academic & Professional",
    "Internships and Employment": "Academic & Professional",
    "Honor Society": "Academic & Professional",
    # Arts & Media
    "Visual & Performing Arts": "Arts & Media",
    "Media & Publications": "Arts & Media",
    "Acapella Groups": "Arts & Media",
    # Recreation & Social
    "Social & Hobby": "Recreation & Social",
    "Club Sport": "Recreation & Social",
    # Service & Advocacy
    "Public Service": "Service & Advocacy",
    "Political & Advocacy": "Service & Advocacy",
    "Peer Mentors": "Service & Advocacy",
    "Health and Wellness": "Service & Advocacy",
    "Sustainability": "Service & Advocacy",
    "Special Status Organization (SSO)": "Service & Advocacy",
    "Honors and Awards": "Service & Advocacy",
    # Campus Units
    "Administrative Unit": "Campus Units",
    "Department, Schools, or Centers": "Campus Units",
    "Department Group or Program": "Campus Units",
    "Residence Hall": "Campus Units",
    "Agency": "Campus Units",
    "Northern Virginia": "Campus Units",
    # Professional Schools
    "Darden School": "Professional Schools",
    "Law School": "Professional Schools",
}

# ── fixed pick order ────────────────────────────────────────────────────────
BUCKET_PRIORITY = [
    "Greek Life",
    "Identity & Culture",
    "Service & Advocacy",
    "Professional Schools",
    "Academic & Professional",
    "Arts & Media",
    "Recreation & Social",
    "Campus Units",
]


class Command(BaseCommand):
    """Django management command to import club data from CSV into the database."""

    help = "Imports club data from clubs.csv into the database"

    def determine_category(self, raw_categories):
        """Determine the appropriate category for a club based on its raw categories."""
        # Squash + dedupe, drop the no-app tag
        broad = {
            SQUASH_MAP.get(c, c)
            for c in raw_categories
            if c != "No Application or Interview Required"
        }

        # Pick by fixed bucket priority
        for bucket in BUCKET_PRIORITY:
            if bucket in broad:
                return bucket

        # Fallback
        return "Miscellaneous"

    def get_or_create_category(self, category_name, categories_dict):
        """Get or create a ClubCategory object."""
        if category_name in categories_dict:
            return categories_dict[category_name]

        slug = slugify(category_name).upper()[:4]
        category, created = ClubCategory.objects.get_or_create(
            name=category_name, defaults={"slug": slug}
        )
        categories_dict[category_name] = category

        if created:
            self.stdout.write(f"Created category: {category_name}")

        return category

    def handle(self, *args, **options):
        """Execute the command to import club data."""
        self.stdout.write("Loading club data...")

        csv_file = "tcf_website/management/commands/club_data/csv/clubs.csv"
        photo_base_url = (
            "https://virginia-cdn.presence.io/organization-photos/"
            "cea28f2b-baa9-4c47-8879-da8d675e4471/"
        )

        # Dictionary to keep track of created categories
        categories = {}

        # Clear existing clubs for a clean import
        Club.objects.all().delete()

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader)

            for row in tqdm(reader, desc="Importing clubs"):
                if len(row) < 5:
                    self.stdout.write(
                        self.style.WARNING(f"Skipping row: {row} - insufficient data")
                    )
                    continue

                self.process_club_row(row, categories, photo_base_url)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported {Club.objects.count()} clubs")
        )

    def process_club_row(self, row, categories, photo_base_url):
        """Process a single row from the CSV and create a club."""
        name = row[0]
        raw_categories = row[1].split("$")
        application_required = row[2].lower() == "true"
        description = row[3]
        meeting_time = row[4]
        photo = row[5]

        # Process categories
        category_name = self.determine_category(raw_categories)
        category = self.get_or_create_category(category_name, categories)

        # Create photo URL
        photo_url = ""
        if photo:
            photo_url = f"{photo_base_url}{photo}"

        # Create the club
        Club.objects.create(
            name=name,
            category=category,
            application_required=application_required,
            description=description,
            meeting_time=meeting_time,
            photo_url=photo_url,
        )
