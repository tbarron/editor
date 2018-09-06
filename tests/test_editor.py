import editor
import glob
import pexpect
import py
import pytest
import re
import tbx

from editor.text import catalog as K


# -----------------------------------------------------------------------------
def test_flake8():
    """
    Checks output of flake8 on payload and test code
    """
    result = pexpect.run(K["flake_cmd"])
    assert "" == result.decode()


# -----------------------------------------------------------------------------
def test_abandon(tmpdir, td, fx_chdir):
    """
    Verifies that if an abandoned edit (i.e., save=False passed to the quit()
    method) leaves the original content is left in the source file without
    creating a backup.
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    q.append(K["oops"])
    q.quit(save=False)
    assert td.filename.exists()
    assert q.backup_filename() is None
    assert len(tmpdir.listdir()) == 1
    content = td.filename.read()
    assert written_format(K["orig_l"]) == content
    assert K["oops"] not in content


# -----------------------------------------------------------------------------
def test_another(tmpdir, td, fx_chdir):
    """
    Verifies that <editor>.quit() with filepath argument saves the edited
    content to the alternate file path.
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    other = tmpdir.join(K["altfile"])
    q.sub(K["test"], K["frib"])
    q.quit(filepath=other.strpath)
    edited = [x.replace(K["test"], K["frib"]) for x in K["orig_l"]]
    assert q.backup_filename() is None
    assert td.filename.exists()
    assert other.exists()
    assert written_format(K["orig_l"]) == td.filename.read()
    assert written_format(edited) == other.read()


# -----------------------------------------------------------------------------
def test_append(tmpdir, td, fx_chdir):
    """
    Verifies that <editor>.append(data) appends *data* to the end of the file
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    q.append(K["new"])
    q.quit()
    backup = py.path.local(q.backup_filename())
    assert backup.exists()
    assert td.filename.exists()
    bdata = backup.read()
    assert K["new"] not in bdata
    exp = written_format(K["orig_l"] + [K["new"]])
    assert exp == td.filename.read()


# -----------------------------------------------------------------------------
def test_backup_altfunc(tmpdir, td, fx_chdir):
    """
    Verify that backup=alt_func causes alt_func to be run for backup (at save
    time).
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=alt_backup)
    q.quit()
    fl = glob_assert("*", 2)
    assert K["abm"] + K["dfmt"] in fl


# -----------------------------------------------------------------------------
def test_backup_altfunc_q(tmpdir, td, fx_chdir):
    """
    Verify that backup=alt_func passed to .quit() causes alt_func to be run for
    backup (at save time).
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit(backup=alt_backup)
    fl = glob_assert("*", 2)
    assert K["abm"] + K["dfmt"] in fl


# -----------------------------------------------------------------------------
def test_backup_default(tmpdir, td, fx_chdir):
    """
    Verify that passing no values for backup yields the default backup
    behavior.
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl
    [other] = [x for x in fl if x != td.basename]
    dstr = other.replace(td.basename, '')
    assert re.match(K["drgx"], dstr)


# -----------------------------------------------------------------------------
def test_backup_default_strftime(tmpdir, td, fx_chdir):
    """
    Verify that backup=('.%Y%b%d', 'load') does the right thing
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(K["ymdf"], K["load"]))
    fl = glob_assert("*", 2)
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(K["ymd_rgx"], left)
    q.quit()


# -----------------------------------------------------------------------------
def test_backup_default_strftime_q(tmpdir, td, fx_chdir):
    """
    Verify that backup=('.%Y.%m%d.%H%M%S') behaves as expected
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(K["dfmt"], K["save"]))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(K["drgx"], left)


# -----------------------------------------------------------------------------
def test_backup_extension(tmpdir, td, fx_chdir):
    """
    Verify that backup='extension' works. (Can't use 'save' or 'load' as a file
    name extension, but '.save' or '.load' should work.)
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=K["dfid"])
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert left == K["dfid"]


# -----------------------------------------------------------------------------
def test_backup_extension_q(tmpdir, td, fx_chdir):
    """
    Verify that backup='extension' works when passed to .quit(). (Can't use
    'save' or 'load' as a file name extension, but '.save' or '.load' should
    work.)
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
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(K["wump"], alt_backup))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert K["abm"] + K["wump"] in fl


