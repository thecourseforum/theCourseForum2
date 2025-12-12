import os
from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import Course, StudyGuide

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except Exception as e:  # pragma: no cover
    service_account = None
    build = None
    HttpError = Exception


SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def get_credentials(sa_path: str):
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    return creds


def create_doc(drive_service, name: str, folder_id: str | None):
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.document",
    }
    if folder_id:
        metadata["parents"] = [folder_id]
    file = drive_service.files().create(body=metadata, fields="id").execute()
    return file["id"]


def set_public_edit(drive_service, file_id: str):
    permission = {
        "type": "anyone",
        "role": "writer",
        "allowFileDiscovery": False,
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()


def init_doc_content(docs_service, file_id: str, header: str):
    # Insert a simple header at the top of the document
    body = {
        "requests": [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": header + "\n\n"
                }
            }
        ]
    }
    docs_service.documents().batchUpdate(documentId=file_id, body=body).execute()


class Command(BaseCommand):
    help = "Create Google Docs for course study guides and link them to StudyGuide entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--service_account_json",
            type=str,
            default=os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"),
            help="Path to Google service account JSON key file (or set GOOGLE_SERVICE_ACCOUNT_JSON)",
        )
        parser.add_argument(
            "--folder_id",
            type=str,
            default=os.environ.get("GOOGLE_DRIVE_FOLDER_ID"),
            help="Optional Drive folder ID to place created docs (or set GOOGLE_DRIVE_FOLDER_ID)",
        )
        parser.add_argument(
            "--share_public",
            action="store_true",
            help="Grant public writer access (anyone with the link can edit)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit number of courses processed",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Recreate or replace doc IDs for courses that already have a StudyGuide",
        )
        parser.add_argument(
            "--mnemonic",
            type=str,
            help="Only process courses for a given subdepartment mnemonic (e.g., CS)",
        )

    def handle(self, *args, **options):
        if build is None or service_account is None:
            raise CommandError(
                "Google API libraries not found. Please install requirements and retry."
            )

        sa_path = options["service_account_json"]
        if not sa_path or not os.path.exists(sa_path):
            raise CommandError(
                "Provide --service_account_json or set GOOGLE_SERVICE_ACCOUNT_JSON to a valid file path."
            )

        creds = get_credentials(sa_path)
        drive = build("drive", "v3", credentials=creds)
        docs = build("docs", "v1", credentials=creds)

        qs = Course.objects.all().select_related("subdepartment")
        if options.get("mnemonic"):
            qs = qs.filter(subdepartment__mnemonic=options["mnemonic"])

        processed = 0
        for course in qs.iterator():
            sg = StudyGuide.objects.filter(course=course).first()
            if sg and sg.google_doc_id and not options["overwrite"]:
                continue

            try:
                name = f"Study Guide – {course.subdepartment.mnemonic} {course.number}: {course.title}"
                file_id = create_doc(drive, name, options["folder_id"])
                # Initialize content header
                header = (
                    f"{course.subdepartment.mnemonic} {course.number} – {course.title} (Study Guide)\n"
                    f"Course ID: {course.id}\n"
                )
                init_doc_content(docs, file_id, header)

                if options["share_public"]:
                    set_public_edit(drive, file_id)

                if sg:
                    sg.google_doc_id = file_id
                    sg.save(update_fields=["google_doc_id"])
                else:
                    StudyGuide.objects.create(course=course, google_doc_id=file_id)

                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created doc {file_id} for {course.subdepartment.mnemonic} {course.number}"
                    )
                )
                if options.get("limit") and processed >= options["limit"]:
                    break
            except HttpError as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed for {course.subdepartment.mnemonic} {course.number}: {e}"
                    )
                )
            except Exception as e:  # pragma: no cover
                self.stderr.write(
                    self.style.ERROR(
                        f"Unexpected error for {course.subdepartment.mnemonic} {course.number}: {e}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"Processed {processed} course(s)."))