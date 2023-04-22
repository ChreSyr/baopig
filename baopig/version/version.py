

class BaopigVersion(tuple):
    """Code from pygame.version.PygameVersion"""
    __slots__ = ()
    fields = 'major', 'minor', 'patch', 'backup'

    def __new__(cls, major, minor, patch, backup=None):
        return tuple.__new__(cls, (major, minor, patch) + tuple([backup] if backup else ()))

    def __repr__(self):
        fields = ('{}={}'.format(fld, val) for fld, val in zip(self.fields, self))
        return '{}({})'.format(str(self.__class__.__name__), ', '.join(fields))

    def __str__(self):
        return '{}.{}.{}'.format(*self) if len(self) == 3 else '{}.{}.{} - {}'.format(*self)

    major = property(lambda self: self[0])
    minor = property(lambda self: self[1])
    patch = property(lambda self: self[2])


version = BaopigVersion(0, 20, 5)

if __name__ == "__main__":
    # TODO : try to access baopig.version without creating application, threads...
    print("Hello, this is baopig version", version)
