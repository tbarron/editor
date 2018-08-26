from datetime import datetime as dt
import editor
import glob
import pexpect
import py
import pytest


# -----------------------------------------------------------------------------
def test_flake8():
    """
    Checks output of flake8
    """
    result = pexpect.run(u"flake8 conftest.py editor tests")
    assert b"" == result


# -----------------------------------------------------------------------------
def test_abandon(tmpdir, testdata):
    """
    Verifies that if an edit is abandoned (i.e., save=False passed to the
    quit() method), the original content is left in the file

        import editor
        q = editor.editor('filename')
        q.sub('good stuff', 'bad stuff')   # oops!
        q.quit(save=False)
        # original content left in 'filename'
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
    Verifies that <editor>.quit() with filepath argument saves the edited
    content to the alternate file path.

        import editor
        q = editor.editor('filename')
        q.quit(filepath='other_filename')
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(testdata.filename.strpath)

    # terminate the editor (should write out the file to a different name)
    other = tmpdir.join("another_filename")
    q.sub("test", "fribble")
    q.quit(filepath=other.strpath)

    # compute the expected edited content
    edited = [x.replace("test", "fribble") for x in testdata.orig]

    # verify that both backup and original file exist
    assert not hasattr(q, "backup_filename")
    assert testdata.filename.exists()
    assert other.exists()

    # verify that the new line IS in the original file
    assert written_format(testdata.orig) == testdata.filename.read()
    assert written_format(edited) == other.read()


# -----------------------------------------------------------------------------
def test_append(tmpdir, testdata):
    """
    Verifies that <editor>.append(data) appends *data* to the end of the file

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
    Verifies that the backup function gets called and that we can specify an
    alternate backup function.

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
    Verifies that a closed editor object will throw an error if we try to do
    something with it.

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
def test_copy_on_load_default(tmpdir, testdata):
    """
    Verifies that when we load a file with copy_on_load unspecified, no backup
    copy is created
    """
    pytest.debug_func()
    editor.editor(testdata.filename.strpath)
    fl = glob.glob(tmpdir.join("*").strpath)
    assert testdata.filename.strpath in fl
    assert len(fl) == 1


# -----------------------------------------------------------------------------
def test_copy_on_load_fixed(tmpdir, testdata):
    """
    Verifies that when we load a file with copy_on_load specified as a simple
    string (not a date format), a backup copy is created with the specified
    extension appended to the file name.
    """
    pytest.debug_func()
    editor.editor(testdata.filename.strpath, copy_on_load='~')
    fl = glob.glob(tmpdir.join("*").strpath)
    assert testdata.filename.strpath in fl
    assert len(fl) == 2
    [other] = [x for x in fl if x != testdata.filename.strpath]
    assert other == testdata.filename.strpath + "~"
    assert contents(testdata.filename.strpath) == contents(other)


# -----------------------------------------------------------------------------
def test_copy_on_load_fdate(tmpdir, testdata):
    """
    Verifies that when we load a file with copy_on_load specified as a data
    formattable string (eg., '%Y.%m%d'), a backup copy is created with the
    specified strftime-processed extension appended to the file name.
    """
    pytest.debug_func()
    ext = ".%Y.%m%d.%H%M%S"
    editor.editor(testdata.filename.strpath, copy_on_load=ext)
    fl = glob.glob(tmpdir.join("*").strpath)
    assert testdata.filename.strpath in fl
    assert len(fl) == 2
    [other] = [x for x in fl if x != testdata.filename.strpath]
    dstr = other.replace(testdata.filename.strpath, '')
    assert dt.strptime(dstr, ext)


# -----------------------------------------------------------------------------
def test_delete(testdata):
    """
    Verifies that <editor>.delete() removes matching lines

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
    Verifies that specifying newline='\r\n' in the .quit() call, puts CR-LF as
    line separators in the output file.

        import editor
        q = editor.editor('filename')
        q.append('This is a new line')
        q.quit(newline='\r\n')
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
    actual = testdata.filename.read_binary()
    assert exp == actual


# -----------------------------------------------------------------------------
def test_newfile(tmpdir, justdata):
    """
    Verifies that we can build the contents of a file in an editor object a
    line at a time.

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
    Verifies that specifying contents for an existing file throws an exception

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
    Verifies that the original file winds up with a backup name
    (YYYY.mmdd.HHMMSS added to the name) while the contents of the object
    buffer goes into the original file name.

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
    Verifies that an alternate backup routine can be called with argument to
    quit() method

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
    Verifies that with a change to every line in the editor buffer, .quit()
    writes that edited text to the original file and the original text to the
    backup file.

        import editor
        q = editor.editor('/path/to/file')
        # Make a change to every line in the editor object
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
    Checks the version
    """
    assert editor.editor.version() != ""


# -----------------------------------------------------------------------------
def test_wtarget_none():
    """
    Verifies that attempting to quit an editor object with no file name
    established throws an exception

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
def contents(path):
    """
    Return the contents of *path* as a string
    """
    with open(path, 'r') as inp:
        rval = inp.read()
    return rval


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
    Adds newlines to the test data at appropriate spots and writes the result
    to a file in tmpdir
    """
    testdata.orig = justdata.orig
    testdata.ovwr = justdata.ovwr
    testdata.filename = tmpdir.join("testfile")
    testdata.filename.write(written_format(testdata.orig))
    return testdata
