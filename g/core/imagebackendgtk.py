from gi.repository import GdkPixbuf

from g.core.imagebackend import ImageBackend


class ImageBackendGtk(ImageBackend):
    def __init__(self):
        ImageBackend.__init__()

    @staticmethod
    def fromFilePath(path):
        pixBuf = GdkPixbuf.Pixbuf.new_from_file(path)
        return pixBuf

