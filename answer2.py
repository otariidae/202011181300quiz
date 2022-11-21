from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from dataclasses import dataclass, field
from ipaddress import IPv4Interface
from util import LogRecord


class RecordAbstractState(ABC):
    consecutive_timeout_threshold: int
    _context: ServerContext

    @abstractmethod
    def push_newer_record(self, record: LogRecord):
        ...


@dataclass(kw_only=True)
class RecordHealthyState(RecordAbstractState):
    """健康状態

    Attributes:
        last_timeout_datetime_chain: 直近で連続してタイムアウトした時刻のリスト
    """

    last_timeout_datetime_chain: list[datetime] = field(default_factory=list)

    def push_newer_record(self, record: LogRecord):
        if record.is_timed_out:
            self.last_timeout_datetime_chain.append(record.datetime)
            if (
                len(self.last_timeout_datetime_chain)
                >= self.consecutive_timeout_threshold
            ):
                self._context.transition_to(
                    RecordFailedState(
                        last_fail_datetime=self.last_timeout_datetime_chain[0]
                    )
                )
        else:
            self.last_timeout_datetime_chain = []


@dataclass(kw_only=True)
class RecordFailedState(RecordAbstractState):
    """故障状態

    Attributes:
        last_fail_datetime: 故障時刻
    """

    last_fail_datetime: datetime

    def push_newer_record(self, record: LogRecord):
        if not record.is_timed_out:
            self._context.transition_to(
                RecordRecoveredState(
                    last_fail_datetime=self.last_fail_datetime,
                    recovery_datetime=record.datetime,
                )
            )


@dataclass(kw_only=True)
class RecordRecoveredState(RecordHealthyState):
    """復旧状態

    Attributes:
        last_fail_datetime: 故障時刻
        recovery_datetime: 復旧時刻
    """

    last_fail_datetime: datetime
    recovery_datetime: datetime


@dataclass
class ServerContext:
    """サーバ状態のコンテクスト

    Attributes:
        consecutive_timeout_threshold: 連続してタイムアウトすると故障とみなす回数
    """

    consecutive_timeout_threshold: int
    _state: RecordAbstractState = field(default_factory=RecordHealthyState)

    def __post_init__(self):
        self._state._context = self
        self._state.consecutive_timeout_threshold = self.consecutive_timeout_threshold

    def push_newer_record(self, record: LogRecord):
        self._state.push_newer_record(record)

    def transition_to(self, state: RecordAbstractState):
        self._state = state
        self._state._context = self
        self._state.consecutive_timeout_threshold = self.consecutive_timeout_threshold

    @property
    def state(self):
        return self._state


ServerContextMap = dict[IPv4Interface, ServerContext]


def detect_failure_duration(
    log: Iterable[LogRecord], consecutive_timeout_threshold: int
) -> ServerContextMap:
    """読み込まれた監視ログからサーバ状態（健康・故障・復旧）を算出する

    Args:
        log: 読み込まれた監視ログ
        consecutive_timeout_threshold: 連続してタイムアウトすると故障とみなす回数
    """
    ip_context_map: dict[IPv4Interface, ServerContext] = {}
    for record in log:
        record_failure_context = ip_context_map.setdefault(
            record.ipv4interface, ServerContext(consecutive_timeout_threshold)
        )
        record_failure_context.push_newer_record(record)
    return ip_context_map


def print_failure_duration(
    log: Iterable[LogRecord], consecutive_timeout_threshold: int
):
    """読み込まれた監視ログからサーバの故障期間を出力する

    形式は1行ずつ：
    <サーバアドレス>, <故障時刻>, <復旧時刻>

    Args:
        log: 読み込まれた監視ログ
        consecutive_timeout_threshold: 連続してタイムアウトすると故障とみなす回数
    """
    failure_contexts = detect_failure_duration(log, consecutive_timeout_threshold)
    for ipv4interface, context in failure_contexts.items():
        if isinstance(context.state, RecordFailedState):
            print(f"{ipv4interface}, {context.state.last_fail_datetime.isoformat()},")
        elif isinstance(context.state, RecordRecoveredState):
            print(
                f"{ipv4interface}, {context.state.last_fail_datetime.isoformat()}, {context.state.recovery_datetime.isoformat()}"
            )
