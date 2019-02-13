#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import sys
from PyQt5.QtWidgets import QApplication
from openspectra.ui.openspectra_ui import OpenSpectraUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    os = OpenSpectraUI()
    sys.exit(app.exec_())