# -----------------------------------------------------------------------------
def test_backup_func_ymd(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, '%Y%b%d') calls function('%Y%b%d') at save
    time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, K["ymdf"]))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert K["abm"] + K["ymdf"] in fl


# -----------------------------------------------------------------------------
def test_backup_func_ymd_load(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, '%b%y%H', 'load') calls function('%b%y%H') at
    load time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, K["ymdf"], K["load"]))
    fl = glob_assert("*", 2)
    assert K["abm"] + K["ymdf"] in fl
    q.quit()
    fl = glob_assert("*", 2)


# -----------------------------------------------------------------------------
def test_backup_func_ymd_save(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, '%b%y%H', 'save') calls function('%b%y%H') at
    save time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, K["ymdf"], K["save"]))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert K["abm"] + K["ymdf"] in fl


# -----------------------------------------------------------------------------
def test_backup_load(tmpdir, td, fx_chdir):
    """
    Verify that backup='load' makes the backup happen at load time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=K["load"])
    fl = glob_assert("*", 2)
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(K["drgx"], left)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl


# -----------------------------------------------------------------------------
def test_backup_load_ext(tmpdir, td, fx_chdir):
    """
    Verify that backup=('load', '.ext') makes the backup happen at load time
    and uses the specified extension.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(K["load"], K["froo"]))
    fl = glob_assert("*", 2)
    assert td.basename in fl
    assert td.basename + K["froo"] in fl
    q.quit()
    fl = glob_assert("*", 2)


# -----------------------------------------------------------------------------
def test_backup_load_func(tmpdir, td, fx_chdir):
    """
    Verify that backup=(function, 'load') runs function at load time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(alt_backup, K["load"]))
    fl = glob_assert("*", 2)
    assert K["abm"] + K["dfmt"] in fl
    q.quit()
    fl = glob_assert("*", 2)


# -----------------------------------------------------------------------------
def test_backup_save(tmpdir, td, fx_chdir):
    """
    Verify that backup='save' delays the backup time to when .quit() is called.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=K["save"])
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename in fl
    [other] = [x for x in fl if x != td.basename]
    left = other.replace(td.basename, '')
    assert re.match(K["drgx"], left)


# -----------------------------------------------------------------------------
def test_backup_save_ext(tmpdir, td, fx_chdir):
    """
    Verify that backup=('.ext', 'save') makes the backup at save time with .ext
    as the extension on the backup file.
    """
    pytest.debug_func()
    ext = K["bkup"]
    q = editor.editor(td.basename, backup=(K["save"], ext))
    fl = glob_assert("*", 1)
    assert td.basename in fl
    q.quit()
    fl = glob_assert("*", 2)
    assert td.basename + ext in fl


