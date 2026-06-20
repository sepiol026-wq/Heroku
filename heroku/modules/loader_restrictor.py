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

ANS_COUNT = 4


@dataclass()
class PollStep:
    key: str
    answer_index: int

    @property
    def answer_keys(self):
        return [f"{self.key}:ans{i + 1}" for i in range(ANS_COUNT)]

    def is_correct(self, index: int):
        return self.answer_index == index


@dataclass()
class PollStatus:
    poll_id: int
    message_id: int
    answers: list[bool]
    step: int


QUESTIONS = [
    PollStep("q1", 0),
    PollStep("q2", 1),
    PollStep("q3", 2),
    PollStep("q4", 3),
    PollStep("q5", 0),
]


@loader.tds
class LoaderRestrictor(loader.Module):
    strings = {
        "name": "LoaderRestrictor",
        "q1": "test",
        "q1:ans1": "1",
        "q1:ans2": "2",
        "q1:ans3": "3",
        "q1:ans4": "4",
        "q2": "test 1",
        "q2:ans1": "1",
        "q2:ans2": "2",
        "q2:ans3": "3",
        "q2:ans4": "4",
        "q3": "test 2",
        "q3:ans1": "1",
        "q3:ans2": "2",
        "q3:ans3": "3",
        "q3:ans4": "4",
        "q4": "test 3",
        "q4:ans1": "1",
        "q4:ans2": "2",
        "q4:ans3": "3",
        "q4:ans4": "4",
        "q5": "test 4",
        "q5:ans1": "1",
        "q5:ans2": "2",
        "q5:ans3": "3",
        "q5:ans4": "4",
    }

    async def client_ready(self):
        self.poll: PollStatus | None = None

    def _build_poll(self, poll_step: PollStep) -> InputMediaPoll:
        poll = Poll(
            id=0,
            question=TextWithEntities(*html.parse(self.strings[poll_step.key])),
            answers=[
                PollAnswer(
                    text=TextWithEntities(*html.parse(self.strings[ans])),
                    option=str(i),
                )
                for i, ans in enumerate(poll_step.answer_keys)
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
        await self.inline.bot.send_message(
            self.client.tg_id,
            f"Done with {len([i for i in self.poll.answers if i])}/{len(self.poll.answers)} correct answers",
        )

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
