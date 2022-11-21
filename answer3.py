from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from dataclasses import dataclass, field
from ipaddress import IPv4Interface
from util import LogRecord


class RecordAbstractState(ABC):
    consecutive_timeout_threshold: int
    overload_timeout_threshold: int
    consecutive_overload_threshold: int
    _context: ServerContext

    @abstractmethod
    def push_newer_record(self, record: LogRecord):
        ...


@dataclass(kw_only=True)
class RecordHealthyState(RecordAbstractState):
    """健康状態

    Attributes:
        last_timeout_datetime_chain: 直近で連続してタイムアウトした時刻のリスト
        last_overload_datetime_chain: 直近で連続して応答時間が長かった時刻のリスト
    """

    last_timeout_datetime_chain: list[datetime] = field(default_factory=list)
    last_overload_datetime_chain: list[datetime] = field(default_factory=list)

    def push_newer_record(self, record: LogRecord):
        if record.is_timed_out:
            self.last_overload_datetime_chain = []
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
            if record.response_ms > self.overload_timeout_threshold:
                self.last_overload_datetime_chain.append(record.datetime)
                if (
                    len(self.last_overload_datetime_chain)
                    >= self.consecutive_overload_threshold
                ):
                    self._context.transition_to(
                        RecordOverloadState(
                            last_overload_datetime=self.last_overload_datetime_chain[0]
                        )
                    )


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
                RecordFailRecoveredState(
                    last_fail_datetime=self.last_fail_datetime,
                    fail_recovery_datetime=record.datetime,
                )
            )


@dataclass(kw_only=True)
class RecordFailRecoveredState(RecordHealthyState):
    """故障からの復旧状態

    Attributes:
        last_fail_datetime: 故障時刻
        fail_recovery_datetime: 復旧時刻
    """

    last_fail_datetime: datetime
    fail_recovery_datetime: datetime


@dataclass(kw_only=True)
class RecordOverloadState(RecordAbstractState):
    """過負荷状態

    Attributes:
        last_overload_datetime: 過負荷時刻
    """

    last_overload_datetime: datetime

    def push_newer_record(self, record: LogRecord):
        if not record.response_ms > self.overload_timeout_threshold:
            self._context.transition_to(
                RecordOverloadRecorveredState(
                    last_overload_datetime=self.last_overload_datetime,
                    overload_recovery_datetime=record.datetime,
                )
            )


@dataclass(kw_only=True)
class RecordOverloadRecorveredState(RecordHealthyState):
    """過負荷からの復旧状態

    Attributes:
        last_overload_datetime: 過負荷時刻
        overload_recovery_datetime: 復旧時刻
    """

    last_overload_datetime: datetime
    overload_recovery_datetime: datetime


@dataclass
class ServerContext:
    """サーバ状態のコンテクスト

    Attributes:
        consecutive_timeout_threshold: 連続してタイムアウトすると故障とみなす回数
        overload_timeout_threshold: 超過すると過負荷とみなす応答時間（ミリ秒）
        consecutive_overload_threshold: 連続して応答時間が長いと過負荷とみなす回数
    """

    consecutive_timeout_threshold: int
    overload_timeout_threshold: int
    consecutive_overload_threshold: int
    _state: RecordAbstractState = field(default_factory=RecordHealthyState)

    def __post_init__(self):
        self._state._context = self
        self._state.consecutive_timeout_threshold = self.consecutive_timeout_threshold
        self._state.overload_timeout_threshold = self.overload_timeout_threshold
        self._state.consecutive_overload_threshold = self.consecutive_overload_threshold

    def push_newer_record(self, record: LogRecord):
        self._state.push_newer_record(record)

    def transition_to(self, state: RecordAbstractState):
        self._state = state
        self._state._context = self
        self._state.consecutive_timeout_threshold = self.consecutive_timeout_threshold
        self._state.overload_timeout_threshold = self.overload_timeout_threshold
        self._state.consecutive_overload_threshold = self.consecutive_overload_threshold

    @property
    def state(self):
        return self._state


def detect_failure_or_overload_duration(
    log: Iterable[LogRecord],
    consecutive_timeout_threshold: int,
    overload_timeout_threshold: int,
    consecutive_overload_threshold: int,
):
    """読み込まれた監視ログからサーバ状態（健康・故障・復旧）を算出する

    Args:
        consecutive_timeout_threshold: 連続してタイムアウトすると故障とみなす回数
        overload_timeout_threshold: 超過すると過負荷とみなす応答時間（ミリ秒）
        consecutive_overload_threshold: 連続して応答時間が長いと過負荷とみなす回数
    """
    ip_context_map: dict[IPv4Interface, ServerContext] = {}
    for record in log:
        record_failure_context = ip_context_map.setdefault(
            record.ipv4interface,
            ServerContext(
                consecutive_timeout_threshold,
                overload_timeout_threshold,
                consecutive_overload_threshold,
            ),
        )
        record_failure_context.push_newer_record(record)
    return ip_context_map


def print_failure_or_overload_duration(
    log: Iterable[LogRecord],
    consecutive_timeout_threshold: int,
    overload_timeout_threshold: int,
    consecutive_overload_threshold: int,
):
    """読み込まれた監視ログからサーバの故障期間と過負荷になっている期間を出力する

    形式は1行ずつ：
    <サーバアドレス>, <故障時刻>, <故障復旧時刻>, <過負荷時刻>, <過負荷復旧時刻>

    Args:
        log: 読み込まれた監視ログ
        consecutive_timeout_threshold: 連続してタイムアウトすると故障とみなす回数
    """
    ip_context_map = detect_failure_or_overload_duration(
        log,
        consecutive_timeout_threshold,
        overload_timeout_threshold,
        consecutive_overload_threshold,
    )
    for ip, context in ip_context_map.items():
        if isinstance(context.state, RecordFailedState):
            print(f"{ip}, {context.state.last_fail_datetime.isoformat()},,,")
        elif isinstance(context.state, RecordFailRecoveredState):
            print(
                f"{ip}, {context.state.last_fail_datetime.isoformat()}, {context.state.fail_recovery_datetime.isoformat()},,"
            )
        elif isinstance(context.state, RecordOverloadState):
            print(
                f"{ip},,, {context.state.last_overload_datetime.isoformat()},"
            )
        elif isinstance(context.state, RecordOverloadRecorveredState):
            print(
                f"{ip},,, {context.state.last_overload_datetime.isoformat()}, {context.state.overload_recovery_datetime.isoformat()}"
            )
