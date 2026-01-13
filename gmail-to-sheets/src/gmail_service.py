from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import base64
import time

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_gmail_service():
    creds = None
    token_path = 'token.json'

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            '../credentials/credentials.json',
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def extract_body(payload):
    if 'body' in payload and payload['body'].get('data'):
        return base64.urlsafe_b64decode(
            payload['body']['data']
        ).decode(errors='ignore')

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                return base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode(errors='ignore')

    return ""


def fetch_unread_emails(service):
    emails = []
    page_token = None
    page = 1

    while True:
        print(f"Fetching unread emails (page {page})...")

        response = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            pageToken=page_token
        ).execute()

        messages = response.get('messages', [])

        if not messages:
            break

        for idx, msg in enumerate(messages, start=1):
            try:
                print(f"  Fetching message {idx} on page {page}")

                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                headers = msg_data['payload']['headers']
                payload = msg_data['payload']

                email = {
                    "id": msg['id'],
                    "from": "",
                    "subject": "",
                    "date": "",
                    "content": extract_body(payload)
                }

                for h in headers:
                    if h['name'] == 'From':
                        email['from'] = h['value']
                    elif h['name'] == 'Subject':
                        email['subject'] = h['value']
                    elif h['name'] == 'Date':
                        email['date'] = h['value']

                emails.append(email)

            except Exception as e:
                print("  Skipping message due to error:", e)
                continue

        page_token = response.get('nextPageToken')
        if not page_token:
            break

        page += 1

    print(f"Total unread emails fetched: {len(emails)}")
    return emails


