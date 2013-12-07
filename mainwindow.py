# -*- coding: utf-8 -*-
from PyQt4.QtGui import QMainWindow
from ui_mainwindow import Ui_MainWindow
import model
import PyQt4


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.app = app
        self.pbEvent.clicked.connect(self.onBtnEvent)
        self._model = None

    def onBtnEvent(self):
        self.teLog.clear()
        self.teCars.clear()
        gen_exp = float(self.leGenExpVal.text())
        proc_exp = float(self.leProcExpVal.text())
        proc_half = float(self.leProcDiap.text())
        petrol_rows_num = int(self.leRowsNum.text())
        petrol_stations = int(self.leStationsInRowNum.text())
        m = model.Model(gen_exp, proc_exp, proc_half, petrol_stations, petrol_rows_num)
        m.run_event(int(self.leCarsNum.text()))
        for l in m.get_logs():
            self.teLog.appendPlainText(l)
            PyQt4.QtGui.QApplication.processEvents()
        for l in m.get_cars():
            self.teCars.appendPlainText(repr(l))
            PyQt4.QtGui.QApplication.processEvents()
        self.lblAvgTimeInQueue.setText("Среднее время машины в очереди на заправку: %f" % m.get_avg_time_in_queue())
        self.lblAvgTimeToLeave.setText("Среднее время машины в очереди на выезд: %f" % m.get_avg_time_to_leave())
        self.lblFreedTime.setText("Ожидание машины: %f колонко*времени" % m.get_time_freed())
        self.lblWastedTime.setText("Ожидание на выезд: %f колонко*времени" % m.get_time_complete())
        self.lblModelingTime.setText("Время моделирования: %f" % m.get_modeling_time())
