#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import sys
from PyQt5.QtWidgets import QApplication
from openspectra.ui.openspectra_ui import OpenSpectraUI

if __name__ == '__main__':
    return_val = 0
    app = QApplication(sys.argv)
    try:
        os = OpenSpectraUI()
        return_val = app.exec_()
    except:
        print("Uncaught exception {0}".format(sys.exc_info()[0]))
    finally:
        print("Terminating with value {0}".format(return_val))
        sys.exit(return_val)
