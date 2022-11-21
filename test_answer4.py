from util import read_log
from answer4 import (
    detect_failure_or_overload_duration,
    print_failure_or_overload_duration,
    RecordHealthyState,
    RecordFailedState,
    RecordFailRecoveredState,
    RecordOverloadState,
    RecordOverloadRecorveredState,
    NetworkHealthyState,
    NetworkFailedState,
    NetworkFailRecorveredState,
)
from contextlib import redirect_stdout
from datetime import datetime
from ipaddress import IPv4Interface, IPv4Network
from io import StringIO
from unittest import TestCase


# class Answer4Test(TestCase):
#     def test_detect_failure_duration(self):
#         with open("samplelog4.csv") as f:
#             log = list(read_log(f))
#         CONSECUTIVE_TIMEOUT_THRESHOLD = 3
#         CONSECUTIVE_OVERLOAD_THRESHOLD = 3
#         OVERLOAD_TIMEOUT_THRESHOLD = 200
#         ip_state_map, network_state_map = detect_failure_or_overload_duration(
#             log,
#             consecutive_timeout_threshold=CONSECUTIVE_TIMEOUT_THRESHOLD,
#             consecutive_overload_threshold=CONSECUTIVE_OVERLOAD_THRESHOLD,
#             overload_timeout_threshold=OVERLOAD_TIMEOUT_THRESHOLD,
#         )
#         self.maxDiff = None
#         self.assertEqual(
#             ip_state_map,
#             {
#                 IPv4Interface("10.20.30.1/16"): RecordFailRecoveredState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 32, 24),
#                     fail_recovery_datetime=datetime(2020, 10, 19, 13, 35, 24),
#                 ),
#                 IPv4Interface("10.20.30.2/16"): RecordFailRecoveredState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 32, 25),
#                     fail_recovery_datetime=datetime(2020, 10, 19, 13, 35, 25),
#                 ),
#                 IPv4Interface("192.168.1.1/24"): RecordFailedState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 33, 34)
#                 ),
#                 IPv4Interface("192.168.1.2/24"): RecordOverloadRecorveredState(
#                     last_overload_datetime=datetime(2020, 10, 19, 13, 32, 35),
#                     overload_recovery_datetime=datetime(2020, 10, 19, 13, 35, 35),
#                 ),
#                 IPv4Interface("192.168.1.3/24"): RecordOverloadState(
#                     last_overload_datetime=datetime(2020, 10, 19, 13, 33, 36),
#                 ),
#                 IPv4Interface("192.168.10.1/24"): RecordFailedState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 33, 44),
#                 ),
#                 IPv4Interface("192.168.10.2/24"): RecordFailedState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 33, 45),
#                 )
#             },
#         )
#         self.assertEqual(
#             network_state_map,
#             {
#                 IPv4Network("10.20.0.0/16"): NetworkFailRecorveredState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 32, 24),
#                     fail_recovered_datetime=datetime(2020, 10, 19, 13, 35, 24),
#                 ),
#                 IPv4Network("192.168.1.0/24"): NetworkHealthyState(),
#                 IPv4Network("192.168.10.0/24"): NetworkFailedState(
#                     last_fail_datetime=datetime(2020, 10, 19, 13, 33, 45),
#                 ),
#             },
#         )


#     def test_print_failure_duration(self):
#         with open("samplelog4.csv") as f:
#             log = list(read_log(f))
#         with redirect_stdout(StringIO()) as f:
#             print_failure_or_overload_duration(log, 3, 3, 200)
#             captured_stdout = f.getvalue()
#         self.assertEqual(
#             captured_stdout,
#             """10.20.30.1/16, 2020-10-19T13:32:24, 2020-10-19T13:35:24
# 10.20.30.2/16, 2020-10-19T13:32:25, 2020-10-19T13:35:25
# 192.168.1.1/24, 2020-10-19T13:33:34,
# 192.168.10.1/24, 2020-10-19T13:33:44,
# 192.168.10.2/24, 2020-10-19T13:33:45,\n""",
#         )
