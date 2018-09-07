"""
Manipulate files programmatically
"""
from datetime import datetime as dt
import os
import re
import shutil
import subprocess
import tempfile
import types


from editor import version


class editor(object):
    # -------------------------------------------------------------------------
    def __init__(self, filepath=None, content=[], backup=None, newline='\n'):
        """
        If *filepath* is None, we're creating a new file. The caller will have
        to specify a filepath when calling quit().

        If *filepath* names a file but the file does not exist, it will be
        written if quit is called with save=True.

        In either of the above cases, *content* can be a list of lines to go
        into the file.

        If *filepath* names a file that exists and *content* is empty, we
        will load the contents of the file into this object.

        If *filepath* names a file that exists and *content* is not empty, we
        will throw an exception.

        *backup* can point to a function that will be called as

            backup(*filepath*)

        just before the new content is written to the file.

        File content is held as a list of lines. Line terminators from the file
        are removed from the content at load time. The default line terminator
        is '\n', however, this can be overridden using the *newline* argument
        on the constructor or on quit().
        """
        self.filepath = filepath
        self.newline = newline
        if isinstance(content, str):
            self.buffer = content.rstrip(self.newline).split(self.newline)
        else:
            self.buffer = content
        self.closed = False
        self.backup = {}
        self.backup_setup(backup)

        if self.filepath is None:
            return
        if not os.path.exists(self.filepath):
            return
        if self.buffer:
            raise Error("""{0} exists. To overwrite it,
                f = editor('path')
                f.add(...)
                f.update(...)
                f.quit(save=True)
            """.format(self.filepath))
        else:
            self.buffer = self.contents(self.filepath)
            if self.backup['when'] == 'load':
                self.backup['func'](self.backup['ext'])

    # -------------------------------------------------------------------------
    def __len__(self):
        """
        Return the length of the buffer
        """
        return len(self.buffer)

    # -------------------------------------------------------------------------
    def append(self, line):
        """
        Add *line* to the end of the file
        """
        self.buffer.append(line)

    # -------------------------------------------------------------------------
    def backup_filename(self):
        """
        Return the backup filename if one has been set, otherwise None
        """
        if hasattr(self, "_backup_filename"):
            return self._backup_filename
        else:
            return None

    # -------------------------------------------------------------------------
    def backup_setup(self, backup):
        """
        *backup* may be 'load', 'save', extension string, a function pointer,
        or a tuple containing a combination of these (except that 'load' and
        'save' are mutually exclusive).
        """
        def bs_resolve(val):
            if val == 'load':
                self.backup['when'] = val
            elif val == 'save':
                pass
            elif isinstance(val, types.FunctionType):
                self.backup['func'] = val
            elif isinstance(val, str):
                self.backup['ext'] = val

        self.backup['when'] = 'save'
        self.backup['func'] = self.default_backup
        self.backup['ext'] = ".%Y.%m%d.%H%M%S"
        self.backup['filepath'] = self.filepath

        if isinstance(backup, tuple):
            for item in backup:
                bs_resolve(item)
        else:
            bs_resolve(backup)

    # -------------------------------------------------------------------------
    @staticmethod
    def contents(filepath):
        """
        Read a file and return its contents as a list. \n and \r are removed
        from the end of each line.
        """
        f = open(filepath, 'r')
        rval = [x.rstrip("\r\n") for x in f.readlines()]
        f.close()
        return rval

    # -------------------------------------------------------------------------
    def default_backup(self, ext):
        """
        This default backup routine will copy *filepath* to, for example,
        *filepath*~2015.0112.093715
        """
        ts = dt.now().strftime(ext)
        self._backup_filename = self.backup['filepath'] + ts
        shutil.copy2(self.backup['filepath'], self._backup_filename)

    # -------------------------------------------------------------------------
    def delete(self, rgx):
        """
        Delete lines that match the regex *rgx*. Return the lines removed.
        """
        newbuf = [l for l in self.buffer if not re.search(rgx, l)]
        rval = [l for l in self.buffer if re.search(rgx, l)]
        self.buffer = newbuf
        return rval

    # -------------------------------------------------------------------------
    def edit(self):
        """
        Edit the file in the user's default command line editor
        """
        _, tmp = tempfile.mkstemp()
        with open(tmp, 'w') as f:
            f.write("".join([x + self.newline for x in self.buffer]))
        cledit = os.getenv('EDITOR') or 'vi'
        p = subprocess.Popen([cledit, tmp])
        p.wait()
        buffer = editor.contents(tmp)
        if not buffer:
            return
        else:
            self.buffer = buffer

    # -------------------------------------------------------------------------
    def insert(self, line, where=0):
        """
        Insert *line* after line *where*
        """
        self.buffer.insert(where, line)

    # -------------------------------------------------------------------------
    def quit(self, save=True, filepath=None, backup=None, newline=None):
        """
        If *save* is False, the file is abandoned.

        Otherwise, if *filepath* is None, the edited object content will be
        written to self.filepath after the current version of the file is
        backed up.

        If *backup* is not None, it should be a routine that will take care of
        backing up the original file. If *backup* is None, self.backup will be
        used.

        If *newline* is specified, its value will be used as the line
        terminator.
        """
        if self.closed:
            raise Error("This file is already closed")

        self.closed = True
        if not save:
            return

        if backup:
            self.backup_setup(backup)

        wtarget = filepath or self.filepath

        if wtarget is None:
            raise Error("No filepath specified, content will be lost")
            self.closed = False
        elif os.path.exists(wtarget) and self.backup['when'] == 'save':
            self.backup['func'](self.backup['ext'])

        nl = newline or self.newline
        out = open(wtarget, 'w')
        out.writelines([l + nl for l in self.buffer])
        out.close()

    # -------------------------------------------------------------------------
    def sub(self, rgx, repl, count=0):
        """
        Replace matches of *rgx* with *repl* on each line in the file
        """
        count = max(count, 0)
        newbuf = [re.sub(rgx, repl, line, count) for line in self.buffer]
        self.buffer = newbuf

    # -------------------------------------------------------------------------
    @classmethod
    def version(cls):
        return version.__version__


# -----------------------------------------------------------------------------
class Error(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
