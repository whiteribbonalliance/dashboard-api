"""
This enum is used to help differentiate between question1, question2 etc.
A question code is directly related to a response in a campaign, some campaigns have multiple responses, thus multiple
question codes.
question 1 -> response 1 etc.
"""

from enum import Enum


class QuestionCode(Enum):
    q1: str = "q1"
    q2: str = "q2"
