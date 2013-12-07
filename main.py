import sys
from PyQt4.QtGui import QApplication
from app import Application
from mainwindow import MainWindow


def main():
    qapp = QApplication(sys.argv)
    window = MainWindow(Application())
    window.show()
    sys.exit(qapp.exec_())


if __name__ == '__main__':
    main()
