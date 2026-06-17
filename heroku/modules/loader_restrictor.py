# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

from dataclasses import dataclass
import logging

from herokutl.tl.types import (
    InputMediaPoll,
    Poll,
    PollAnswer,
    TextWithEntities,
    UpdateMessagePollVote,
)
from herokutl.tl.custom import Message

from .. import loader

logger = logging.getLogger(__name__)


@dataclass()
class PollStep:
    question: str
    answer_choices: list[str]
    answer_index: int
    # solution: str

    def is_correct(self, index: int):
        return self.answer_index == index


QUESTIONS = [
    PollStep("test", ["1", "2", "3", "4"], 0),
    PollStep("test 1", ["1", "2", "3", "4"], 1),
    PollStep("test 2", ["1", "2", "3", "4"], 2),
    PollStep("test 3", ["1", "2", "3", "4"], 3),
    PollStep("test 4", ["1", "2", "3", "4"], 0),
]


@loader.tds
class LoaderRestrictor(loader.Module):
    async def client_ready(self):
        self.poll = None

    @loader.need_update("poll_answer")
    async def poll_handler(self, update: UpdateMessagePollVote):
        if not self.get("passed", False):
            return

        logger.debug("Got %s update: %s", update.poll_id, update.to_dict())

    async def start_quiz(self):
        pass

    async def _next_step_quiz(self):
        pass

    @loader.command()
    async def testquiz(self, message: Message):
        step = next(iter(QUESTIONS))
        poll = Poll(
            id=0,
            question=TextWithEntities(text=step.question, entities=[]),
            answers=[
                PollAnswer(
                    text=TextWithEntities(text=ans, entities=[]),
                    option=bytes([i]),
                )
                for i, ans in enumerate(step.answer_choices)
            ],
            hash=0,
            quiz=True,
        )
        await self._client.send_file(
            message.chat_id,
            file=InputMediaPoll(poll=poll, correct_answers=[step.answer_index]),
        )
