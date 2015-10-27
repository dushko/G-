class Tree(object):
    def __init__(self, name, parent=None):
        assert(type(parent) != str)
        if type(parent) == str:
            pass

        self.parent = parent
        self.children = []
        self.name = name

    def addChild(self, child):
        ch = Tree(child, self)
        self.children.append(ch)
        return ch

    def addChildren(self, children):
        self.children.extend(children)

    def print(self, space=2):
        def dfs(tree, depth):
            print(' '*space*depth + tree.name)
            for c in tree.children:
                dfs(c, depth + 1)
        dfs(self, 0)

    def getFullPath(self):
        path = [self.name]
        p = self.parent
        while p is not None:
            path.insert(0, p.name)
            p = p.parent
        return '/'.join(path)

    def __str__(self):
        return "Tree['%s']" % self.name