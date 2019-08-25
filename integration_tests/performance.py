"""A utility for measuring performance characteristics for darglint.
"""

import json
import time
from collections import (
    defaultdict,
)
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    NamedTuple,
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

Stats = NamedTuple(
    'Stats',
    [
        ('times', List[float]),
        ('by_length', List[Tuple[int, float]]),
        ('google', List[float]),
        ('sphinx', List[float]),
    ]
)


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

    def print_chart(self, stats, width=65, height=35):
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

        y_axis_top = str(int(y_max))
        y_axis_bottom = str(int(y_min))
        padding = max(len(y_axis_top), len(y_axis_bottom))
        print('padding: {}'.format(padding))
        print(y_axis_top.rjust(padding) + '│')
        for row in range(height, -1, -1):
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
        print('└'.rjust(padding + 1) + '─' * (width - 1))
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


def _cache(perf):
    """Pull stats results from the cache.

    Intended for internal testing of the output format.

    Args:
        perf: The Performance object.

    Returns:
        The cached (or calculated) statistics.

    """
    def _encode(stats):
        return {
            'times': stats.times,
            'by_length': [[x, y] for x, y in stats.by_length],
            'google': stats.google,
            'sphinx': stats.sphinx,
        }

    def _decode(datum):
        datum['by_length'] = [(x, y) for x, y in datum['by_length']]
        return Stats(**datum)

    try:
        with open('.integration_cache', 'r') as fin:
            data = json.load(fin)
        return _decode(data)
    except Exception:
        pass
    data = perf.test_golden_performance()
    with open('.integration_cache', 'w') as fout:
        json.dump(_encode(data), fout)
    return data


if __name__ == '__main__':
    print('DARGLINT STATS', end=' ')
    print_version()
    perf = Performance()
    # stats = _cache(perf)
    stats = perf.test_golden_performance()
    perf.report_stats(stats)
