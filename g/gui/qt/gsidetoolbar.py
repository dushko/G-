from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt5.QtCore import pyqtSignal


class GSideToolbar(QWidget):
    selectionChange = pyqtSignal(str)

    def __init__(self, buttons):
        super().__init__()

        self.buttons = {}
        self.selectedId = None

        self.mainLayout = QVBoxLayout(self)

        for button in buttons:
            button = QPushButton(button[0])
            self.mainLayout.addWidget(button)

        self.mainLayout.addStretch()

    def buttonState(self, state):
        pass

    @staticmethod
    def createButton(text, icon):
        pass

