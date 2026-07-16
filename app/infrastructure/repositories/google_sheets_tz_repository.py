import asyncio
import gspread
from google.oauth2.service_account import Credentials

from app.core.config import GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_PATH
from app.repositories.tz_repository import BaseTZRepository


class GoogleSheetsTZRepository(BaseTZRepository):

    def __init__(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=scopes
        )
        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(GOOGLE_SHEETS_ID)

    # ======================================================
    # PUBLIC ASYNC METHODS
    # ======================================================

    async def get_user_answers(self, user_id: int) -> dict:
        return await asyncio.to_thread(
            self._get_user_answers_sync,
            user_id
        )

    async def get_skipped_questions(self, user_id: int):
        return await asyncio.to_thread(
            self._get_skipped_questions_sync,
            user_id
        )

    async def save_answer(
        self,
        user_id: int,
        username: str,
        full_name: str,
        section: str,
        question_id: int,
        answer: str,
    ):
        await asyncio.to_thread(
            self._save_answer_sync,
            user_id,
            username,
            full_name,
            section,
            question_id,
            answer
        )

    async def save_start_form(
        self,
        user_id: int,
        username: str,
        full_name: str,
        name: str,
        phone: str,
        email: str,
    ):
        await asyncio.to_thread(
            self._save_start_form_sync,
            user_id,
            username,
            full_name,
            name,
            phone,
            email
        )

    # ======================================================
    # SYNC IMPLEMENTATION
    # ======================================================

    def _normalize_qid(self, raw_value):
        """
        Приводит ID к строке без .0
        """
        try:
            return str(int(float(str(raw_value).strip())))
        except:
            return str(raw_value).strip()

    def _get_user_answers_sync(self, user_id: int):
        sheet = self.spreadsheet.worksheet("tz_answers")
        rows = sheet.get_all_values()

        if len(rows) <= 1:
            return {}

        answers = {}

        for row in rows[1:]:
            if len(row) < 6:
                continue

            row_user_id = str(row[0]).strip()

            if row_user_id != str(user_id):
                continue

            normalized_qid = self._normalize_qid(row[4])
            answer = row[5]

            answers[normalized_qid] = answer

        return answers

    def _get_skipped_questions_sync(self, user_id: int):
        sheet = self.spreadsheet.worksheet("tz_answers")
        rows = sheet.get_all_values()

        if len(rows) <= 1:
            return []

        skipped = []

        for row in rows[1:]:
            if len(row) < 6:
                continue

            row_user_id = str(row[0]).strip()

            if row_user_id != str(user_id):
                continue

            section = row[3]
            normalized_qid = self._normalize_qid(row[4])
            answer = row[5]

            if answer == "__SKIPPED__":
                skipped.append((section, int(normalized_qid)))

        return skipped

    def _save_answer_sync(
        self,
        user_id: int,
        username: str,
        full_name: str,
        section: str,
        question_id: int,
        answer: str,
    ):
        sheet = self.spreadsheet.worksheet("tz_answers")
        rows = sheet.get_all_values()

        normalized_question_id = self._normalize_qid(question_id)

        for idx, row in enumerate(rows[1:], start=2):
            if len(row) < 6:
                continue

            row_user_id = str(row[0]).strip()
            row_qid = self._normalize_qid(row[4])

            if (
                row_user_id == str(user_id)
                and row_qid == normalized_question_id
            ):
                sheet.update_cell(idx, 6, answer)
                return

        sheet.append_row([
            user_id,
            username,
            full_name,
            section,
            normalized_question_id,
            answer
        ])

    def _save_start_form_sync(
        self,
        user_id: int,
        username: str,
        full_name: str,
        name: str,
        phone: str,
        email: str,
    ):
        sheet = self.spreadsheet.worksheet("start_form")
        sheet.append_row([
            user_id,
            username,
            full_name,
            name,
            phone,
            email
        ])
