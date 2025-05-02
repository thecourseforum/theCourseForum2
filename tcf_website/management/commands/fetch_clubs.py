import csv
import os
import re
import backoff
import requests
from tqdm import tqdm

BASE_URL = "https://api.presence.io/virginia/v1/organizations"
session = requests.session()
TIMEOUT = 300

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


def strip_html_tags(text):
    return re.sub(r"<.*?>", "", text)


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=5,
)
def fetch_org_list():
    resp = session.get(BASE_URL, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=5,
)
def fetch_org_details(uri):
    resp = session.get(f"{BASE_URL}/{uri}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def write_csv(csv_file):
    orgs = fetch_org_list()
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # Note new column "OriginalCategories"
        w.writerow(
            [
                "Name",
                "Category",
                "OriginalCategories",
                "Application",
                "Description",
                "Photo",
            ]
        )

        for org in tqdm(orgs, desc="Processing clubs"):
            uri = org.get("uri")
            if not uri:
                continue
            try:
                d = fetch_org_details(uri)
                name = d.get("name", "")
                raw_cats = d.get("categories", [])

                # store the originals joined by $
                original_str = "$".join(raw_cats)

                # Application flag
                application = "No Application or Interview Required" not in raw_cats

                # Squash + dedupe, drop the no-app tag
                broad = {
                    SQUASH_MAP.get(c, c)
                    for c in raw_cats
                    if c != "No Application or Interview Required"
                }

                # 1) pick by fixed bucket priority
                main_cat = ""
                for bucket in BUCKET_PRIORITY:
                    if bucket in broad:
                        main_cat = bucket
                        break

                # 2) fallback
                if not main_cat:
                    main_cat = "Miscellaneous"

                desc = strip_html_tags(d.get("description", ""))
                photo = os.path.basename(d.get("photoUri", ""))

                w.writerow([name, main_cat, original_str, application, desc, photo])

            except Exception as e:
                print(f"Error {uri}: {e}")
                continue

    print("Done.")


if __name__ == "__main__":
    write_csv("club_data/csv/clubs.csv")
