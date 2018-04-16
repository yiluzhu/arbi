from PySide.QtCore import QCoreApplication
from PySide.QtGui import QApplication


def set_qapp():
    if not QCoreApplication.instance():
        app = QApplication([])
        return app


def simplify_dict(result, kept_keys):
    unneeded_keys = [key for key in result.keys() if key not in kept_keys]
    for key in unneeded_keys:
        result.pop(key)

    return result
