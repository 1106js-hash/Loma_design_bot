import gspread
from google.oauth2.service_account import Credentials
from app.core.config import GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_PATH



class GoogleSheetsService:
    def __init__(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=scopes
        )
        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(GOOGLE_SHEETS_ID)

    def append_start_form(self, user_id: int, name: str, phone: str, email: str):
        sheet = self.spreadsheet.worksheet("start_form")
        sheet.append_row([user_id, name, phone, email])
