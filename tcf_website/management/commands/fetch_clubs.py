"""
Fetch club data from UVA's Presence API and write to a CSV file.

Usage:
docker exec -it tcf_django python manage.py fetch_clubs

Example:
docker exec -it tcf_django python manage.py fetch_clubs
"""

import csv
import os
import re
import backoff
import requests
from tqdm import tqdm
from django.core.management.base import BaseCommand

BASE_URL = "https://api.presence.io/virginia/v1/organizations"
session = requests.session()
TIMEOUT = 300


def strip_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r"<.*?>", "", text)


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=5,
)
def fetch_org_list():
    """Fetch the list of organizations from the API."""
    resp = session.get(BASE_URL, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=5,
)
def fetch_org_details(uri):
    """Fetch detailed information for a specific organization."""
    resp = session.get(f"{BASE_URL}/{uri}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def process_organization(org, writer):
    """Process a single organization and write its data to CSV."""
    uri = org.get("uri")
    if not uri:
        return

    try:
        details = fetch_org_details(uri)
        name = details.get("name", "")
        raw_cats = details.get("categories", [])

        # Store all categories as a delimited string
        categories_str = "$".join(raw_cats)

        # Application flag
        application = "No Application or Interview Required" not in raw_cats

        desc = strip_html_tags(details.get("description", ""))
        time = details.get("regularMeetingTime", "")
        photo = os.path.basename(details.get("photoUri", ""))

        writer.writerow([name, categories_str, application, desc, time, photo])

    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"Error {uri}: {e}")


def write_csv(csv_file):
    """Fetch club data and write it to a CSV file."""
    orgs = fetch_org_list()
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Name",
                "Categories",
                "Application",
                "Description",
                "Time",
                "Photo",
            ]
        )

        for org in tqdm(orgs, desc="Processing clubs"):
            process_organization(org, writer)

    print("Done.")


class Command(BaseCommand):
    help = "Fetch club data from UVA's Presence API and write to a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="tcf_website/management/commands/club_data/csv/clubs.csv",
            help="Output CSV file path",
        )

    def handle(self, *args, **options):
        csv_file = options["output"]
        self.stdout.write(f"Fetching club data and writing to {csv_file}...")
        write_csv(csv_file)
        self.stdout.write(self.style.SUCCESS("Successfully fetched club data."))
