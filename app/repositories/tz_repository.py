from abc import ABC, abstractmethod


class BaseTZRepository(ABC):

    @abstractmethod
    async def get_user_answers(self, user_id: int) -> dict:
        pass

    @abstractmethod
    async def get_skipped_questions(self, user_id: int):
        pass

    @abstractmethod
    async def save_answer(
        self,
        user_id: int,
        username: str,
        full_name: str,
        section: str,
        question_id: int,
        answer: str,
    ):
        pass
