import editor
import glob
import pexpect
import py
import pytest
import re
import tbx


# -----------------------------------------------------------------------------
def test_flake8():
    """
    Checks output of flake8
    """
    result = pexpect.run(u"flake8 conftest.py editor tests")
    assert b"" == result


# -----------------------------------------------------------------------------
def test_abandon(tmpdir, td, fx_chdir):
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
    q = editor.editor(td.basename)

    # append some data to the end of the editor buffer
    appline = "Oops! I should not have added this line"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit(save=False)

    # verify that original file exists but backup file does not
    assert td.filename.exists()
    assert not hasattr(q, "backup_filename")
    assert len(tmpdir.listdir()) == 1

    # verify that the appended line is not in the original file
    content = td.filename.read()
    assert written_format(td.orig) == content
    assert appline not in content


# -----------------------------------------------------------------------------
def test_another(tmpdir, td, fx_chdir):
    """
    Verifies that <editor>.quit() with filepath argument saves the edited
    content to the alternate file path.

        import editor
        q = editor.editor('filename')
        q.quit(filepath='other_filename')
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(td.basename)

    # terminate the editor (should write out the file to a different name)
    other = tmpdir.join("another_filename")
    q.sub("test", "fribble")
    q.quit(filepath=other.strpath)

    # compute the expected edited content
    edited = [x.replace("test", "fribble") for x in td.orig]

    # verify that both backup and original file exist
    assert not hasattr(q, "backup_filename")
    assert td.filename.exists()
    assert other.exists()

    # verify that the new line IS in the original file
    assert written_format(td.orig) == td.filename.read()
    assert written_format(edited) == other.read()


# -----------------------------------------------------------------------------
def test_append(tmpdir, td, fx_chdir):
    """
    Verifies that <editor>.append(data) appends *data* to the end of the file

        import editor
        q = editor.editor('filename')
        q.append('This is a new line')
        q.quit(save=True)   # save=True is the default
    """
    pytest.debug_func()

    # load the test data into an editor object
    q = editor.editor(td.basename)

    # append some data to the end of the editor buffer
    appline = "This line is not in the original test data"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit()

    # verify that both backup and original file exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert td.filename.exists()

    # verify that the new line is not in the backup file
    bdata = backup.read()
    assert appline not in bdata

    # verify that the new line IS in the original file
    exp = written_format(td.orig + [appline])
    assert exp == td.filename.read()


# -----------------------------------------------------------------------------
def test_backup_altfunc(tmpdir, td, fx_chdir):
    """
    Verify that backup=alt_func causes alt_func to be run for backup (at save
    time).

    [backup=alt_backup_function]
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=alt_backup)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.abm_name + td.dfmt in fl


# -----------------------------------------------------------------------------
def test_backup_altfunc_q(tmpdir, td, fx_chdir):
    """
    Verify that backup=alt_func passed to .quit() causes alt_func to be run for
    backup (at save time).

    [backup=alt_backup_function]
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit(backup=alt_backup)
    fl = glob_assert("*", 2)
    assert td.abm_name + td.dfmt in fl


# -----------------------------------------------------------------------------
def test_backup_default(tmpdir, td, fx_chdir):
    """
    Verify that passing no values for backup yields the default backup
    behavior.

    [backup unspecified (defaults)]
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl
    [other] = [x for x in fl if x != td.basename]
    dstr = other.replace(td.basename, '')
    assert re.match(td.drgx, dstr)


# -----------------------------------------------------------------------------
def test_backup_default_strftime(tmpdir, td, fx_chdir):
    """
    Verify that backup=('.%Y%b%d', 'load') does the right thing
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(td.ymd_fmt, 'load'))
    fl = glob_assert("*", 2)
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(td.ymd_rgx, left)
    q.quit()


# -----------------------------------------------------------------------------
def test_backup_default_strftime_q(tmpdir, td, fx_chdir):
    """
    Verify that backup=('.%Y.%m%d.%H%M%S') behaves as expected
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(td.dfmt, 'save'))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(td.drgx, left)


# -----------------------------------------------------------------------------
def test_backup_extension(tmpdir, td, fx_chdir):
    """
    Verify that backup='extension' works. (Can't use 'save' or 'load' as a file
    name extension, but '.save' or '.load' should work.)

    [backup='ext']
    """
    pytest.debug_func()
    ext = '.fiddle'
    q = editor.editor(td.basename, backup=ext)
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert left == ext


# -----------------------------------------------------------------------------
def test_backup_extension_q(tmpdir, td, fx_chdir):
    """
    Verify that backup='extension' works when passed to .quit(). (Can't use
    'save' or 'load' as a file name extension, but '.save' or '.load' should
    work.)

    [backup='ext']
    """
    pytest.debug_func()
    ext = '.fiddle'
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit(backup=ext)
    fl = glob_assert("*", 2)
    assert td.basename in fl

    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert left == ext


# -----------------------------------------------------------------------------
def test_backup_func_ext(tmpdir, td, fx_chdir):
    """
    Verify that backup=('ext', function) calls function('ext') at save time.

    [backup=('ext', function)]
    """
    pytest.debug_func()
    ext = ".wumpus"
    q = editor.editor(td.basename, backup=(ext, alt_backup))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.abm_name + ext in fl


