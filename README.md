# editor - manipulate files

### Example uses:

#### Load an existing file

        import editor
        q = editor.editor('/path/to/file')
        # q.buffer is a list of lines from the file
        # optionally change the object contents
        q.quit()       # save is True by default

#### Create an editor object with new content

        q = editor.editor(content=['First line',
                                   'Second line',
                                   'Third line'])

NOTE: If the constructor is called with the path of an existing file and
also new content, an exception is thrown.

#### Backups

##### Backup on save (default behavior)

        q = editor.editor('/path/to/file')

Original file will be copied to backup when q.quit() is called*.

##### Backup on load

        q = editor.editor('/path/to/file', backup='load')

Original file will be copied to backup when constructor is called.

##### Backup using alternate function

        q = editor.editor('/path/to/file', backup=function_name)

The function will be called when q.quit() is called*.

##### Backup using alternate function at laod time

        q = editor.editor('/path/to/file', backup=('load', function_name)

##### Name of backup file

By default, the name of the backup file will be the original filename with
the date and time of the backup appended (e.g., file.YYYY.mmdd.HHMMSS).
Alternate backup file extensions can be specified by providing a string in
the backup argument.

        q = editor.editor('/path/to/file', backup='~')

Backup file name would be 'file~', written at quit time.

        q = editor.editor('/path/to/file', backup=('load', '.%Y.%b.%d'))

Backup file name would be 'file.YYYY.mmm.dd', written at load time.

The backup argument can also be passed to the .quit() method. Of course, if
we tell the constructor to backup on load and also tell quit() to backup on
save, both triggers will fire and backup the file twice.

* When q.quit() is called, argument save has a default value of True. If
  'save=False' is specified, no backup routine will be called at quit time.


#### Add a line to the end of a file

        import editor
        q = editor.editor('filename')
        q.append('This is a new line')
        q.quit(save=True)

#### Change every line in the file

        import editor
        q = editor.editor('filename')
        q.sub('foo', 'bar')
        q.quit()            # save=True by default

#### Abort an edit

        import editor
        q = editor.editor('filename')
        q.sub('good stuff', 'bad stuff')     # oops!
        q.quit(save=False)
        # no backup file written at quit

#### Save to a different file

        import editor
        q = editor.editor('file_one')
        ...
        q.quit(filepath='file_two')
        # backup written to file_two.YYYY.mmdd.HHMMSS

#### Create a new file

        import editor
        q = editor.editor(content=['line 1', 'line 2'])
        q.append('This is a line')
        q.append('Another line')
        ...
        q.quit(filepath='newfile')

#### Change line terminator to \r\n

        import editor
        q = editor.editor('unixfile')
        q.quit(save=True, filepath='dosfile', newline='\r\n')
