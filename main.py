from ui_interface import *
from Custom_Widgets.Widgets import *
import os
import sys

# Main Window Class
class MainWindow(QMainWindow):
    def __init__(self, parent=None):        
        
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # APPLY JSON STYLESHEET
        loadJsonStyle(self, self.ui)

        # Show Window
        self.show()

        # Expand center widget size
        self.ui.calibrationBtn.clicked.connect(
            lambda: self.ui.centerMenuContainer.expandMenu())
        self.ui.helpBtn.clicked.connect(
            lambda: self.ui.centerMenuContainer.expandMenu())

        # Close center widget size
        self.ui.closeCenterMenuBtn.clicked.connect(
            lambda: self.ui.centerMenuContainer.collapseMenu())

        # Expand right widget size
        self.ui.extruderConectBtn.clicked.connect(
            lambda: self.ui.rightMenuContainer.expandMenu())
        self.ui.HVConectBtn.clicked.connect(
            lambda: self.ui.rightMenuContainer.expandMenu())
        self.ui.stageConectBtn.clicked.connect(
            lambda: self.ui.rightMenuContainer.expandMenu())

        # Close right widget size
        self.ui.closeRightMenuBtn.clicked.connect(
            lambda: self.ui.rightMenuContainer.collapseMenu())

# Execute APP
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())