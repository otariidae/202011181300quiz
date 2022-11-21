from util import read_log
from answer1 import print_failure_duration
from io import StringIO

file = StringIO(
    "20201019133124,10.20.30.1/16,2\n20201019133224,10.20.30.1/16,522\n20201019133324,10.20.30.1/16,-"
)
log = read_log(file)
print_failure_duration(log)
"""
10.20.30.1/16, 2020-10-19T13:33:24,
"""
