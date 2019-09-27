"""A utility for measuring performance characteristics for darglint.

Performs performance tests at two levels: the individual docstring,
and individual files.

"""

from collections import (
    defaultdict,
)
from datetime import (
    datetime,
)
from enum import Enum
import json
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Iterable,
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
import subprocess
import os


Golden = Dict[str, Any]


class PerfScope(Enum):

    DOCSTRING = 1
    MODULE = 2


class Stats(object):

    STALE_AGE_MINS = 30

    def __init__(self, times, by_length, google, sphinx,
                 timestamp=None, scope=PerfScope.MODULE):
        # type: (List[float], List[Tuple[int, float]], List[float], List[float], int, PerfScope) -> None  # noqa: E501
        self.times = times
        self.by_length = by_length
        self.google = google
        self.sphinx = sphinx
        self.scope = scope

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
            'scope': self.scope.value,
        }


class Chart(object):
    """A quick graphical representation of the stats."""

    def __init__(self, stats, width=65, height=25):
        # type: (Stats, int, int) -> None
        self.stats = stats
        self.width = width
        self.height = height

    def __str__(self):
        # type: () -> str
        x_min, x_max = self.stats.by_length[0][0], self.stats.by_length[0][0]
        y_min, y_max = self.stats.by_length[0][1], self.stats.by_length[0][1]
        for x, y in self.stats.by_length:
            x_min = min(x, x_min)
            x_max = max(x, x_max)
            y_min = min(y, y_min)
            y_max = max(y, y_max)
        x_bucket = int(x_max - x_min) / self.width
        if x_bucket <= 0:
            x_bucket = 1
        y_bucket = int(y_max - y_min) / self.height
        if y_bucket <= 0:
            y_bucket = 1

        plot_points = defaultdict(lambda: defaultdict(lambda: 0))  # type: Dict[int, Dict[int, int]]  # noqa: E501

        max_amount = 0
        for x, y in self.stats.by_length:
            xb = int(x / x_bucket)
            yb = int(y / y_bucket)
            plot_points[xb][yb] += 1
            if plot_points[xb][yb] > max_amount:
                max_amount = plot_points[xb][yb]

        title = 'Time to Parse (seconds) by Length (chars)\n'
        ret = title.rjust((self.width // 2) - (len(title) // 2) + len(title))

        y_axis_top = str(int(y_max))
        y_axis_bottom = str(int(y_min))
        padding = max(len(y_axis_top), len(y_axis_bottom))
        ret += y_axis_top.rjust(padding) + '│\n'
        for row in range(self.height + 1, -1, -1):
            if row == 0:
                ret += y_axis_bottom.rjust(padding) + '│'
            else:
                ret += '│'.rjust(padding + 1)
            for col in range(self.width + 1):
                point = plot_points[col][row]
                if point == 0:
                    ret += ' '
                elif 0 < point <= max_amount / 3:
                    ret += '○'
                elif max_amount / 3 < point < 2 * (max_amount / 3):
                    ret += '◎'
                elif 2 * (max_amount / 3) < point:
                    ret += '●'
            ret += '\n'
        ret += '└'.rjust(padding + 1) + '─' * (self.width) + '\n'
        x_axis_left = str(int(x_min))
        x_axis_right = str(int(x_max))
        ret += '{}{}\n'.format(
            x_axis_left.rjust(padding + len(x_axis_left)),
            x_axis_right.rjust(self.width - (len(x_axis_left) + padding))
        )
        return ret


class Performance(object):
    """Measure and report on performance of darglint."""

    def __init__(self, stats=None, module_stats=None):
        # type: (Optional[Stats], Optional[Stats]) -> None
        self.stats = stats
        self.module_stats = module_stats

    def report_worst_five_percent(self, scope=PerfScope.DOCSTRING):
        # type: (PerfScope) -> None
        if scope == PerfScope.DOCSTRING:
            stats = self.stats
        elif scope == PerfScope.MODULE:
            stats = self.module_stats
        else:
            raise Exception('Unrecognized PerfScope {}'.format(scope))
        assert stats
        total = len(stats.times)
        n = int(0.01 * total)
        assert n > 0
        sorted_stats = sorted(stats.times)
        worst = mean(sorted_stats[-1 * n:])
        print('1 %ile mean: {}'.format(worst))

    def report_stats(self):
        # type: () -> None
        if self.stats:
            print('∷∴∵∴∵∴∵∴∵∴∵∴∵ DOCSTRING ∴∵∴∵∴∵∴∵∴∵∴∵∷')
            print('x̄: {}'.format(mean(self.stats.times)))
            print('s: {}'.format(stdev(self.stats.times)))
            print('n: {}'.format(len(self.stats.times)))
            self.report_worst_five_percent()
            print()
            chart = Chart(self.stats)
            print(chart)
            print()

        if self.module_stats:
            print('∷∴∵∴∵∴∵∴∵∴∵∴∵∴∵ MODULE ∴∵∴∵∴∵∴∵∴∵∴∵∴∵∷')
            print('x̄: {}'.format(mean(self.module_stats.times)))
            print('s: {}'.format(stdev(self.module_stats.times)))
            print('n: {}'.format(len(self.module_stats.times)))
            self.report_worst_five_percent(PerfScope.MODULE)
            print()
            chart = Chart(self.module_stats)
            print(chart)

    def _parse_golden(self, golden):
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

    def _parse_and_measure(self, golden):
        # type: (Golden) -> Tuple[float, bool]
        succeeded = True
        start = time.time()
        try:
            self._parse_golden(golden)
        except Exception:
            succeeded = False
        end = time.time()
        return end - start, succeeded

    def _read_goldens(self):
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
        goldens = self._read_goldens()
        for golden in goldens:
            duration, succeeded = self._parse_and_measure(golden)

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
        self.stats = stats
        return stats

    def _read_and_measure(self, filename):
        # type: (str) -> Tuple[float, bool, str]
        succeeded = True
        start = time.time()
        try:
            completed_process = subprocess.run([
                'darglint',
                filename
            ], stdout=subprocess.PIPE)
            value = completed_process.stdout.decode('utf8')
        except Exception:
            succeeded = False
            value = ''
        end = time.time()
        return end - start, succeeded, value

    def _get_module_size(self, filename):
        # type: (str) -> Optional[int]
        try:
            completed_process = subprocess.run([
                'wc',
                '-l',
                filename,
            ], stdout=subprocess.PIPE)
            value = completed_process.stdout.decode('utf8')
            return int(value.split()[0])
        except Exception:
            return None

    def yield_modules(self):
        # type: () -> Iterable[str]
        for path, folders, filenames in os.walk('integration_tests/repos'):
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                yield os.path.join(path, filename)

    def test_repo_performance(self):
        assert not self.module_stats
        stats = Stats(
            times=list(),
            by_length=list(),
            google=list(),
            sphinx=list(),
            scope=PerfScope.MODULE,
        )
        self.module_stats = stats
        for module in self.yield_modules():
            duration, succeed, value = self._read_and_measure(module)
            size = self._get_module_size(module)
            if size is None:
                succeed = False
            if succeed:
                stats.times.append(duration)
                stats.by_length.append((size, duration))
        return stats


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


class PerformanceRegressionTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.prev_stats = _read_from_cache()
        cls.prev_module_stats = _read_from_cache('.performance_module_testrun')
        cls.stats = Stats(
            times=list(),
            by_length=list(),
            google=list(),
            sphinx=list(),
        )
        cls.module_stats = Stats(
            times=list(),
            by_length=list(),
            google=list(),
            sphinx=list(),
        )

    @classmethod
    def tearDownClass(cls):
        _write_to_cache(cls.stats)
        _write_to_cache(cls.module_stats, '.performance_module_testrun')

    def test_performance_not_worse_than_before(self):
        # Capture stats and test.
        perf = Performance()
        self.stats = perf.test_golden_performance()
        if not self.prev_stats or not len(self.prev_stats.times):
            return
        prev_mean = mean(self.prev_stats.times)
        prev_stdev = stdev(self.prev_stats.times)
        curr_mean = mean(self.stats.times)
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

    def test_performance_against_repositories(self):
        perf = Performance()
        self.module_stats = perf.test_repo_performance()


def _record_historical(stats, module_stats, filename='.performance_history'):
    # We don't bother with checking if it's unique or not, since
    # we can just open it in vim and do a sort.
    with open(filename, 'a') as fout:
        fout.write('{}\t{}\t{}\t{}\t{}\n'.format(
            datetime.fromtimestamp(stats.timestamp).isoformat(),
            mean(stats.times),
            stdev(stats.times),
            mean(module_stats.times),
            stdev(module_stats.times),
        ))


def _main():
    print('DARGLINT STATS', end=' ')
    print_version()
    stats = _read_from_cache()
    perf = Performance(stats)
    if not stats or stats.is_stale() or not len(stats.times):
        stats = perf.test_golden_performance()
        _write_to_cache(stats)

    module_stats = _read_from_cache('.performance_module_testrun')
    if (not module_stats
            or module_stats.is_stale()
            or not len(module_stats.times)):
        module_stats = perf.test_repo_performance()
        _write_to_cache(module_stats, '.performance_module_testrun')
    perf.module_stats = module_stats
    _record_historical(stats, module_stats)
    perf.report_stats()


if __name__ == '__main__':
    _main()
