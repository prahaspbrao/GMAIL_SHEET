from sheets_service import get_sheets_service
from config import SPREADSHEET_ID, SHEET_NAME

service = get_sheets_service()

values = [
    ["Test Sender", "Test Subject", "Test Date", "Test Content"]
]

body = {
    "values": values
}

service.spreadsheets().values().append(
    spreadsheetId=SPREADSHEET_ID,
    range=f"{SHEET_NAME}!A:D",
    valueInputOption="RAW",
    body=body
).execute()

print("Row added successfully!")
