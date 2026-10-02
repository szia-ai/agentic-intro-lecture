"""Output models passed to each framework as its output type, never pasted into prompts."""

from typing import Literal

from pydantic import BaseModel, Field


class Answer(BaseModel):  # the answering agent, all stages
    answer: str = Field(
        description="The answer in one or two sentences, with the number."
    )
    sql: str = Field(description="The SELECT statement that produced the answer.")


class Triage(BaseModel):  # stages 2 and 3: the first step decides the scenario
    scenario: Literal["answer", "clarify", "out_of_scope", "not_allowed"]
    question: str = Field(
        description="The one clarifying question to ask when the scenario is clarify; "
        "empty otherwise."
    )


class Review(BaseModel):  # stage 3
    approved: bool
    reason: str = Field(description="Why the SQL is right, or what to fix.")
