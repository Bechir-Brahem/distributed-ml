
class Task:
    # TODO: change bad name

    def __init__(self, filetype=None, filename=None, filesize=None):
        """
        :param filetype:  'X' for input, 'Y' for target
        :param filename:
        :param filesize:
        """
        self.filetype = filetype
        self.filename = filename
        self.filesize = filesize
        self.filepath=None