# -----------------------------------------------------------------------------
def test_backup_save_func(tmpdir, td, fx_chdir):
    """
    Verify that backup=('save', function) runs function at save time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename, backup=(K["save"], alt_backup))
    fl = glob_assert("*", 1)
    q.quit()
    fl = glob_assert("*", 2)
    assert K["abm"] + K["dfmt"] in fl


# -----------------------------------------------------------------------------
def test_backup_save_func_q(tmpdir, td, fx_chdir):
    """
    Verify that backup=('save', function) passed to .quit() runs function at
    save time.
    """
    pytest.debug_func()
    q = editor.editor(td.basename)
    fl = glob_assert("*", 1)
    q.quit(backup=(K["save"], alt_backup))
    fl = glob_assert("*", 2)
    assert K["abm"] + K["dfmt"] in fl


# -----------------------------------------------------------------------------
def test_backup_function(tmpdir, td, backup_reset):
    """
    Verifies that the backup function gets called and that we can specify an
    alternate backup function.
    """
    pytest.debug_func()
    assert not hasattr(squawker, K['called'])
    q = editor.editor(td.filename.strpath, backup=squawker)
    assert not hasattr(squawker, K['called'])
    q.quit()
    assert hasattr(squawker, K['called']) and squawker.called


# -----------------------------------------------------------------------------
def test_closed(td):
    """
    Verifies that a closed editor object will throw an error if we try to do
    something with it that depends on an open editor object.
    """
    pytest.debug_func()
    q = editor.editor(filepath=td.filename.strpath)
    q.quit()
    with pytest.raises(editor.Error) as err:
        q.quit()
    assert K["closed"] in str(err)


# -----------------------------------------------------------------------------
def test_delete(td):
    """
    Verifies that <editor>.delete() removes matching lines
    """
    pytest.debug_func()
    q = editor.editor(filepath=td.filename.strpath)
    rmd = q.delete(K["stst"])
    q.quit()
    backup = py.path.local(q.backup_filename())

    assert q.closed
    assert K["orig_l"][1] in [_.strip() for _ in rmd]
    assert K["orig_l"][3] in rmd
    assert len(rmd) == 2
    assert backup.exists()
    assert td.filename.exists()
    assert K["orig_l"][1] not in td.filename.read()
    assert K["orig_l"][3] not in td.filename.read()


# -----------------------------------------------------------------------------
def test_dos(tmpdir, td):
    """
    Verifies that specifying newline='\r\n' in the .quit() call uses CR-LF to
    separate lines in the output file.

    We have to .read_binary() the file to see the \r. Calling .read()
    apparently converts \r\n to just \n. We put the expected value in a
    bytearray based on a utf8 string.
    """
    pytest.debug_func()
    q = editor.editor(td.filename.strpath)
    q.append(K["new"])
    q.quit(newline=K["crlf"])
    backup = py.path.local(q.backup_filename())
    assert backup.exists()
    assert td.filename.exists()
    assert written_format(K["orig_l"]) in backup.read()
    assert K["new"] not in backup.read()
    exp = bytearray(written_format(K["orig_l"] + [K["new"]],
                                   newline=K["crlf"]), 'utf8')
    actual = td.filename.read_binary()
    assert exp == actual


# -----------------------------------------------------------------------------
def test_init_content():
    """
    Verify that the constructor will take a list of strings or a single string
    for the content argument.
    """
    pytest.debug_func()
    a = editor.editor(content=K["orig_l"])
    assert a.buffer == K["orig_l"]
    strinp = "".join([_ + "\n" for _ in K["orig_l"]])
    b = editor.editor(content=strinp)
    assert b.buffer == K["orig_l"]


# -----------------------------------------------------------------------------
def test_insert(tmpdir, td):
    """
    Verify that we can insert new lines at specific spots in the editor buffer
    """
    pytest.debug_func()
    q = editor.editor(td.filename.strpath)
    edited = K["orig_l"][:]
    q.insert(K["before"])
    edited.insert(0, K["before"])
    assert q.buffer == edited

    q.insert(K["after"], len(q))
    edited.insert(len(edited), K["after"])
    assert q.buffer == edited

    q.insert(K["middle"], 3)
    edited.insert(3, K["middle"])
    assert q.buffer == edited

    q.quit()
    assert written_format(edited) == td.filename.read()


# -----------------------------------------------------------------------------
def test_newfile(tmpdir):
    """
    Verifies that we can build the contents of a file in an editor object by
    appending a line at a time.
    """
    pytest.debug_func()
    init = K["frst"]
    last = K["last"]
    stem = tmpdir.join(K["nwfl"])
    assert len(tmpdir.listdir()) == 0
    q = editor.editor(filepath=stem.strpath, content=[init])
    for _ in K["orig_l"]:
        q.append(_)
    q.append(last)
    q.quit(filepath=stem.strpath)
    exp = written_format([init] + K["orig_l"] + [last])
    assert exp == stem.read()


# -----------------------------------------------------------------------------
def test_overwrite_fail(tmpdir, td):
    """
    Verifies that specifying contents for an existing file throws an exception
    """
    pytest.debug_func()
    with pytest.raises(editor.Error) as err:
        q = editor.editor(filepath=td.filename.strpath,  # noqa: F841
                          content=[K["before"], K["middle"], K["after"]])
    assert td.filename.strpath in str(err)
    assert K["ovwr"] in str(err)
    assert K["err"] in repr(err)


# -----------------------------------------------------------------------------
def test_overwrite_recovery(tmpdir, td):
    """
    What this test verifies is that whatever is in the original file at save
    time gets copied to the backup file, even if it isn't the original content.
    Whatever is in the editor buffer gets written out to the original file.
    """
    pytest.debug_func()
    q = editor.editor(td.filename.strpath)
    assert K["orig_l"] == q.buffer
    td.filename.write(written_format(K["ovwr_l"]))
    q.quit()
    backup = py.path.local(q.backup_filename())
    assert backup.exists()
    assert td.filename.exists()
    assert written_format(K["ovwr_l"]) == backup.read()
    assert written_format(K["orig_l"]) == td.filename.read()


# -----------------------------------------------------------------------------
def test_qbackup(tmpdir, td, backup_reset):
    """
    Verifies that an alternate backup routine can be called with argument to
    quit() method
    """
    pytest.debug_func()
    try:
        del squawker.called
    except AttributeError:
        pass
    q = editor.editor(td.filename.strpath, backup=squawker)
    q.quit(backup=altbackup)
    assert not hasattr(squawker, K['called'])
    assert hasattr(altbackup, K['called']) and altbackup.called


# -----------------------------------------------------------------------------
def test_substitute(tmpdir, td):
    """
    Verifies that with a change to every line in the editor buffer, .quit()
    writes that edited text to the original file and the original text to the
    backup file.
    """
    pytest.debug_func()
    q = editor.editor(td.filename.strpath)
    assert K["orig_l"] == q.buffer
    q.sub(K["lowe"], K["uppE"])
    q.quit()
    backup = py.path.local(q.backup_filename())
    assert backup.exists()
    assert td.filename.exists()
    assert written_format(K["orig_l"]) == backup.read()
    exp = written_format([_.replace(K["lowe"], K["uppE"])
                          for _ in K["orig_l"]])
    assert exp == td.filename.read()


# -----------------------------------------------------------------------------
def test_substitute_limit(tmpdir, td):
    """
    Verify that we can pass a number to sub as the third argument that will
    limit the number of substitutions
    """
    pytest.debug_func()
    q = editor.editor(td.filename.strpath)
    q.sub(K["lowa"], K["uppA"], 1)
    q.quit()
    exp = written_format([_.replace(K["lowa"], K["uppA"], 1)
                          for _ in K["orig_l"]])
    assert exp == td.filename.read()


# -----------------------------------------------------------------------------
def test_trailing_whitespace(tmpdir, td):
    """
    Detects the bug where trailing whitespace on the last line of the file is
    lost because of the rstrip() in <editor>.contents()
    """
    pytest.debug_func()

    K["orig_l"][-1] += K["whsp"]
    wws = tmpdir.join(K["with"])
    wws.write(written_format(K["orig_l"]))

    q = editor.editor(wws.strpath)
    assert K["orig_l"] == q.buffer


# -----------------------------------------------------------------------------
def test_version():
    """
    Checks the version
    """
    result = editor.editor.version()
    assert re.match("\d+\.\d+\.\d+", result)


# -----------------------------------------------------------------------------
def test_wtarget_none():
    """
    Verifies that attempting to quit an editor object with no file name
    established throws an exception
    """
    pytest.debug_func()
    q = editor.editor(content=[K["one"], K["two"]])
    with pytest.raises(editor.Error) as err:
        q.quit()
    assert K["miss"] in str(err)


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
    filename = K["abm"] + ext
    open(filename, 'w').close()


# -----------------------------------------------------------------------------
def contents(path):
    """
    Return the contents of *path* as a string
    """
    with open(path, 'r') as inp:
        rval = inp.read()
    return rval


# -----------------------------------------------------------------------------
def glob_assert(globexpr, exp_count):
    """
    Given a glob expression in *globexpr*, assert that it matches *exp_count*
    entries
    """
    flist = glob.glob(globexpr)
    assert len(flist) == exp_count
    return flist


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
def fx_chdir(tmpdir):
    """
    Run the test after cd'ing to tmpdir.strpath
    """
    with tbx.chdir(tmpdir.strpath):
        yield


# -----------------------------------------------------------------------------
@pytest.fixture
def td(tmpdir):
    """
    Adds newlines to the test data at appropriate spots and writes the result
    to a file in tmpdir
    """
    td.filename = tmpdir.join("testfile")
    td.filename.write(written_format(K["orig_l"]))
    td.basename = td.filename.basename
    return td
