"""manipulate files

Examples:

    Age out a file in favor of a new version

        import editor
        q = editor.editor('/path/to/file')
        # file is changed or overwritten
        q.quit()
        # quit() writes old version to /path/to/file.YYYY.mmdd.HHMMSS

    Add a line to the end of a file

        import editor
        q = editor.editor('filename')
        q.append('This is a new line')
        q.quit(save=True)

    Change every line in the file

        import editor
        q = editor.editor('filename')
        q.sub('foo', 'bar')
        q.quit()            # save=True by default

    Abort an edit

        import editor
        q = editor.editor('filename')
        q.sub('good stuff', 'bad stuff')     # oops!
        q.quit(save=False)

    Save to a different file

        import editor
        q = editor.editor('file_one')
        ...
        q.quit(filepath='file_two')

    Create a new file

        import editor
        q = editor.editor(['line 1', 'line 2'])
        q.append('This is a line')
        q.append('Another line')
        ...
        q.quit(filepath='newfile')

    Change file to \r\n line terminator

        import editor
        q = editor.editor('unixfile')
        q.quit(save=True, filepath='dosfile', newline='\r\n')

"""
import os
import re
import shutil
import time

class editor(object):
    # -------------------------------------------------------------------------
    def __init__(self, filepath=None, content=[], backup=None, newline='\n'):
        """
        If *filepath* is None, we're creating a new file. The caller will have to
        specify a filepath when calling quit().

        If *filepath* names a file but the file does not exist, it will be
        written if quit is called with save=True.

        In either of the above cases, *content* can be a list of lines to go into
        the file.

        If *filepath* names a file that exists and *content* is empty, we
        will load the contents of the file into this object.

        If *filepath* names a file that exists and *content* is not empty, we
        will throw an exception.

        *backup* can point to a function that will be called as

            backup(*filepath*)

        just before the new content is written to the file.

        File content is held as a list of lines. Line terminators from the file
        are left in the content until we're ready to write the data out. The
        default line terminator is '\n'. This can be overridden using the
        *newline* argument on the constructor or on quit().
        """
        self.filepath = filepath
        self.buffer = content
        self.closed = False
        self.newline = newline
        if backup:
            self.backup = backup

        if self.filepath is None:
            return
        if not os.path.exists(self.filepath):
            return
        if self.buffer:
            raise Error("""%s exists. To overwrite it,
                f = editor('path')
                f.add(...)
                f.update(...)
                f.quit(save=True)
            """)
        else:
            self.buffer = self.contents(self.filepath)


    # -------------------------------------------------------------------------
    def append(self, line):
        """
        Add *line* to the end of the file
        """
        self.buffer.append(line)


    # -------------------------------------------------------------------------
    def backup(self, filepath):
        """
        This default backup routine will copy *filepath* to, for example,
        *filepath*~2015.0112.093715
        """
        ts = time.strftime("~%Y.%m%d.%H%M%S")
        shutil.copy2(filepath, filepath + ts)


    # -------------------------------------------------------------------------
    def contents(self, filepath):
        """
        Read a file and return its contents as a list
        """
        f = open(filepath, 'r')
        self.buffer = f.readlines()
        f.close()


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

        wtarget = filepath or self.filepath

        if wtarget is None:
            raise Error("No filepath specified, content will be lost")
        elif os.path.exists(wtarget):
            if backup:
                backup(wtarget)
            else:
                self.backup(wtarget)

        nl = newline or self.newline
        out = open(wtarget, 'w')
        out.writelines([l.rstrip('\r\n') + nl for l in self.buffer])
        out.close()

    # -------------------------------------------------------------------------
    def sub(self, rgx, repl):
        """
        Replace matches of *rgx* with *repl* on each line in the file
        """
        newbuf = [re.sub(rgx, repl, line) for line in self.buffer]
        self.buffer = newbuf


# -----------------------------------------------------------------------------
class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
