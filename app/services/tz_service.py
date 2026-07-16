from app.domain.tz_structure import SECTIONS


class TZService:

    def __init__(self, repository):
        self.repository = repository

    # ======================================================
    # START
    # ======================================================

    async def start(self, user_id: int):
        raw_answers = await self.repository.get_user_answers(user_id)

        # Жёсткая нормализация ключей
        answers = {}

        for k, v in raw_answers.items():
            try:
                normalized_key = str(int(k))
            except:
                normalized_key = str(k).strip()

            answers[normalized_key] = v

        sections_progress = {}
        completed = 0

        for key, section in SECTIONS.items():
            answered, total = self.calculate_section_progress(answers, section)

            sections_progress[key] = {
                "section": section,
                "answered": answered,
                "total": total
            }

            if answered == total and total > 0:
                completed += 1

        return {
            "answers": answers,
            "completed": completed,
            "total_sections": len(SECTIONS),
            "sections_progress": sections_progress
        }

    # ======================================================
    # ПРОГРЕСС РАЗДЕЛА
    # ======================================================

    def calculate_section_progress(self, answers: dict, section: dict):
        total = len(section["questions"])
        answered = 0

        for question in section["questions"]:
            qid = str(question["id"])

            if qid in answers and answers[qid] != "__SKIPPED__":
                answered += 1

        return answered, total

    # ======================================================
    # ОБРАБОТКА ОТВЕТА
    # ======================================================

    async def process_answer(
        self,
        user_id: int,
        username: str,
        full_name: str,
        section_key: str,
        question_index: int,
        answer_value: str,
        answers: dict,
        skipped_flow: list | None,
        skipped_index: int | None
    ):

        section = SECTIONS[section_key]
        question = section["questions"][question_index]

        qid = str(question["id"])

        # ==================================================
        # 🔥 ЕСЛИ ВЫБРАНО "ДРУГОЕ" — НУЖЕН ДОП. ТЕКСТ
        # ==================================================

        if (
            question.get("options")
            and "Другое" in question.get("options", [])
            and answer_value == "Другое"
        ):
            return {
                "mode": "need_other_text",
                "section_key": section_key,
                "question_index": question_index,
                "answers": answers
            }

        # ==================================================
        # СОХРАНЕНИЕ ОТВЕТА
        # ==================================================

        answers[qid] = answer_value

        await self.repository.save_answer(
            user_id=user_id,
            username=username,
            full_name=full_name,
            section=section_key,
            question_id=question["id"],
            answer=answer_value
        )

        # ==================================================
        # ПРОПУСКИ
        # ==================================================

        if skipped_flow:

            skipped_index = 0 if skipped_index is None else skipped_index + 1

            if skipped_index < len(skipped_flow):
                next_section, next_question_id = skipped_flow[skipped_index]

                next_question_index = next(
                    i for i, q in enumerate(SECTIONS[next_section]["questions"])
                    if q["id"] == next_question_id
                )

                return {
                    "mode": "continue_skipped",
                    "section_key": next_section,
                    "question_index": next_question_index,
                    "skipped_index": skipped_index,
                    "answers": answers
                }

            return {
                "mode": "skipped_finished",
                "answers": answers
            }

        # ==================================================
        # ОБЫЧНЫЙ РЕЖИМ
        # ==================================================

        if question_index + 1 < len(section["questions"]):
            return {
                "mode": "next_question",
                "section_key": section_key,
                "question_index": question_index + 1,
                "answers": answers
            }

        return {
            "mode": "section_finished",
            "answers": answers
        }

    # ======================================================
    # ПОЛУЧЕНИЕ ВОПРОСА
    # ======================================================

    def get_question(self, section_key: str, question_index: int):
        section = SECTIONS[section_key]
        question = section["questions"][question_index]

        return {
            "section": section,
            "question": question,
            "total_questions": len(section["questions"]),
            "current_number": question_index + 1
        }
