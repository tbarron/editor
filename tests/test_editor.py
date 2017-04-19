import editor
import pexpect
import py
import pytest


# -----------------------------------------------------------------------------
def test_flake8():
    """
    Check output of flake8
    """
    result = pexpect.run(u"flake8 conftest.py editor tests")
    assert b"" == result


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
    appline = "Oops! I should not have added this line"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit(save=False)

    # verify that original file exists but backup file does not
    assert testdata.filename.exists()
    assert not hasattr(q, "backup_filename")
    assert len(tmpdir.listdir()) == 1

    # verify that the appended line is not in the original file
    assert written_format(testdata.orig) == testdata.filename.read()
    assert appline not in testdata.filename.read()


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
    assert written_format(testdata.orig) == testdata.filename.read()
    assert written_format(testdata.orig) == other.read()


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
    appline = "This line is not in the original test data"
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
    exp = written_format(testdata.orig + [appline])
    assert exp == testdata.filename.read()


# -----------------------------------------------------------------------------
def test_backup_function(tmpdir, testdata, backup_reset):
    """
    q = editor.editor(..., backup=function, ...)
    q.quit()   # verify that function runs
    """
    pytest.debug_func()
    assert not hasattr(squawker, 'called')
    q = editor.editor(testdata.filename.strpath, backup=squawker)
    assert not hasattr(squawker, 'called')
    q.quit()
    assert hasattr(squawker, 'called') and squawker.called


# -----------------------------------------------------------------------------
def test_closed(testdata):
    """
    q = editor.editor()
    q.quit()
    q.quit()      # expect editor.Error('already closed')
    """
    pytest.debug_func()
    q = editor.editor(filepath=testdata.filename.strpath)
    q.quit()
    with pytest.raises(editor.Error) as err:
        q.quit()
    assert "This file is already closed" in str(err)


# -----------------------------------------------------------------------------
def test_delete(testdata):
    """
    q = editor.editor()
    q.delete(<expr>)
    q.quit()      # expect matching lines to have disappeared
    """
    pytest.debug_func()
    q = editor.editor(filepath=testdata.filename.strpath)
    rmd = q.delete(' test')
    q.quit()
    backup = py.path.local(q.backup_filename)

    assert q.closed
    assert testdata.orig[1] in [_.strip() for _ in rmd]
    assert testdata.orig[3] in rmd
    assert len(rmd) == 2
    assert backup.exists()
    assert testdata.filename.exists()
    assert testdata.orig[1] not in testdata.filename.read()
    assert testdata.orig[3] not in testdata.filename.read()


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
    appline = "This line is not in the original test data"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit(newline="\r\n")

    # verify that both backup and original file exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert testdata.filename.exists()

    # verify that the new line is not in the backup file
    assert written_format(testdata.orig) in backup.read()
    assert appline not in backup.read()

    # verify that the new line IS in the original file
    # exp = testdata.orig.replace("\n", "\r\n") + appline + "\r\n"
    exp = bytearray(written_format(testdata.orig + [appline], newline="\r\n"),
                    'utf8')
    actual = bytearray(testdata.filename.read_binary(), 'utf8')
    assert exp == actual


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
    pytest.debug_func()
    init = "First line"
    last = "Last line"
    stem = tmpdir.join("newfile")
    assert len(tmpdir.listdir()) == 0
    q = editor.editor(filepath=stem.strpath, content=[init])
    for _ in justdata.orig:
        q.append(_)
    q.append(last)
    q.quit(filepath=stem.strpath)
    exp = written_format([init] + justdata.orig + [last])
    assert exp == stem.read()


# -----------------------------------------------------------------------------
def test_overwrite_fail(tmpdir, testdata):
    """
    q = editor.editor('/path/to/file', content=['foo', 'bar'])
    """
    pytest.debug_func()
    with pytest.raises(editor.Error) as err:
        q = editor.editor(filepath=testdata.filename.strpath,  # noqa: F841
                          content=['line 1', 'line 2'])
    assert testdata.filename.strpath in str(err)
    assert "To overwrite it" in str(err)
    assert "Error" in repr(err)


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

    # pull the test file content into an editor buffer
    q = editor.editor(testdata.filename.strpath)
    assert testdata.orig == q.buffer

    # overwrite the test file outside the editor
    testdata.filename.write(written_format(testdata.ovwr))

    # terminate the editor (saving the original data and backing up the
    # overwrite data)
    q.quit()

    # verify that the backup and original files exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert testdata.filename.exists()

    # verify that the backup file contains the right stuff
    assert written_format(testdata.ovwr) == backup.read()

    # verify that the payload file contains the right stuff
    assert written_format(testdata.orig) == testdata.filename.read()


# -----------------------------------------------------------------------------
def test_qbackup(tmpdir, testdata, backup_reset):
    """
    q = editor.editor('/path/to/file', backup=foobar)
    q.quit(backup=other)
    assert not foobar.called
    assert other.called
    """
    pytest.debug_func()
    try:
        del squawker.called
    except AttributeError:
        pass
    q = editor.editor(testdata.filename.strpath, backup=squawker)
    q.quit(backup=altbackup)
    assert not hasattr(squawker, 'called')
    assert hasattr(altbackup, 'called') and altbackup.called


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
    assert testdata.orig == q.buffer

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
    assert written_format(testdata.orig) == backup.read()

    # verify that the payload file contains the right stuff
    exp = written_format([_.replace("e", "E") for _ in testdata.orig])
    assert exp == testdata.filename.read()


# -----------------------------------------------------------------------------
def test_version():
    """
    Check the version
    """
    assert editor.editor.version() != ""


# -----------------------------------------------------------------------------
def test_wtarget_none():
    """
    q = editor.editor(content=['one', 'two'])
    q.quit()        # expect Error('No filepath specified...')
    """
    pytest.debug_func()
    q = editor.editor(content=["one", "two"])
    with pytest.raises(editor.Error) as err:
        q.quit()
    assert "No filepath specified" in str(err)


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
