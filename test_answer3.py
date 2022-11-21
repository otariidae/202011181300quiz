from util import read_log
from answer3 import (
    detect_failure_or_overload_duration,
    print_failure_or_overload_duration,
    ServerContext,
    RecordHealthyState,
    RecordFailedState,
    RecordFailRecoveredState,
    RecordOverloadState,
    RecordOverloadRecorveredState,
)
from contextlib import redirect_stdout
from datetime import datetime
from ipaddress import IPv4Interface
from io import StringIO
from unittest import TestCase


class Answer3Test(TestCase):
    def test_detect_failure_duration(self):
        with open("samplelog3.csv") as f:
            log = list(read_log(f))
        CONSECUTIVE_TIMEOUT_THRESHOLD = 3
        CONSECUTIVE_OVERLOAD_THRESHOLD = 3
        OVERLOAD_TIMEOUT_THRESHOLD = 200
        result = detect_failure_or_overload_duration(
            log,
            consecutive_timeout_threshold=CONSECUTIVE_TIMEOUT_THRESHOLD,
            consecutive_overload_threshold=CONSECUTIVE_OVERLOAD_THRESHOLD,
            overload_timeout_threshold=OVERLOAD_TIMEOUT_THRESHOLD,
        )
        self.maxDiff = None
        self.assertEqual(
            result,
            {
                IPv4Interface("10.20.30.1/16"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    OVERLOAD_TIMEOUT_THRESHOLD,
                    CONSECUTIVE_OVERLOAD_THRESHOLD,
                    RecordFailRecoveredState(
                        last_fail_datetime=datetime(2020, 10, 19, 13, 32, 24),
                        fail_recovery_datetime=datetime(2020, 10, 19, 13, 35, 24),
                    ),
                ),
                IPv4Interface("10.20.30.2/16"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    OVERLOAD_TIMEOUT_THRESHOLD,
                    CONSECUTIVE_OVERLOAD_THRESHOLD,
                    RecordHealthyState(
                        last_timeout_datetime_chain=[datetime(2020, 10, 19, 13, 35, 25)]
                    ),
                ),
                IPv4Interface("192.168.1.1/24"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    OVERLOAD_TIMEOUT_THRESHOLD,
                    CONSECUTIVE_OVERLOAD_THRESHOLD,
                    RecordFailedState(
                        last_fail_datetime=datetime(2020, 10, 19, 13, 33, 34)
                    ),
                ),
                IPv4Interface("192.168.1.2/24"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    OVERLOAD_TIMEOUT_THRESHOLD,
                    CONSECUTIVE_OVERLOAD_THRESHOLD,
                    RecordOverloadRecorveredState(
                        last_overload_datetime=datetime(2020, 10, 19, 13, 32, 35),
                        overload_recovery_datetime=datetime(2020, 10, 19, 13, 35, 35),
                    ),
                ),
                IPv4Interface("192.168.1.3/24"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    OVERLOAD_TIMEOUT_THRESHOLD,
                    CONSECUTIVE_OVERLOAD_THRESHOLD,
                    RecordOverloadState(
                        last_overload_datetime=datetime(2020, 10, 19, 13, 33, 36),
                    ),
                ),
            },
        )

    def test_print_failure_duration(self):
        with open("samplelog3.csv") as f:
            log = list(read_log(f))
        with redirect_stdout(StringIO()) as f:
            print_failure_or_overload_duration(log, consecutive_timeout_threshold=3, overload_timeout_threshold=200, consecutive_overload_threshold=3)
            captured_stdout = f.getvalue()
        self.maxDiff = None
        self.assertEqual(
            captured_stdout,
            "10.20.30.1/16, 2020-10-19T13:32:24, 2020-10-19T13:35:24,,\n192.168.1.1/24, 2020-10-19T13:33:34,,,\n192.168.1.2/24,,, 2020-10-19T13:32:35, 2020-10-19T13:35:35\n192.168.1.3/24,,, 2020-10-19T13:33:36,\n",
        )
