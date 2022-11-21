## 達成状況

- 設問1, 2：できたと思う
- 設問3：できたと思ったら問題文読み間違い時間切れ
  - 「平均」を読み落として「直近m回の応答時間がtミリ秒を超えた場合」として実装
- 設問4：テストだけ書いてできず時間切れ

## 動作環境

- Python 3.11


## テスト

```console
$ python -m unittest
```

## 使用例

公開用関数

- 設問1: answer1.py: `detect_failure_duration`, `print_failure_duration`
- 設問2: answer2.py: `detect_failure_duration`, `print_failure_duration`
- 設問3: answer3.py: `detect_failure_or_overload_duration`, `print_failure_or_overload_duration`

```python
from util import read_log
from answer1 import detect_failure_duration, ServerContext, RecordFailedState
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
```

```python
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
```

※詳細は各ファイルのdocstringを参照
