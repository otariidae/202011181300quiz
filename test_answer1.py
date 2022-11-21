from util import read_log
from answer1 import (
    detect_failure_duration,
    print_failure_duration,
    ServerContext,
    RecordHealthyState,
    RecordFailedState,
    RecordRecoveredState,
)
from contextlib import redirect_stdout
from datetime import datetime
from ipaddress import ip_interface
from io import StringIO
from unittest import TestCase


class Answer2Test(TestCase):
    def test_detect_failure_duration(self):
        with open("samplelog1.csv") as f:
            log = list(read_log(f))
        result = detect_failure_duration(log)
        self.assertEqual(
            result,
            {
                ip_interface("10.20.30.1/16"): ServerContext(
                    RecordRecoveredState(
                        last_fail_datetime=datetime(2020, 10, 19, 13, 32, 24),
                        recovery_datetime=datetime(2020, 10, 19, 13, 33, 24),
                    )
                ),
                ip_interface("10.20.30.2/16"): ServerContext(RecordHealthyState()),
                ip_interface("192.168.1.1/24"): ServerContext(
                    RecordFailedState(
                        last_fail_datetime=datetime(2020, 10, 19, 13, 33, 34)
                    )
                ),
            },
        )

    def test_print_failure_duration(self):
        with open("samplelog1.csv") as f:
            log = list(read_log(f))
        with redirect_stdout(StringIO()) as f:
            print_failure_duration(log)
            captured_stdout = f.getvalue()
        self.assertEqual(
            captured_stdout,
            "10.20.30.1/16, 2020-10-19T13:32:24, 2020-10-19T13:33:24\n192.168.1.1/24, 2020-10-19T13:33:34,\n",
        )
