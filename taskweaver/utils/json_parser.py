import itertools
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
]


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


def reduce_events(events: Iterable[ParserEvent], skip_ws: bool = True) -> Iterable[ParserEvent]:
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


def parse_json_stream(token_stream: Iterable[str], skip_ws: bool = False) -> Iterable[ParserEvent]:
    buf: str = ""
    is_end: bool = False
    prefix_stack: List[str] = []
    state_stack: List[Tuple[ParserStateType, Any]] = [("root", (False, False))]
    ev_queue: List[ParserEvent] = []

    def add_event(ev: ParserEventType, value: Any, value_str: str, is_end: bool):
        ev_queue.append(
            ParserEvent(
                "".join(prefix_stack),
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
            raise Exception(f"invalid value after value of key {key}: {ch}")
        if value_to_begin:
            state_stack[-1] = ("object_value", (key, False, True))
            if parse_value_begin(ch):
                return True
            raise Exception(f"invalid value for key {key}: {ch}")
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
            prefix_stack.append(f"[{idx}]")
            if parse_value_begin(ch):
                return True
            raise Exception(f"invalid value for index {idx}: {ch}")
        return False

    def parse_str_value(ch: str, cur_state_ext: Tuple[bool, str, str, bool]) -> bool:
        in_escape, escape_buf, value_buf, is_obj_key = cur_state_ext
        ev: ParserEventType = "map_key" if is_obj_key else "string"
        if in_escape and escape_buf.startswith("u"):
            if ch in "0123456789abcdefABCDEF":
                escape_buf += ch
            else:
                raise Exception(f"invalid unicode escape sequence: \\{escape_buf}{ch}")
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
                raise Exception(f"invalid escape sequence: \\{ch}")
            value_buf += new_ch
            add_event(ev, None, new_ch, False)
            state_stack[-1] = ("string", (False, "", value_buf, is_obj_key))
            return True
        if ch == '"':
            add_event(ev, value_buf, "", True)
            state_stack.pop()
            if is_obj_key:
                prefix_stack.append(value_buf)
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
        raise Exception(f"invalid literal in parsing when expecting {literal}: {buf}")

    def parse_number(ch: str, cur_state_ext: Tuple[str, bool, bool, bool]):
        buf, in_exp, in_frac, in_exp_sign = cur_state_ext
        if ch.isdigit() or ch == "." or ch == "e" or ch == "E" or ch == "+" or ch == "-":
            buf += ch
            add_event("number", None, ch, False)
            state_stack[-1] = ("number", (buf, in_exp, in_frac, in_exp_sign))
            return True
        num_val = float(buf)
        add_event("number", num_val, "", True)
        state_stack.pop()
        return False

    def parse_root(ch: str, cur_state_ext: Tuple[bool, bool]):
        has_root_elem, is_end = cur_state_ext
        if parse_ws(ch):
            return True
        if ch == "":
            state_stack[-1] = ("root", (has_root_elem, True))
            return True
        if has_root_elem:
            raise Exception(f"invalid token after root element: {ch}")
        state_stack[-1] = ("root", (True, is_end))
        return parse_value_begin(ch)

    def process_ev_queue():
        result = ev_queue.copy()
        result = reduce_events(result, skip_ws=skip_ws)
        ev_queue.clear()
        return result

    for chunk in itertools.chain(token_stream, [None]):
        if chunk is None:
            is_end = True
        else:
            buf += chunk
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
                raise Exception(f"not implemented handling for {cur_state}: {ch}")
            if not r and not is_end:
                raise Exception(
                    f"failed to parse {cur_state}: {ch} \n State: {state_stack} Prefix: {prefix_stack}",
                )
            if is_end:
                break
        yield from process_ev_queue()
