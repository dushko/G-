import sys

from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QMainWindow

from g.gui.qt.gsidetoolbar import GSideToolbar


class MainWindow(QMainWindow):
    def __init__(self, *args, parent=None):
        super(MainWindow, self).__init__()

        loadUi('data/mainwindow.ui', self)

        leftToolbarButtons = [['albums', 'Albums', 'image'],
                ['tags', 'Tags', 'accessories-text-editor']]
        rightToolbarButtons = [['properties', 'Properties', 'image'],
                ['metadata', 'Metadata', 'image']]
        self.leftSideToolbar = GSideToolbar(leftToolbarButtons)
        self.rightSideToolbar = GSideToolbar(rightToolbarButtons)

        self.centralLayout.insertWidget(-1, self.rightSideToolbar)
        self.centralLayout.insertWidget(0, self.leftSideToolbar)



    @staticmethod
    def start(*args):
        app = QApplication(sys.argv)

        w = MainWindow(args)
        w.show()

        sys.exit(app.exec_())
