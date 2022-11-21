from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from dataclasses import dataclass, field
from ipaddress import IPv4Interface, IPv4Network
from util import LogRecord


class RecordAbstractState(ABC):
    consecutive_timeout_threshold: int
    overload_timeout_threshold: int
    consecutive_overload_threshold: int
    _context: RecordFailureContext

    @abstractmethod
    def push_newer_record(self, record: LogRecord):
        ...


@dataclass(kw_only=True)
class RecordHealthyState(RecordAbstractState):
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
    last_fail_datetime: datetime
    fail_recovery_datetime: datetime


@dataclass(kw_only=True)
class RecordOverloadState(RecordAbstractState):
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
    last_overload_datetime: datetime
    overload_recovery_datetime: datetime


@dataclass
class RecordFailureContext:
    _consecutive_timeout_threshold: int
    _overload_timeout_threshold: int
    _consecutive_overload_threshold: int
    _state: RecordAbstractState = field(default_factory=RecordHealthyState)

    def __post_init__(self):
        self._state._context = self
        self._state.consecutive_timeout_threshold = self._consecutive_timeout_threshold
        self._state.overload_timeout_threshold = self._overload_timeout_threshold
        self._state.consecutive_overload_threshold = (
            self._consecutive_overload_threshold
        )

    def push_newer_record(self, record: LogRecord):
        self._state.push_newer_record(record)

    def transition_to(self, state: RecordAbstractState):
        self._state = state
        self._state._context = self
        self._state.consecutive_timeout_threshold = self._consecutive_timeout_threshold
        self._state.overload_timeout_threshold = self._overload_timeout_threshold
        self._state.consecutive_overload_threshold = (
            self._consecutive_overload_threshold
        )

    @property
    def state(self):
        return self._state


class NetworkAbstractState(ABC):
    consecutive_timeout_threshold: int
    _context: NetworkFailureContext

    @abstractmethod
    def push_newer_network_contexts(self, *contexts: RecordFailureContext):
        ...

    @abstractmethod
    def push_newer_record_contexts(
        self, ip: IPv4Interface, context: RecordFailureContext
    ):
        ...


@dataclass(kw_only=True)
class NetworkHealthyState(NetworkAbstractState):
    last_timeout_ip_datetime_chain: dict[IPv4Interface, list[datetime]] = field(
        default_factory=dict
    )

    def push_newer_network_contexts(self, *contexts):
        most_recent_fail_datetime = datetime.min
        for context in contexts:
            if not isinstance(context.state, RecordFailedState):
                return
            if context.state.last_fail_datetime > most_recent_fail_datetime:
                most_recent_fail_datetime = context.state.last_fail_datetime
        self._context.transition_to(
            NetworkFailedState(last_fail_datetime=most_recent_fail_datetime)
        )


@dataclass(kw_only=True)
class NetworkFailedState(NetworkAbstractState):
    last_fail_datetime: datetime

    def push_newer_network_contexts(self, *contexts):
        for context in contexts:
            if isinstance(context.state, RecordFailRecoveredState):
                self._context.transition_to(
                    NetworkFailRecorveredState(
                        last_fail_datetime=self.last_fail_datetime,
                        fail_recovered_datetime=context.state.fail_recovery_datetime,
                    )
                )
                break


@dataclass(kw_only=True)
class NetworkFailRecorveredState(NetworkHealthyState):
    last_fail_datetime: datetime
    fail_recovered_datetime: datetime


@dataclass
class NetworkFailureContext:
    _state: NetworkAbstractState = field(default_factory=NetworkHealthyState)

    def __post_init__(self):
        self._state._context = self

    def push_newer_network_contexts(self, *contexts):
        self._state.push_newer_network_contexts(*contexts)

    def push_newer_record_context(self, context: RecordFailureContext):
        self._state.push_newer_record_context(context)

    def transition_to(self, state: NetworkAbstractState):
        self._state = state
        self._state._context = self

    @property
    def state(self):
        return self._state


def group_by_ip_network(ip_interfaces: Iterable[IPv4Interface]):
    network_interface_map: dict[IPv4Network, set[IPv4Interface]] = {}
    for ip_interface in ip_interfaces:
        network = ip_interface.network
        interfaces = network_interface_map.setdefault(network, set())
        interfaces.add(ip_interface)
    return network_interface_map


def calc_failure_or_overload(
    log: Iterable[LogRecord],
    consecutive_timeout_threshold: int,
    overload_timeout_threshold: int,
    consecutive_overload_threshold: int,
):
    ip_context_map: dict[IPv4Interface, RecordFailureContext] = {}
    network_context_map: dict[IPv4Network, NetworkFailureContext] = {}
    for record in log:
        record_failure_context = ip_context_map.setdefault(
            record.ipv4interface,
            RecordFailureContext(
                consecutive_timeout_threshold,
                overload_timeout_threshold,
                consecutive_overload_threshold,
            ),
        )
        record_failure_context.push_newer_record(record)
        network_failure_context = network_context_map.setdefault(
            record.ipv4interface.network, NetworkFailureContext()
        )
        network_context_map.push_newer_record_context(record_failure_context)
    return ip_context_map


def calc_network_failure_from_record_failure_context(
    interface_context_map: dict[IPv4Interface, RecordFailureContext]
):
    network_context_map: dict[IPv4Network, NetworkFailureContext] = {}
    ip_interfaces = interface_context_map.keys()
    network_interface_map = group_by_ip_network(ip_interfaces)
    for network, interfaces in network_interface_map.items():
        network_interface_contexts: list[RecordFailureContext] = []
        print(network)
        for interface in interfaces:
            context = interface_context_map[interface]
            network_interface_contexts.append(context)
            print(context.state)
        network_failure_context = network_context_map.setdefault(
            network, NetworkFailureContext()
        )
        network_failure_context.push_newer_network_contexts(*network_interface_contexts)
    return network_context_map


def detect_failure_or_overload_duration(
    log: Iterable[LogRecord],
    consecutive_timeout_threshold: int,
    overload_timeout_threshold: int,
    consecutive_overload_threshold: int,
):
    interface_context_map = calc_failure_or_overload(
        log,
        consecutive_timeout_threshold,
        overload_timeout_threshold,
        consecutive_overload_threshold,
    )
    network_context_map = calc_network_failure_from_record_failure_context(
        interface_context_map
    )
    ip_state_map: dict[IPv4Interface, RecordAbstractState] = {}
    for ip, context in interface_context_map.items():
        ip_state_map[ip] = context.state
    network_state_map: dict[IPv4Network, NetworkAbstractState] = {}
    for network, context in network_context_map.items():
        network_state_map[network] = context.state
    return ip_state_map, network_state_map


def print_failure_or_overload_duration(
    log: Iterable[LogRecord],
    consecutive_timeout_threshold: int,
    overload_timeout_threshold: int,
    consecutive_overload_threshold: int,
):
    ip_state_map, network_state_map = detect_failure_or_overload_duration(
        log,
        consecutive_timeout_threshold,
        overload_timeout_threshold,
        consecutive_overload_threshold,
    )
    for ip, state in ip_state_map.items():
        if isinstance(state, RecordFailedState):
            print(f"{ip}, {state.last_fail_datetime.isoformat()},")
        elif isinstance(state, RecordFailRecoveredState):
            print(
                f"{ip}, {state.last_fail_datetime.isoformat()}, {state.fail_recovery_datetime.isoformat()}"
            )
