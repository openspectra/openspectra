import sys
from PyQt5.QtWidgets import QApplication
from openspectra.ui.openspectra_ui import OpenSpectraUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    os = OpenSpectraUI()
    sys.exit(app.exec_())