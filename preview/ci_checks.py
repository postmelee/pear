#!/usr/bin/env python3
"""Run portable Preview fixtures; never start an app, runtime or real account."""
import json
from pathlib import Path
import sys
import unittest


def main():
    suite = unittest.TestLoader().discover(str(Path(__file__).parent), pattern='test_*.py')
    count = suite.countTestCases()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = dict(scope='synthetic fixtures only', discovered=count, ran=result.testsRun,
                   failures=len(result.failures), errors=len(result.errors),
                   skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
                   unexpected_successes=len(result.unexpectedSuccesses))
    print(json.dumps(summary, sort_keys=True))
    return 0 if (count > 0 and result.testsRun == count and result.wasSuccessful()
                 and not result.skipped and not result.expectedFailures
                 and not result.unexpectedSuccesses) else 1


if __name__ == '__main__':
    sys.exit(main())
