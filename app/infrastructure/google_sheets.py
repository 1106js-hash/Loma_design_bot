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

    # ======================
    # START FORM
    # ======================

    def append_start_form(self, user_id: int, name: str, phone: str, email: str):
        sheet = self.spreadsheet.worksheet("start_form")
        sheet.append_row([user_id, name, phone, email])

    # ======================
    # TZ ANSWERS
    # ======================

    def upsert_tz_answer(self, user_id: int, section: str, question_id: int, answer: str):
        sheet = self.spreadsheet.worksheet("tz_answers")
        rows = sheet.get_all_values()

        # ищем существующую строку
        for idx, row in enumerate(rows[1:], start=2):  # пропускаем header
            row_user_id = row[0]
            row_question_id = row[2]

            if str(row_user_id) == str(user_id) and str(row_question_id) == str(question_id):
                    # обновляем колонку answer (4 колонка)
                sheet.update_cell(idx, 4, answer)
                return

        # если не нашли — добавляем новую строку
        sheet.append_row([user_id, section, question_id, answer])


    # ======================
    # GET SKIPPED QUESTIONS
    # ======================

    def get_skipped_questions(self, user_id: int):
        sheet = self.spreadsheet.worksheet("tz_answers")

        rows = sheet.get_all_values()

        # если нет данных
        if len(rows) <= 1:
            return []

        skipped = []

        # пропускаем заголовок (первая строка)
        for row in rows[1:]:
            row_user_id = str(row[0])
            section = row[1]
            question_id = int(row[2])
            answer = row[3]

            if row_user_id == str(user_id) and answer == "__SKIPPED__":
                skipped.append((section, question_id))

        return skipped

    # ======================
    # GET ALL USER ANSWERS
    # ======================

    def get_user_answers(self, user_id: int):
        sheet = self.spreadsheet.worksheet("tz_answers")
        rows = sheet.get_all_values()

        if len(rows) <= 1:
            return {}

        answers = {}

        for row in rows[1:]:
            if len(row) < 4:
                continue

            row_user_id = str(row[0])
            question_id = row[2]
            answer = row[3]

            if row_user_id == str(user_id):
                answers[str(question_id)] = answer

        return answers
