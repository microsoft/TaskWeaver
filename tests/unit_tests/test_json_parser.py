import json
from typing import Any, List

import pytest

from taskweaver.utils import json_parser

obj_cases: List[Any] = [
    ["hello", "world"],
    "any_str",
    {
        "test_key": {
            "str_array": ["hello", "world", "test"],
            "another_key": {},
            "empty_array": [[[]], []],
        },
    },
    [True, False, None],
    [1, 2, 3],
    123.345,
    {"val": 123.345},
    [
        {
            "a": {},
            "b": {},
            "c": {},
            "d": {},
            "e": {},
        },
    ],
    {
        "test_key": {
            "str_array": ["hello", "world", "test"],
            "test another key": [
                "hello",
                "world",
                1,
                2.0,
                True,
                False,
                None,
                {
                    "test yet another key": "test value",
                    "test yet  key 2": '\r\n\u1234\ffdfd\tfdfv\b"',
                },
            ],
            True: False,
        },
    },
]


@pytest.mark.parametrize("obj", obj_cases)
def test_json_parser(obj: Any):
    dumped_str = json.dumps(obj)
    obj = json_parser.parse_json(json.dumps(obj))
    dumped_str2 = json.dumps(obj)
    assert dumped_str == dumped_str2


str_cases: List[str] = [
    '   { "a": [ true, false, null ] }  ',
    "  \r  \n \t  [  \r \n \t true, false, null \r \n \t ]  \r \n \t  ",
    ' \r \n \t "hello world" \r \n \t ',
]


@pytest.mark.parametrize("str_case", str_cases)
def test_json_parser_str(str_case: str):
    obj = json.loads(str_case)
    dumped_str = json.dumps(obj)
    obj = json_parser.parse_json(str_case)
    dumped_str2 = json.dumps(obj)
    assert dumped_str == dumped_str2
