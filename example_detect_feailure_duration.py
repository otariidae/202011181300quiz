from util import read_log
from answer1 import (
    detect_failure_duration,
    print_failure_duration,
    ServerContext,
    RecordFailedState,
)
from datetime import datetime
from io import StringIO
from ipaddress import IPv4Interface

file = StringIO(
    "20201019133124,10.20.30.1/16,2\n20201019133224,10.20.30.1/16,522\n20201019133324,10.20.30.1/16,-"
)
log = read_log(file)
server_context_map = detect_failure_duration(log)

assert server_context_map == {
    IPv4Interface("10.20.30.1/16"): ServerContext(
        RecordFailedState(last_fail_datetime=datetime(2020, 10, 19, 13, 33, 24))
    )
}
