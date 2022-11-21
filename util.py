from __future__ import annotations
from collections.abc import Iterable
from csv import DictReader
from datetime import datetime
from dataclasses import dataclass
from ipaddress import IPv4Interface
from typing import TextIO, TypedDict, Optional

TimeoutResponse = "-"


class PrimitiveLogDict(TypedDict):
    datetime: str
    ipv4interface: str
    response_ms: str


@dataclass
class LogRecord:
    """監視ログ1行分

    Attributes:
        datetime: 確認日時
        ipv4interface: サーバアドレス
        response_ms: 応答時間（ミリ秒）
    """

    datetime: datetime
    ipv4interface: IPv4Interface
    response_ms: Optional[int] = None

    @property
    def is_timed_out(self):
        return self.response_ms is None

    @staticmethod
    def from_primitive_dict(d: PrimitiveLogDict) -> LogRecord:
        dt = datetime.strptime(d["datetime"], "%Y%m%d%H%M%S")
        ipv4interface = IPv4Interface(d["ipv4interface"])
        if d["response_ms"] == TimeoutResponse:
            return LogRecord(datetime=dt, ipv4interface=ipv4interface)
        return LogRecord(
            datetime=dt, ipv4interface=ipv4interface, response_ms=int(d["response_ms"])
        )


def read_log(f: TextIO) -> Iterable[LogRecord]:
    """監視ログを読み込む

    Args:
        f: 監視ログ
    """
    reader = DictReader(f, fieldnames=["datetime", "ipv4interface", "response_ms"])
    for row in reader:
        yield LogRecord.from_primitive_dict(row)
