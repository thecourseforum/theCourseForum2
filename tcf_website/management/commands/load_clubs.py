import csv
import os

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from tqdm import tqdm

from tcf_website.models import Club, ClubCategory


class Command(BaseCommand):
    help = "Imports club data from clubs.csv into the database"

    def handle(self, *args, **options):
        self.stdout.write("Loading club data...")

        csv_file = "tcf_website/management/commands/club_data/csv/clubs.csv"
        photo_base_url = "https://virginia-cdn.presence.io/organization-photos/cea28f2b-baa9-4c47-8879-da8d675e4471/"

        # Dictionary to keep track of created categories
        categories = {}

        # Clear existing clubs for a clean import
        Club.objects.all().delete()

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader)

            for row in tqdm(reader, desc="Importing clubs"):
                if len(row) < 6:
                    self.stdout.write(
                        self.style.WARNING(f"Skipping row: {row} - insufficient data")
                    )
                    continue

                name = row[0]
                category_name = row[1]
                # Skip original_categories (row[2])
                application_required = row[3].lower() == "true"
                description = row[4]
                photo = row[5]

                # Get or create the category
                if category_name in categories:
                    category = categories[category_name]
                else:
                    slug = slugify(category_name).upper()[:4]
                    category, created = ClubCategory.objects.get_or_create(
                        name=category_name, defaults={"slug": slug}
                    )
                    categories[category_name] = category
                    if created:
                        self.stdout.write(f"Created category: {category_name}")

                # Create photo URL
                photo_url = ""
                if photo:
                    photo_url = f"{photo_base_url}{photo}"

                # Create the club
                club = Club.objects.create(
                    name=name,
                    category=category,
                    application_required=application_required,
                    description=description,
                    photo_url=photo_url,
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported {Club.objects.count()} clubs")
        )
