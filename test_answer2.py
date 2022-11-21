from util import read_log
from answer2 import (
    detect_failure_duration,
    print_failure_duration,
    ServerContext,
    RecordHealthyState,
    RecordFailedState,
    RecordRecoveredState,
)
from contextlib import redirect_stdout
from datetime import datetime
from ipaddress import IPv4Interface
from io import StringIO
from unittest import TestCase


class Answer2Test(TestCase):
    def test_detect_failure_duration(self):
        with open("samplelog2.csv") as f:
            log = list(read_log(f))
        CONSECUTIVE_TIMEOUT_THRESHOLD = 3
        result = detect_failure_duration(
            log, consecutive_timeout_threshold=CONSECUTIVE_TIMEOUT_THRESHOLD
        )
        self.maxDiff = None
        self.assertEqual(
            result,
            {
                IPv4Interface("10.20.30.1/16"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    RecordRecoveredState(
                        last_fail_datetime=datetime(2020, 10, 19, 13, 32, 24),
                        recovery_datetime=datetime(2020, 10, 19, 13, 35, 24),
                    ),
                ),
                IPv4Interface("10.20.30.2/16"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    RecordHealthyState(
                        last_timeout_datetime_chain=[datetime(2020, 10, 19, 13, 35, 25)]
                    ),
                ),
                IPv4Interface("192.168.1.1/24"): ServerContext(
                    CONSECUTIVE_TIMEOUT_THRESHOLD,
                    RecordFailedState(
                        last_fail_datetime=datetime(2020, 10, 19, 13, 33, 34)
                    ),
                ),
            },
        )

    def test_print_failure_duration(self):
        with open("samplelog2.csv") as f:
            log = list(read_log(f))
        with redirect_stdout(StringIO()) as f:
            print_failure_duration(log, 3)
            captured_stdout = f.getvalue()
        self.assertEqual(
            captured_stdout,
            "10.20.30.1/16, 2020-10-19T13:32:24, 2020-10-19T13:35:24\n192.168.1.1/24, 2020-10-19T13:33:34,\n",
        )
