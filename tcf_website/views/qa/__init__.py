"""Q&A views."""

from .views import (
    AnswerForm,
    DeleteAnswer,
    DeleteQuestion,
    QuestionForm,
    check_duplicate,
    downvote_answer,
    downvote_question,
    edit_answer,
    edit_question,
    new_answer,
    new_question,
    upvote_answer,
    upvote_question,
)

__all__ = [
    "AnswerForm",
    "DeleteAnswer",
    "DeleteQuestion",
    "QuestionForm",
    "check_duplicate",
    "downvote_answer",
    "downvote_question",
    "edit_answer",
    "edit_question",
    "new_answer",
    "new_question",
    "upvote_answer",
    "upvote_question",
]
