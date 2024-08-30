import time
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass()
class TimeUsage:
    start: float
    end: float
    process: float
    total: float


@contextmanager
def time_usage():
    usage = TimeUsage(start=time.time(), end=0, process=0, total=0)
    perf_time_start = time.perf_counter_ns()
    process_start = time.process_time_ns()
    yield usage
    process_end = time.process_time_ns()
    perf_time_end = time.perf_counter_ns()
    usage.end = time.time()
    usage.process = round((process_end - process_start) / 1e6, 3)
    usage.total = round((perf_time_end - perf_time_start) / 1e6, 3)
