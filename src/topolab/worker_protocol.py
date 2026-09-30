"""Versioned JSON messages shared by the local run manager and worker."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from topolab.problem import TopologyProblem, TopologyResult

type Version = Literal["topolab.a2.worker.v1"]
WORKER_PROTOCOL_VERSION: Version = "topolab.a2.worker.v1"


class _Message(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    version: Version = WORKER_PROTOCOL_VERSION
    run_id: Annotated[str, Field(min_length=1)]


class Start(_Message):
    kind: Literal["start"] = "start"
    problem: TopologyProblem


class Cancel(_Message):
    kind: Literal["cancel"] = "cancel"


class Started(_Message):
    kind: Literal["started"] = "started"
    pid: Annotated[int, Field(strict=True, gt=0)]


class Progress(_Message):
    kind: Literal["progress"] = "progress"
    iteration: Annotated[int, Field(strict=True, gt=0)]


class Succeeded(_Message):
    kind: Literal["succeeded"] = "succeeded"
    result: TopologyResult


class Failed(_Message):
    kind: Literal["failed"] = "failed"
    error: Annotated[str, Field(min_length=1)]


class Cancelled(_Message):
    kind: Literal["cancelled"] = "cancelled"


type Command = Annotated[Start | Cancel, Field(discriminator="kind")]
type Event = Annotated[
    Started | Progress | Succeeded | Failed | Cancelled,
    Field(discriminator="kind"),
]

_COMMAND_ADAPTER: TypeAdapter[Command] = TypeAdapter(Command)
_EVENT_ADAPTER: TypeAdapter[Event] = TypeAdapter(Event)


def parse_command(line: str) -> Command:
    return _COMMAND_ADAPTER.validate_json(line)


def parse_event(line: str) -> Event:
    return _EVENT_ADAPTER.validate_json(line)


def encode(message: _Message) -> str:
    return message.model_dump_json() + "\n"
