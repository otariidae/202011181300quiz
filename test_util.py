from util import (
    read_log,
    LogRecord,
)
from datetime import datetime
from ipaddress import ip_interface
from unittest import TestCase


class UtilTest(TestCase):
    def test_read_log(self):
        with open("samplelog.csv") as f:
            log = list(read_log(f))
        self.assertEqual(
            log,
            [
                LogRecord(
                    datetime(2020, 10, 19, 13, 31, 24), ip_interface("10.20.30.1/16"), 2
                ),
                LogRecord(
                    datetime(2020, 10, 19, 13, 31, 35),
                    ip_interface("192.168.1.2/24"),
                    5,
                ),
                LogRecord(
                    datetime(2020, 10, 19, 13, 32, 24),
                    ip_interface("10.20.30.1/16"),
                    522,
                ),
                LogRecord(
                    datetime(2020, 10, 19, 13, 32, 35),
                    ip_interface("192.168.1.2/24"),
                    15,
                ),
                LogRecord(
                    datetime(2020, 10, 19, 13, 33, 24),
                    ip_interface("10.20.30.1/16"),
                    None,
                ),
            ],
        )
