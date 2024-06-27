import copy
import itertools
import types
from typing import Any, Iterable, List, Literal, NamedTuple, Optional, Tuple

ParserEventType = Literal[
    "start_map",
    "end_map",
    "start_array",
    "end_array",
    "map_key",
    "null",
    "boolean",
    # use number for both integer and double
    # "integer",
    # "double",
    "number",
    "string",
    "ws",
    "skip",
]


class StreamJsonParserError(Exception):
    pass


class ParserEvent(NamedTuple):
    prefix: str
    event: ParserEventType
    value: Any
    value_str: str
    is_end: bool


ParserStateType = Literal[
    "root",
    "object",
    "object_value",
    "array",
    "number",
    "string",
    "literal",
    "ws",
]


def reduce_events(
    events: Iterable[ParserEvent],
    skip_ws: bool = True,
) -> Iterable[ParserEvent]:
    reduced: List[ParserEvent] = []
    cur: Optional[ParserEvent] = None
    for ev in events:
        if skip_ws and ev.event == "ws":
            continue
        if cur is None:
            cur = ev
            continue
        if ev.event == cur.event:
            cur = ParserEvent(
                ev.prefix,
                cur.event,
                ev.value,
                cur.value_str + ev.value_str,
                ev.is_end,
            )
        else:
            reduced.append(cur)
            cur = ev
    if cur is not None:
        reduced.append(cur)
    return reduced


def is_ws(ch: str):
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r"