# -----------------------------------------------------------------------------
def test_backup_func_ymd(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, '%Y%b%d') calls function('%Y%b%d') at save
    time.

    [backup=(function, '%Y%b%d')]
    """
    pytest.debug_func()
    ext = td.ymd_fmt
    q = editor.editor(td.basename, backup=(alt_backup, ext))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.abm_name + td.ymd_fmt in fl


# -----------------------------------------------------------------------------
def test_backup_func_ymd_load(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, '%b%y%H', 'load') calls function('%b%y%H') at
    load time.

    [backup=(function, '%b%y%H', 'load')]
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, td.ymd_fmt, 'load'))
    fl = glob_assert("*", 2)
    assert td.abm_name + td.ymd_fmt in fl
    q.quit()
    fl = glob_assert("*", 2)


# -----------------------------------------------------------------------------
def test_backup_func_ymd_save(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, '%b%y%H', 'save') calls function('%b%y%H') at
    save time.

    [backup=(function, '%b%y%H', 'save')]
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, td.ymd_fmt, 'save'))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.abm_name + td.ymd_fmt in fl


# -----------------------------------------------------------------------------
def test_backup_load(tmpdir, td, fx_chdir):
    """
    Verify that backup='load' makes the backup happen at load time.

    [backup='load']
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup='load')
    fl = glob_assert("*", 2)
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(td.drgx, left)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl


# -----------------------------------------------------------------------------
def test_backup_load_ext(tmpdir, td, fx_chdir):
    """
    Verify that backup=('load', '.ext') makes the backup happen at load time
    and uses the specified extension.

    [backup=('load', 'ext')]
    """
    pytest.debug_func()
    ext = ".frooble"
    q = editor.editor(td.basename, backup=('load', ext))
    fl = glob_assert("*", 2)
    assert td.basename in fl
    assert "{}{}".format(td.basename, ext) in fl
    q.quit()
    fl = glob_assert("*", 2)


# -----------------------------------------------------------------------------
def test_backup_load_func(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, 'load') runs function at load time.

    [backup=(function, 'load')]
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, 'load'))
    fl = glob_assert("*", 2)
    assert "{}{}".format(td.abm_name, td.dfmt) in fl
    q.quit()
    fl = glob_assert("*", 2)


# -----------------------------------------------------------------------------
def test_backup_save(tmpdir, td, fx_chdir):
    """
    Verify that backup='save' delays the backup time to when .quit() is called.

    [backup='save']
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup='save')
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(td.drgx, left)


# -----------------------------------------------------------------------------
def test_backup_save_ext(tmpdir, td, fx_chdir):
    """
    Verify that backup=('.ext', 'save') makes the backup at save time with .ext
    as the extension on the backup file.

    [backup=('.ext', 'save')]
    """
    pytest.debug_func()
    ext = ".backup"
    q = editor.editor(td.basename, backup=('save', ext))
    fl = glob_assert("*", 1)
    assert td.basename in fl
    q.quit()
    fl = glob_assert("*", 2)
    assert "{}{}".format(td.basename, ext) in fl


# -----------------------------------------------------------------------------
def test_backup_save_func(tmpdir, td, fx_chdir):
    """
    Verify that backup=('save', function) runs function at save time.

    [backup=('save', function)]
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=('save', alt_backup))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert "alt_backup_marker{}".format(td.dfmt) in fl


