from enum import Enum, unique

@unique
class ImageBackendType(Enum):
    GTK = 1,
    QT = 2

class ImageBackend(object):
    def __init__(self):
        pass

    @staticmethod
    def get(backendType):
        if backendType == ImageBackendType.GTK:
            import g.core.imagebackendgtk
            return g.core.imagebackendgtk.ImageBackend()
        elif backendType == ImageBackendType.QT:
            raise NotImplementedError('QT backend not implemented yet')
        else:
            if backendType not in ImageBackendType:
                raise ValueError('Unknown backend type')
            else:
                raise NotImplementedError()

    @staticmethod
    def fromFilePath(path):
        raise NotImplementedError()


