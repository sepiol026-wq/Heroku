# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from dataclasses import dataclass

from herokutl.extensions import html
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


@dataclass()
class PollStatus:
    poll_id: int
    message_id: int
    answers: list[bool]
    step: int


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
        self.poll: PollStatus | None = None

    def _build_poll(self, poll_step: PollStep) -> InputMediaPoll:
        poll = Poll(
            id=0,
            question=TextWithEntities(*html.parse(poll_step.question)),
            answers=[
                PollAnswer(
                    text=TextWithEntities(*html.parse(ans)),
                    option=str(i),
                )
                for i, ans in enumerate(poll_step.answer_choices)
            ],
            hash=0,
            quiz=True,
            public_voters=True,
            revoting_disabled=True,
        )
        return InputMediaPoll(poll=poll, correct_answers=[poll_step.answer_index])

    @loader.need_update("poll_answer")
    async def poll_handler(self, update: UpdateMessagePollVote):
        if self.get("passed", False):
            return

        if not self.poll or not update.poll_id == self.poll.poll_id:
            return

        self.poll.answers.append(
            update.positions[0] == QUESTIONS[self.poll.step].answer_index
        )

        await self.inline.bot.delete_message(self.client.tg_id, self.poll.message_id)

        await self._next_step_quiz()

    async def start_quiz(self):
        pass

    async def _next_step_quiz(self):
        if self.poll.step == len(QUESTIONS) - 1:
            return await self._end_quiz()

        self.poll.step += 1
        question = QUESTIONS[self.poll.step]

        poll_m: Message = await self.inline.bot.send_file(
            self.client.tg_id,
            file=self._build_poll(question),
        )
        self.poll.message_id = poll_m.id
        self.poll.poll_id = poll_m.media.poll.id

    async def _end_quiz(self):
        await self.inline.bot.send_message(self.client.tg_id, "done")

    @loader.command()
    async def testquiz(self, message: Message):
        step = next(iter(QUESTIONS))
        poll_m: Message = await self.inline.bot.send_file(
            self.client.tg_id,
            file=self._build_poll(step),
        )
        await message.delete()

        self.poll = PollStatus(
            poll_id=poll_m.media.poll.id,
            message_id=poll_m.id,
            answers=[],
            step=0,
        )
