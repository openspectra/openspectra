#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import sys
import traceback

from PyQt5.QtWidgets import QApplication
from openspectra.ui.openspectra_ui import OpenSpectraUI
from openspectra.utils import OpenSpectraProperties

if __name__ == '__main__':
    return_val = 0

    # trigger configuration properties to load
    OpenSpectraProperties.get_property(None, None)

    app = QApplication(sys.argv)
    try:
        os = OpenSpectraUI()
        return_val = app.exec_()
    except:
        info = sys.exc_info()
        print("Uncaught exception:\n{0}: {1}".format(info[0], info[1]))
        traceback.print_tb(info[2], file=sys.stdout)
    finally:
        print("Terminating with value {0}".format(return_val))
        sys.exit(return_val)
