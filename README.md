# editor - manipulate files

Example uses:

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
        # no backup file is written

    Save to a different file

        import editor
        q = editor.editor('file_one')
        ...
        q.quit(filepath='file_two')
        # backup written to file_two.YYYY.mmdd.HHMMSS

    Create a new file

        import editor
        q = editor.editor(['line 1', 'line 2'])
        q.append('This is a line')
        q.append('Another line')
        ...
        q.quit(filepath='newfile')

    Change line terminator to \r\n

        import editor
        q = editor.editor('unixfile')
        q.quit(save=True, filepath='dosfile', newline='\r\n')