# -----------------------------------------------------------------------------
def test_backup_save_func_q(tmpdir, td, fx_chdir):
    """
    Verify that backup=('save', function) passed to .quit() runs function at
    save time.

    [backup=('save', function)]
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit(backup=('save', alt_backup))
    fl = glob_assert("*", 2)
    assert "alt_backup_marker{}".format(td.dfmt) in fl


# -----------------------------------------------------------------------------
def test_backup_function(tmpdir, td, backup_reset):
    """
    Verifies that the backup function gets called and that we can specify an
    alternate backup function.

        q = editor.editor(..., backup=function, ...)
        q.quit()   # verify that function runs
    """
    pytest.debug_func()
    assert not hasattr(squawker, 'called')
    q = editor.editor(td.filename.strpath, backup=squawker)
    assert not hasattr(squawker, 'called')
    q.quit()
    assert hasattr(squawker, 'called') and squawker.called


# -----------------------------------------------------------------------------
def test_closed(td):
    """
    Verifies that a closed editor object will throw an error if we try to do
    something with it.

        q = editor.editor()
        q.quit()
        q.quit()      # expect editor.Error('already closed')
    """
    pytest.debug_func()
    q = editor.editor(filepath=td.filename.strpath)
    q.quit()
    with pytest.raises(editor.Error) as err:
        q.quit()
    assert "This file is already closed" in str(err)


# -----------------------------------------------------------------------------
def test_delete(td):
    """
    Verifies that <editor>.delete() removes matching lines

        q = editor.editor()
        q.delete(<expr>)
        q.quit()      # expect matching lines to have disappeared
    """
    pytest.debug_func()
    q = editor.editor(filepath=td.filename.strpath)
    rmd = q.delete(' test')
    q.quit()
    backup = py.path.local(q.backup_filename)

    assert q.closed
    assert td.orig[1] in [_.strip() for _ in rmd]
    assert td.orig[3] in rmd
    assert len(rmd) == 2
    assert backup.exists()
    assert td.filename.exists()
    assert td.orig[1] not in td.filename.read()
    assert td.orig[3] not in td.filename.read()


# -----------------------------------------------------------------------------
def test_dos(tmpdir, td):
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
    q = editor.editor(td.filename.strpath)

    # append some data to the end of the editor buffer
    appline = "This line is not in the original test data"
    q.append(appline)

    # terminate the editor (should write out the file)
    q.quit(newline="\r\n")

    # verify that both backup and original file exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert td.filename.exists()

    # verify that the new line is not in the backup file
    assert written_format(td.orig) in backup.read()
    assert appline not in backup.read()

    # verify that the new line IS in the original file
    # exp = testdata.orig.replace("\n", "\r\n") + appline + "\r\n"
    exp = bytearray(written_format(td.orig + [appline], newline="\r\n"),
                    'utf8')
    actual = td.filename.read_binary()
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
def test_overwrite_fail(tmpdir, td):
    """
    Verifies that specifying contents for an existing file throws an exception

        q = editor.editor('/path/to/file', content=['foo', 'bar'])
    """
    pytest.debug_func()
    with pytest.raises(editor.Error) as err:
        q = editor.editor(filepath=td.filename.strpath,  # noqa: F841
                          content=['line 1', 'line 2'])
    assert td.filename.strpath in str(err)
    assert "To overwrite it" in str(err)
    assert "Error" in repr(err)


# -----------------------------------------------------------------------------
def test_overwrite_recovery(tmpdir, td):
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
    q = editor.editor(td.filename.strpath)
    assert td.orig == q.buffer

    # overwrite the test file outside the editor
    td.filename.write(written_format(td.ovwr))

    # terminate the editor (saving the original data and backing up the
    # overwrite data)
    q.quit()

    # verify that the backup and original files exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert td.filename.exists()

    # verify that the backup file contains the right stuff
    assert written_format(td.ovwr) == backup.read()

    # verify that the payload file contains the right stuff
    assert written_format(td.orig) == td.filename.read()


# -----------------------------------------------------------------------------
def test_qbackup(tmpdir, td, backup_reset):
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
    q = editor.editor(td.filename.strpath, backup=squawker)
    q.quit(backup=altbackup)
    assert not hasattr(squawker, 'called')
    assert hasattr(altbackup, 'called') and altbackup.called


# -----------------------------------------------------------------------------
def test_substitute(tmpdir, td):
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
    q = editor.editor(td.filename.strpath)
    # assert all([_ in testdata.orig for _ in q.buffer])
    assert td.orig == q.buffer

    # make a change on every line
    # testdata.filename.write(testdata.ovwr)
    q.sub("e", "E")

    # terminate the editor (saving the original data and backing up the
    # overwrite data)
    q.quit()

    # verify that the backup and original files exist
    backup = py.path.local(q.backup_filename)
    assert backup.exists()
    assert td.filename.exists()

    # verify that the backup file contains the right stuff
    assert written_format(td.orig) == backup.read()

    # verify that the payload file contains the right stuff
    exp = written_format([_.replace("e", "E") for _ in td.orig])
    assert exp == td.filename.read()


# -----------------------------------------------------------------------------
def test_trailing_whitespace(tmpdir, td):
    """
    Detects the bug where trailing whitespace on the last line of the file is
    lost because of the rstrip() in <editor>.contents()
    """
    pytest.debug_func()

    td.orig[-1] += "     "
    wws = tmpdir.join("with_whitespace")
    wws.write(written_format(td.orig))

    q = editor.editor(wws.strpath)
    assert td.orig == q.buffer


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
def alt_backup(ext):
    """
    Alternate backup function
    """
    filename = "alt_backup_marker{}".format(ext)
    open(filename, 'w').close()


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
def glob_assert(globexpr, exp_count):
    flist = glob.glob(globexpr)
    assert len(flist) == exp_count
    return flist


# -----------------------------------------------------------------------------
@pytest.fixture
def fx_chdir(tmpdir):
    with tbx.chdir(tmpdir.strpath):
        yield


# -----------------------------------------------------------------------------
@pytest.fixture
def td(tmpdir, justdata):
    """
    Adds newlines to the test data at appropriate spots and writes the result
    to a file in tmpdir
    """
    td.orig = justdata.orig
    td.ovwr = justdata.ovwr
    td.filename = tmpdir.join("testfile")
    td.filename.write(written_format(td.orig))
    td.basename = td.filename.basename
    td.abm_name = "alt_backup_marker"
    td.drgx = "\.\d{4}\.\d{4}\.\d{6}"
    td.ymd_fmt = ".%Y%b%d"
    td.ymd_rgx = "^\.\d{4}\w{3}\d{2}$"
    td.dfmt = ".%Y.%m%d.%H%M%S"
    return td
