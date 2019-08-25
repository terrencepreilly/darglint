"""A utility for measuring performance characteristics for darglint.
"""

from collections import (
    defaultdict,
)
from datetime import (
    datetime,
)
import json
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)
from unittest import (
    TestCase,
)

from darglint.docstring.base import (
    BaseDocstring,
)
from darglint.docstring.docstring import (
    Docstring,
)
from darglint.driver import (
    print_version,
)
from statistics import (
    mean,
    stdev,
)


Golden = Dict[str, Any]


class Stats(object):

    STALE_AGE_MINS = 30

    def __init__(self, times, by_length, google, sphinx, timestamp=None):
        # type: (List[float], List[Tuple[int, float]], List[float], List[float], int) -> None  # noqa: E501
        self.times = times
        self.by_length = by_length
        self.google = google
        self.sphinx = sphinx

        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = int(time.time())

    def is_stale(self):
        # type: () -> bool
        current = int(time.time())
        delta = self.timestamp - current
        return (delta // 60) > self.STALE_AGE_MINS

    @staticmethod
    def decode(datum):
        # type: (Dict[str, Any]) -> Stats
        datum['by_length'] = [(x, y) for x, y in datum['by_length']]
        return Stats(**datum)

    def encode(self):
        return {
            'times': self.times,
            'by_length': [[x, y] for x, y in self.by_length],
            'google': self.google,
            'sphinx': self.sphinx,
            'timestamp': self.timestamp,
        }


class Performance(object):

    def parse_golden(self, golden):
        # type: (Golden) -> BaseDocstring
        if golden['type'] == 'GOOGLE':
            assert isinstance(golden['docstring'], str)
            docstring = Docstring.from_google(golden['docstring'])
        elif golden['type'] == 'SPHINX':
            assert isinstance(golden['docstring'], str)
            docstring = Docstring.from_sphinx(golden['docstring'])
        else:
            raise Exception('Unsupported docstring type {}'.format(
                golden['type']
            ))
        return docstring

    def parse_and_measure(self, golden):
        # type: (Golden) -> Tuple[float, bool]
        succeeded = True
        start = time.time()
        try:
            self.parse_golden(golden)
        except Exception:
            succeeded = False
        end = time.time()
        return end - start, succeeded

    def read_goldens(self):
        # type: () -> List[Golden]
        with open('integration_tests/goldens.json', 'r') as fin:
            goldens = json.load(fin)
        return goldens

    def test_golden_performance(self):
        # type: () -> Stats
        stats = Stats(
            times=list(),
            by_length=list(),
            google=list(),
            sphinx=list(),
        )
        goldens = self.read_goldens()
        for golden in goldens:
            duration, succeeded = self.parse_and_measure(golden)

            # Really, all of them should succeed, as this should
            # have run through the goldens test first.
            if not succeeded:
                continue

            stats.times.append(duration)
            if golden['type'] == 'GOOGLE':
                stats.google.append(duration)
            elif golden['type'] == 'SPHINX':
                stats.google.append(duration)
            else:
                raise Exception('Unexpected docstring type {}'.format(
                    golden['type'],
                ))
            stats.by_length.append(
                (len(golden['docstring']), duration)
            )
        return stats

    def print_chart(self, stats, width=65, height=25):
        # type: (Stats, int, int) -> None
        x_min, x_max = stats.by_length[0][0], stats.by_length[0][0]
        y_min, y_max = stats.by_length[0][1], stats.by_length[0][1]
        for x, y in stats.by_length:
            x_min = min(x, x_min)
            x_max = max(x, x_max)
            y_min = min(y, y_min)
            y_max = max(y, y_max)
        x_bucket = int(x_max - x_min) / width
        y_bucket = int(y_max - y_min) / height

        plot_points = defaultdict(lambda: defaultdict(lambda: 0))  # type: Dict[int, Dict[int, int]]  # noqa: E501

        max_amount = 0
        for x, y in stats.by_length:
            xb = int(x / x_bucket)
            yb = int(y / y_bucket)
            plot_points[xb][yb] += 1
            if plot_points[xb][yb] > max_amount:
                max_amount = plot_points[xb][yb]

        title = 'Time to Parse (seconds) by Length (chars)'
        print(title.rjust((width // 2) - (len(title) // 2) + len(title)))

        y_axis_top = str(int(y_max))
        y_axis_bottom = str(int(y_min))
        padding = max(len(y_axis_top), len(y_axis_bottom))
        print(y_axis_top.rjust(padding) + '│')
        for row in range(height + 1, -1, -1):
            if row == 0:
                print(y_axis_bottom.rjust(padding), end='│')
            else:
                print('│'.rjust(padding + 1), end='')
            for col in range(width + 1):
                point = plot_points[col][row]
                if point == 0:
                    print(' ', end='')
                elif 0 < point <= max_amount / 3:
                    print('○', end='')
                elif max_amount / 3 < point < 2 * (max_amount / 3):
                    print('◎', end='')
                elif 2 * (max_amount / 3) < point:
                    print('●', end='')
            print()
        print('└'.rjust(padding + 1) + '─' * (width))
        x_axis_left = str(int(x_min))
        x_axis_right = str(int(x_max))
        print('{}{}'.format(
            x_axis_left.rjust(padding + len(x_axis_left)),
            x_axis_right.rjust(width - (len(x_axis_left) + padding))
        ))

    def report_stats(self, stats):
        # type: (Stats) -> None
        print('x̄: {}'.format(mean(stats.times)))
        print('s: {}'.format(stdev(stats.times)))
        print()
        self.print_chart(stats)


def _read_from_cache(filename='.performance_testrun'):
    # type: (str) -> Optional[Stats]
    try:
        with open(filename, 'r') as fin:
            data = json.load(fin)
        return Stats.decode(data)
    except Exception:
        return None


def _write_to_cache(data, filename='.performance_testrun'):
    # type: (Stats, str) -> None
    with open(filename, 'w') as fout:
        json.dump(data.encode(), fout)


def _cache(perf):
    """Pull stats results from the cache.

    Intended for internal testing of the output format.

    Args:
        perf: The Performance object.

    Returns:
        The cached (or calculated) statistics.

    """
    prev = _read_from_cache()
    if prev and not prev.is_stale():
        return prev
    data = perf.test_golden_performance()
    _write_to_cache(data)
    return data


class PerformanceRegressionTest(TestCase):

    def test_performance_not_worse_than_before(self):
        prev_stats = _read_from_cache()
        perf = Performance()
        # Capture stats and test.
        stats = perf.test_golden_performance()
        if not prev_stats:
            _write_to_cache(stats)
            return
        prev_mean = mean(prev_stats.times)
        prev_stdev = stdev(prev_stats.times)
        curr_mean = mean(stats.times)
        delta = abs(prev_mean - curr_mean)

        # We aren't exactly performing a rigorous statistical
        # analysis here.  Really, we should do a proper difference
        # of means.
        self.assertTrue(
            delta < prev_stdev * 2,
            'Expected small variance in performance change, but '
            'current mean, {}, is more than two standard deviations ({}) '
            'from previous mean, {}'.format(
                curr_mean,
                prev_stdev,
                prev_mean,
            ),
        )

        # NOTE: Should we perform a difference of variance test?
        # Is that very meaningful in this context?

        # NOTE: Should we perform a test for difference of distributions?
        # That would give us a hint whether we're in a different time
        # complexity.

        _write_to_cache(stats)


def _record_historical(stats, filename='.performance_history'):
    # We don't bother with checking if it's unique or not, since
    # we can just open it in vim and do a sort.
    with open(filename, 'a') as fout:
        fout.write('{}\t{}\t{}\n'.format(
            datetime.fromtimestamp(stats.timestamp).isoformat(),
            mean(stats.times),
            stdev(stats.times),
        ))


def _main():
    print('DARGLINT STATS', end=' ')
    print_version()
    stats = _read_from_cache()
    perf = Performance()
    if not stats or stats.is_stale():
        stats = perf.test_golden_performance()
        _write_to_cache(stats)
    _record_historical(stats)
    perf.report_stats(stats)


if __name__ == '__main__':
    _main()