def parse_json_stream(
    token_stream: Iterable[str],
    skip_ws: bool = False,
    ijson_prefix: bool = False,
    skip_after_root: bool = False,
    include_all_values: bool = False,
) -> Iterable[ParserEvent]:
    buf: str = ""
    is_end: bool = False
    prefix_stack: List[Tuple[bool, str]] = []
    state_stack: List[Tuple[ParserStateType, Any]] = [("root", (False, False))]
    ev_queue: List[ParserEvent] = []

    root_array: List[Any] = []
    obj_stack: List[Tuple[Literal["object", "array", "key"], Any]] = [
        ("array", root_array),
    ]

    def add_value(val: Any):
        cur_obj_t, cur_obj_v = obj_stack[-1]
        if cur_obj_t == "array":
            assert type(cur_obj_v) is list
            cur_obj_v.append(val)  # type: ignore
        elif cur_obj_t == "key":
            obj_stack.pop()
            assert obj_stack[-1][0] == "object", f"unexpected stack state when adding key {obj_stack}"
            obj_stack[-1][1][cur_obj_v] = val
        else:
            assert False, "object value need to have key"

    def add_event(ev: ParserEventType, value: Any, value_str: str, is_end: bool):
        if ijson_prefix:
            prefix = ".".join("item" if is_arr else val for is_arr, val in prefix_stack)
        else:
            prefix = "".join(f"[{val}]" if is_arr else f".{val}" for is_arr, val in prefix_stack)
        ev_queue.append(
            ParserEvent(
                prefix,
                ev,
                value,
                value_str,
                is_end,
            ),
        )

    def parse_ws(ch: str) -> bool:
        is_in_ws = state_stack[-1][0] == "ws" if len(state_stack) > 0 else False

        if not is_ws(ch):
            if is_in_ws:
                add_event("ws", None, "", True)
                state_stack.pop()
            return False
        if not is_in_ws:
            state_stack.append(("ws", None))
        add_event("ws", None, ch, False)
        return True

    def parse_str_begin(ch: str, is_obj_key: bool = False) -> bool:
        if ch == '"':
            add_event("map_key" if is_obj_key else "string", "", "", False)
            state_stack.append(("string", (False, "", "", is_obj_key)))
            return True
        return False

    def parse_value_begin(ch: str) -> bool:
        if parse_ws(ch) or parse_str_begin(ch):
            return True
        if ch == "{":
            add_event("start_map", None, ch, True)
            state_stack.append(("object", None))
            return True
        if ch == "[":
            add_event("start_array", None, ch, True)
            state_stack.append(("array", (0, False, False)))
            return True
        if ch in ["t", "f", "n"]:
            literal_state: Tuple[str, ParserEventType, str, Any]
            if ch == "t":
                literal_state = (ch, "boolean", "true", True)
            elif ch == "f":
                literal_state = (ch, "boolean", "false", False)
            else:
                literal_state = (ch, "null", "null", None)
            add_event(literal_state[1], None, ch, False)
            state_stack.append(("literal", literal_state))
            return True
        if ch == "-" or ch.isdigit():
            add_event("number", ch, ch, False)
            state_stack.append(("number", (ch, False, False, False)))
            return True
        return False

    def parse_obj_begin(ch: str) -> bool:
        if ch == "}":
            add_event("end_map", None, ch, True)
            state_stack.pop()
            return True
        if parse_ws(ch):
            return True
        if parse_str_begin(ch, True):
            return True
        return False

    def parse_obj_value(ch: str, cur_state_ext: Tuple[str, bool, bool]) -> bool:
        key, value_to_begin, value_to_end = cur_state_ext
        if parse_ws(ch):
            return True
        if value_to_end:
            prefix_stack.pop()
            state_stack.pop()
            if ch == ",":
                return True
            if ch == "}":
                add_event("end_map", None, ch, True)
                state_stack.pop()  # pop the object begin state
                return True
            raise StreamJsonParserError(f"invalid value after value of key {key}: {ch}")
        if value_to_begin:
            state_stack[-1] = ("object_value", (key, False, True))
            if parse_value_begin(ch):
                return True
            raise StreamJsonParserError(f"invalid value for key {key}: {ch}")
        if ch == ":":
            state_stack[-1] = ("object_value", (key, True, False))
            return True
        return False

    def parse_array_begin(ch: str, cur_state_ext: Tuple[int, bool, bool]) -> bool:
        idx, value_begins, require_value = cur_state_ext
        if parse_ws(ch):
            return True
        if value_begins:
            prefix_stack.pop()
            if ch == ",":
                state_stack[-1] = ("array", (idx + 1, False, True))
                return True
            if ch == "]":
                add_event("end_array", None, ch, True)
                state_stack.pop()
                return True
        else:
            if not require_value and ch == "]":
                add_event("end_array", None, ch, True)
                state_stack.pop()
                return True
            state_stack[-1] = ("array", (idx, True, False))
            prefix_stack.append((True, str(idx)))
            if parse_value_begin(ch):
                return True
            raise StreamJsonParserError(f"invalid value for index {idx}: {ch}")
        return False

    def parse_str_value(ch: str, cur_state_ext: Tuple[bool, str, str, bool]) -> bool:
        in_escape, escape_buf, value_buf, is_obj_key = cur_state_ext
        ev: ParserEventType = "map_key" if is_obj_key else "string"
        if in_escape and escape_buf.startswith("u"):
            if ch in "0123456789abcdefABCDEF":
                escape_buf += ch
            else:
                raise StreamJsonParserError(f"invalid unicode escape sequence: \\{escape_buf}{ch}")
            if len(escape_buf) == 5:
                new_ch = chr(int(escape_buf[1:], 16))
                value_buf += new_ch
                add_event(ev, None, new_ch, False)
                state_stack[-1] = ("string", (False, "", value_buf, is_obj_key))
            else:
                state_stack[-1] = ("string", (True, escape_buf, value_buf, is_obj_key))
            return True
        if in_escape:
            assert escape_buf == ""
            if ch == "u":
                state_stack[-1] = ("string", (True, ch, value_buf, is_obj_key))
                return True
            new_ch = ""
            if ch == "n":
                new_ch = "\n"
            elif ch == "/":
                new_ch = "/"
            elif ch == "\\":
                new_ch = "\\"
            elif ch == "r":
                new_ch = "\r"
            elif ch == "r":
                new_ch = "\r"
            elif ch == "t":
                new_ch = "\t"
            elif ch == "b":
                new_ch = "\b"
            elif ch == "f":
                new_ch = "\f"
            elif ch == '"':
                new_ch = '"'
            else:
                raise StreamJsonParserError(f"invalid escape sequence: \\{ch}")
            value_buf += new_ch
            add_event(ev, None, new_ch, False)
            state_stack[-1] = ("string", (False, "", value_buf, is_obj_key))
            return True
        if ch == '"':
            add_event(ev, value_buf, "", True)
            state_stack.pop()
            if is_obj_key:
                prefix_stack.append((False, value_buf))
                state_stack.append(("object_value", (value_buf, False, False)))
            return True
        if ch == "\\":
            state_stack[-1] = ("string", (True, "", value_buf, is_obj_key))
            return True
        value_buf += ch
        add_event(ev, None, ch, False)
        state_stack[-1] = ("string", (False, "", value_buf, is_obj_key))
        return True

    def parse_literal_value(
        ch: str,
        cur_state_ext: Tuple[str, ParserEventType, str, Any],
    ) -> bool:
        buf, ev, literal, value = cur_state_ext
        buf += ch
        if buf == literal:
            add_event(ev, value, buf, True)
            state_stack.pop()
            return True
        if literal.startswith(buf):
            add_event(ev, None, ch, False)
            state_stack[-1] = ("literal", (buf, ev, literal, value))
            return True
        raise StreamJsonParserError(f"invalid literal in parsing when expecting {literal}: {buf}")

    def parse_number(ch: str, cur_state_ext: Tuple[str, bool, bool, bool]):
        # TODO: support rigir
        buf, in_exp, in_frac, in_exp_sign = cur_state_ext
        if ch.isdigit() or ch == "." or ch == "e" or ch == "E" or ch == "+" or ch == "-":
            buf += ch
            add_event("number", None, ch, False)
            state_stack[-1] = ("number", (buf, in_exp, in_frac, in_exp_sign))
            return True
        is_float_mode = "." in buf or "e" in buf or "E" in buf
        try:
            num_val = float(buf) if is_float_mode else int(buf)
        except ValueError:
            raise StreamJsonParserError(f"invalid number literal {buf}")
        add_event("number", num_val, "", True)
        state_stack.pop()
        return False

    def parse_root(ch: str, cur_state_ext: Tuple[bool, bool]):
        has_root_elem, has_skip_cnt = cur_state_ext

        if has_skip_cnt and skip_after_root:
            add_event("skip", None, ch, ch == "")
            return True

        if parse_ws(ch):
            return True
        if ch == "":
            return True
        if has_root_elem:
            if skip_after_root:
                # detected content after first root element, skip if configured
                state_stack[-1] = ("root", (True, True))
                add_event("skip", None, ch, False)
                return True
            raise StreamJsonParserError(f"invalid token after root element: {ch}")
        else:
            # first root element begins
            state_stack[-1] = ("root", (True, has_skip_cnt))
            return parse_value_begin(ch)

    def process_ev_queue() -> Iterable[ParserEvent]:
        result = ev_queue.copy()
        result = reduce_events(result, skip_ws=skip_ws)
        ev_queue.clear()
        if not include_all_values:
            for ev in result:
                yield ev
            return

        for ev in result:
            if not ev.is_end:
                yield ev
                continue
            evt = ev.event
            val = ev.value

            if evt == "start_map":
                obj_stack.append(("object", {}))
            elif evt == "start_array":
                obj_stack.append(("array", []))
            elif evt == "map_key":
                obj_stack.append(("key", val))
            elif evt == "ws" or evt == "skip":
                pass
            elif evt == "end_map" or evt == "end_array":
                obj_val = obj_stack.pop()[1]
                add_value(obj_val)
                yield ParserEvent(ev.prefix, evt, copy.deepcopy(obj_val), ev.value_str, ev.is_end)
                continue
            elif evt == "boolean" or evt == "null" or evt == "number" or evt == "string":
                add_value(val)
            else:
                assert f"unsupported parser event {evt}"

            yield ev

    def parse_buf():
        nonlocal buf, is_end
        while True:
            if len(buf) == 0 and not is_end:
                break
            cur_state, cur_state_ext = state_stack[-1]
            ch = "" if buf == "" else buf[0]
            buf = buf if buf == "" else buf[1:]
            r = False
            if cur_state == "root":
                r = parse_root(ch, cur_state_ext)
            elif cur_state == "object":
                r = parse_obj_begin(ch)
            elif cur_state == "string":
                assert cur_state_ext is not None
                r = parse_str_value(ch, cur_state_ext)
            elif cur_state == "object_value":
                assert cur_state_ext is not None
                r = parse_obj_value(ch, cur_state_ext)
            elif cur_state == "array":
                assert cur_state_ext is not None
                r = parse_array_begin(ch, cur_state_ext)
            elif cur_state == "literal":
                assert cur_state_ext is not None
                r = parse_literal_value(ch, cur_state_ext)
            elif cur_state == "number":
                assert cur_state_ext is not None
                r = parse_number(ch, cur_state_ext)
                if not r:
                    # number needs to peek next token to determine if it's finished
                    # restore token to buffer when finishes
                    buf = ch + buf
                    r = True
                    continue
            elif cur_state == "ws":
                r = parse_ws(ch)
                if not r:
                    # ws also need to peek next token to determine the end
                    # restore token to buffer when finishes
                    buf = ch + buf
                    r = True
                    continue
            else:
                raise StreamJsonParserError(f"not implemented handling for {cur_state}: {ch}")
            if not r and not is_end:
                raise StreamJsonParserError(
                    f"failed to parse {cur_state}: {ch} \n State: {state_stack} Prefix: {prefix_stack}",
                )
            if is_end:
                break

    try:
        for chunk in itertools.chain(token_stream, [None]):
            if chunk is None:
                is_end = True
            else:
                buf += chunk
            parse_buf()
            yield from process_ev_queue()

        # post parsing checks
        assert len(state_stack) > 0

        final_root_type, final_root_state = state_stack[0]
        assert final_root_type == "root"

        if not final_root_state[0]:
            raise StreamJsonParserError("empty string with no element found")

        if len(state_stack) > 1:
            raise StreamJsonParserError("incomplete JSON str ends prematurely")
    finally:
        if isinstance(token_stream, types.GeneratorType):
            try:
                token_stream.close()
            except GeneratorExit:
                print("generator already closed in parser")


def parse_json(token_stream: Iterable[str], skip_after_root: bool = False) -> Any:
    ev_queue: List[ParserEvent] = []
    for ev in parse_json_stream(
        token_stream,
        skip_after_root=skip_after_root,
        include_all_values=True,
    ):
        if (
            ev.prefix == ""
            and ev.is_end
            and ev.event
            in [
                # all value closing events
                "end_map",
                "end_array",
                "number",
                "string",
                "boolean",
                "null",
            ]
        ):
            ev_queue.append(ev)
    assert len(ev_queue) == 1
    return ev_queue[0].value
