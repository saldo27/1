from cli import run_cli
import sys
from PySide6.QtWidgets import QApplication
from gui import MainWindow

if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print("QApplication instance already exists.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
