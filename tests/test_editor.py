import editor
import py
import pytest
import time

# -----------------------------------------------------------------------------
def test_abandon(tmpdir, testdata):
    """
    import editor
    q = editor.editor('filename')
    q.sub('good stuff', 'bad stuff')   # oops!
    q.quit(save=False)
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(testdata.filename.strpath)

    # append some data to the end of the editor buffer
    appline = "Oops! I should not have added this line\n"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit(save=False)

    # verify that original file exists but backup file does not
    assert testdata.filename.exists()
    assert not hasattr(q, "backup_filename")
    assert len(tmpdir.listdir()) == 1

    # verify that the new line IS in the original file
    assert testdata.filename.read() == testdata.orig


# -----------------------------------------------------------------------------
def test_another(tmpdir, testdata):
    """
    import editor
    q = editor.editor('filename')
    q.quit(filepath='other_filename')
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(testdata.filename.strpath)

    # terminate the editor (should write out the file to a different name)
    other = tmpdir.join("another_filename")
    q.quit(filepath=other.strpath)

    # verify that both backup and original file exist
    assert not hasattr(q, "backup_filename")
    assert testdata.filename.exists()
    assert other.exists()

    # verify that the new line IS in the original file
    assert testdata.filename.read() == testdata.orig
    assert other.read() == testdata.orig


# -----------------------------------------------------------------------------
def test_append(tmpdir, testdata):
    """
    import editor
    q = editor.editor('filename')
    q.append('This is a new line')
    q.quit(save=True)   # save=True is the default
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(testdata.filename.strpath)

    # append some data to the end of the editor buffer
    appline = "This line is not in the original test data\n"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit()

    # verify that both backup and original file exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert testdata.filename.exists()

    # verify that the new line is not in the backup file
    bdata = backup.read()
    assert appline not in bdata

    # verify that the new line IS in the original file
    assert testdata.filename.read() == testdata.orig + appline


# -----------------------------------------------------------------------------
def test_dos(tmpdir, testdata):
    """
    import editor
    q = editor.editor('filename')
    q.append('This is a new line')
    q.quit(save=True)   # save=True is the default
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(testdata.filename.strpath)

    # append some data to the end of the editor buffer
    appline = "This line is not in the original test data\n"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit(newline="\r\n")

    # verify that both backup and original file exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert testdata.filename.exists()

    # verify that the new line is not in the backup file
    assert appline not in backup.read()

    # verify that the new line IS in the original file
    result = testdata.orig + appline
    assert testdata.filename.read() == result.replace("\n", "\r\n")


# -----------------------------------------------------------------------------
def test_newfile(tmpdir, justdata):
    """
    import editor
    q = editor.editor(['line 1', 'line 2'])
    q.append('This is a line')
    q.append('Another line')
    ...
    q.quit(filepath='newfile')
    """
    init = "First line\n"
    last = "Last line\n"
    stem = tmpdir.join("newfile")
    assert len(tmpdir.listdir()) == 0
    q = editor.editor(content=[init])
    for _ in justdata.orig.strip().split("\n"):
        q.append(_ + "\n")
    q.append(last)
    q.quit(filepath=stem.strpath)
    assert stem.read() == init + justdata.orig + last


# -----------------------------------------------------------------------------
def test_overwrite_recovery(tmpdir, testdata):
    """
    import editor
    q = editor.editor('/path/to/file')
    # file is changed or overwritten by another process
    q.quit()
    # quit() writes old version to /path/to/file.YYYY.mmdd.HHMMSS
    """
    pytest.debug_func()
    orig_validator = testdata.orig.split('\n')[1]
    ovwr_validator = testdata.ovwr.split('\n')[2]

    # pull the test file content into an editor buffer
    q = editor.editor(testdata.filename.strpath)
    assert testdata.orig == ''.join(q.buffer)

    # overwrite the test file outside the editor
    testdata.filename.write(testdata.ovwr)

    # terminate the editor (saving the original data and backing up the
    # overwrite data)
    q.quit()

    # verify that the backup and original files exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert testdata.filename.exists()

    # verify that the backup file contains the right stuff
    assert backup.read() == testdata.ovwr

    # verify that the payload file contains the right stuff
    assert testdata.filename.read() == testdata.orig


# -----------------------------------------------------------------------------
def test_substitute(tmpdir, testdata):
    """
    import editor
    q = editor.editor('/path/to/file')
    # file is changed or overwritten by another process
    q.quit()
    # quit() writes old version to /path/to/file.YYYY.mmdd.HHMMSS
    """
    pytest.debug_func()

    # pull the test file content into an editor buffer
    q = editor.editor(testdata.filename.strpath)
    # assert all([_ in testdata.orig for _ in q.buffer])
    assert ''.join(q.buffer) == testdata.orig

    # make a change on every line
    # testdata.filename.write(testdata.ovwr)
    q.sub("e", "E")

    # terminate the editor (saving the original data and backing up the
    # overwrite data)
    q.quit()

    # verify that the backup and original files exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert testdata.filename.exists()

    # verify that the backup file contains the right stuff
    assert backup.read() == testdata.orig

    # verify that the payload file contains the right stuff
    assert testdata.filename.read() == testdata.orig.replace("e", "E")


# -----------------------------------------------------------------------------
def altbackup(filepath):
    """
    Fake backup function
    """
    altbackup.called = True


# -----------------------------------------------------------------------------
@pytest.fixture
def backup_reset():
    """
    Let the test run, then reset the backup routines
    """
    yield
    for bfunc in [altbackup, squawker]:
        try:
            del bfunc.called
        except AttributeError:
            pass


# -----------------------------------------------------------------------------
@pytest.fixture
def justdata(tmpdir):
    """
    Container of the test data
    """
    justdata.orig = ["This is a file containing",
                     "several lines of test data",
                     "to start us out on the",
                     "overwrite test."]
    justdata.ovwr = ["This is the overwriting data",
                     "Once the test is done, this",
                     "should no longer be present."]
    return justdata


# -----------------------------------------------------------------------------
def squawker(filepath):
    """
    Fake backup function
    """
    squawker.called = True


# -----------------------------------------------------------------------------
def written_format(lines, newline="\n"):
    """
    Concatenate *lines* with *newline* separators as if written in a file
    """
    return newline.join(lines) + newline


# -----------------------------------------------------------------------------
@pytest.fixture
def testdata(tmpdir, justdata):
    """
    Container of the test data
    """
    testdata.orig = justdata.orig
    testdata.ovwr = justdata.ovwr
    testdata.filename = tmpdir.join("testfile")
    testdata.filename.write(written_format(testdata.orig))
    return testdata
