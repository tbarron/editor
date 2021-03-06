import os
import pdb
import pytest
import time


# -----------------------------------------------------------------------------
def pytest_addoption(parser):
    """
    Add the --logpath option to the command line
    """
    parser.addoption("--skip", action="append", default=[],
                     help="don't run the named test(s)")
    parser.addoption("--logpath", action="store", default="",
                     help="where to write a test log")
    parser.addoption("--dbg", action="append", default=[],
                     help="start debugger on test named or ALL")
    parser.addoption("--all", action="store_true", default=False,
                     help="override --exitfirst, continue after failures")


# -----------------------------------------------------------------------------
def pytest_report_header(config):
    """
    Put marker in the log file to show where the test run started
    """

    writelog(config, "-" * 60)


# -----------------------------------------------------------------------------
def pytest_configure(config):
    """
    If --all, turn off --exitfirst

    Rather than setting maxfail to an arbitrarily large value, it would be
    strategic to check the number of tests collected and set maxfail to that
    value plus 1. To do this, I need to find out how to get the number of tests
    collected.
    """
    if config.getoption("--all"):
        if "exitfirst" in config.option.__dict__:
            config.option.__dict__['exitfirst'] = False
        if "maxfail" in config.option.__dict__:
            config.option.__dict__['maxfail'] = 200


# -----------------------------------------------------------------------------
def pytest_runtest_setup(item):
    """
    For each test, just before it runs...
    """
    skipl = item.config.getoption("--skip")
    if any([item.name in skipl,
            any([_ in item.name for _ in skipl])]):
        pytest.skip()
    if any([item.name in item.config.getoption("--dbg"),
            'all' in item.config.getoption("--dbg")] +
           [_ in item.name for _ in item.config.getoption('--dbg')]):
        pytest.debug_func = pdb.set_trace
    else:
        pytest.debug_func = lambda: None


# -----------------------------------------------------------------------------
def pytest_unconfigure(config):
    """
    At the end of the run, log a summary
    """
    writelog(config, "passed: %d; FAILED: %d" % (writelog._passcount,
                                                 writelog._failcount))


# -----------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Write a line to the log file for this test
    """
    ctx = yield
    rep = ctx.result
    if rep.when != 'call':
        return

    if rep.outcome == 'failed':
        status = ">>>>FAIL"
        writelog._failcount += 1
    elif rep.outcome == 'passed':
        status = "--pass"
        writelog._passcount += 1
    elif rep.outcome == 'skipped':
        status = '**skip'
    else:
        status = 'other '

    parent = item.parent
    msg = "%-8s %s:%s.%s" % (status,
                             os.path.basename(parent.fspath.strpath),
                             parent.name,
                             item.name)
    writelog(item.config, msg)


# -----------------------------------------------------------------------------
def writelog(config, loggable):
    """
    Here's where we actually write to the log file is one was specified
    """
    logpath = config.getoption("logpath")
    if logpath == "":
        return
    f = open(logpath, 'a')
    msg = "%s %s\n" % (time.strftime("%Y.%m%d %H:%M:%S"),
                       loggable)
    f.write(msg)
    f.close()


writelog._passcount = 0
writelog._failcount = 0
