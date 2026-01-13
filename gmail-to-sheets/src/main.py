import json
import os

from gmail_service import get_gmail_service, fetch_unread_emails
from sheets_service import get_sheets_service
from config import SPREADSHEET_ID, SHEET_NAME

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "state.json")



def load_state():
    if not os.path.exists(STATE_FILE):
        return {"processed_ids": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def append_emails_to_sheet(emails):
    sheets_service = get_sheets_service()

    values = []
    for email in emails:
        values.append([
            email["from"],
            email["subject"],
            email["date"],
            email["content"]
        ])

    if not values:
        print("No new emails to add.")
        return

    body = {"values": values}

    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:D",
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f"Added {len(values)} emails to Google Sheets.")


def mark_emails_as_read(gmail_service, emails):
    if not emails:
        return

    gmail_service.users().messages().batchModify(
        userId="me",
        body={
            "ids": [email["id"] for email in emails],
            "removeLabelIds": ["UNREAD"]
        }
    ).execute()


if __name__ == "__main__":
    gmail_service = get_gmail_service()
    state = load_state()


    all_unread = fetch_unread_emails(gmail_service)

    # 🔐 FILTER ALREADY-PROCESSED EMAILS
    new_emails = [
    email for email in all_unread
    if email["id"] not in state["processed_ids"]
]

if not all_unread:
    print("No unread emails found in Gmail.")

if not new_emails:
    print("No new unread emails to process (already processed).")

    append_emails_to_sheet(new_emails)
    mark_emails_as_read(gmail_service, new_emails)

    # ✅ UPDATE STATE
    for email in new_emails:
        state["processed_ids"].append(email["id"])

    save_state(state)

    print("Process completed successfully.")
