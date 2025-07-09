""" Frogrance Smart (Digital Scent) """
import os
import sys
import json
import struct
# import xlsxwriter
import serial
import random

from datetime import datetime

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtTest
from PySide6 import QtWidgets

# from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import Qt, QCoreApplication, QTimer
from PySide6.QtCore import Signal #Slot
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget, QTableWidgetItem, QScroller, QAbstractItemView

import dsSerial
import dsComm
import dsImage, dsSound, dsText, dsStyle, dsNum
import dsSetting
import dsQRcode

import testModel

# from dsImage import dsBtnImg, dsBgImg, dsResultImg
# from dsUiChartWidget import scentPieChartWidget, scentLineChartWidget
from dsUiCustom import scentSlider

os.environ["PYSIDE_DESIGNER_PLUGINS"] = "."
# __platform__ = sys.platform

# UI 관리 클래스
class UiDlg(QWidget):

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def __init__(self):
        super().__init__()
        # 시리얼 통신 수신 설정
        self.setSerialReadThread()
        # 시작시 설정 반영
        self.loadSettingsFile()

    # 다이얼로그 종료시 오류 해결
    def closeEvent(self, event):
        self.deleteLater()
    
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 시리얼 통신 설정 (Signal, Thread, Read, Write, Console지정)
    _serial_received_data = Signal(bytes, name="serialReceivedData")

    def setSerialReadThread(self):
        self._serial = serial.Serial()
        self._serial_read_thread = dsSerial.SerialReadThread(self._serial)
        self._serial_read_thread._serial_received_data.connect(lambda v: self._serial_received_data.emit(v))
        self._serial_received_data.connect(self.readSerialData)
        self._serial_read_thread.start(QtCore.QThread.Priority.HighestPriority)
    
    def readSerialData(self, rdata):
        self._serial_console.append("RX(%d):"%len(rdata) + str(rdata.hex()))
        self._serial_console.moveCursor(QtGui.QTextCursor.End)
        print("RX(%d):"%len(rdata) + str(rdata.hex()))
        self.parseReadData(rdata)

    def write_data(self, wdata):
        if dsSerial._is_open(self._serial):
            self._serial.write(wdata)
            self._serial_console.append("TX(%d):"%len(wdata) + str(wdata.hex()))
            self._serial_console.moveCursor(QtGui.QTextCursor.End)
            print("TX(%d):"%len(wdata) + str(wdata.hex()))
        else:
            self._serial_console.append(dsText.serialText['status_close'])
            self._serial_console.moveCursor(QtGui.QTextCursor.End)
            print(dsText.serialText['status_close'])

    def setSerialConsole(self, text_console):
        self._serial_console = text_console

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 창 모양
    def setWindowBySetting(self, dialog):
        dialog.setWindowFlags(Qt.WindowType.Window)
        # if dsSetting.dsParam['window_bars_onoff'] != 1:
        #     dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # if dsSetting.dsParam['front_onoff'] == 1:
        #     dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    # 테이블 스크롤러 설정
    def setScroller(self, widget):
        scroller = QScroller.scroller(widget)
        scroller.grabGesture(widget, QScroller.LeftMouseButtonGesture)
    
    # 창 위치 업데이트
    def uiDlgPrevCP(self, prev_dlg):
        self.prev_cp = prev_dlg.frameGeometry().center()

    # 현재 창 위치에서 새 창으로 전환하기
    def uiDlgChange(self, prev_dlg, next_dlg):
        prev_dlg.hide()
        self.uiDlgPrevCP(prev_dlg)
        next_qr = next_dlg.frameGeometry()
        next_qr.moveCenter(self.prev_cp)
        next_dlg.move(next_qr.topLeft())
        next_dlg.show()

    # 새 창 팝업하기 (기억된 위치에서)
    def uiDlgShow(self, next_dlg):
        next_qr = next_dlg.frameGeometry()
        next_qr.moveCenter(self.prev_cp)
        next_dlg.move(next_qr.topLeft())
        next_dlg.show()

    # 팝업 창과 현재 창 2개 닫고 새 창으로 전환하기
    def uiDlgChangeWithDlg(self, prev_dlg, popup_dlg, next_dlg):
        popup_dlg.hide()
        prev_dlg.hide()
        self.uiDlgChange(prev_dlg, next_dlg)

    def uiDlgHide(self, dlg):
        dlg.hide()
    
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 시작
    def uiDlgStart(self):
        self.uiDlgInit()
        self.ui_menu_dlg.show()
        dsSound.playGuideSound('intro_menu')

    # UI 연동 호출: UI객체.objectname.이벤트(QtSignal).connect(함수명)
    def uiDlgInit(self):
        uiLoader = QUiLoader()
        # Custom Widget 등록 (승격된 위젯)
        # uiLoader.registerCustomWidget(scentSlider)
        # UI 개별 로딩
        self.uiDlgProtocol(uiLoader)
        self.uiDlgMenu(uiLoader)
        self.uiDlgSmell(uiLoader)
        self.uiDlgSmellExp(uiLoader)
        self.uiDlgFind(uiLoader)
        self.uiDlgFindLoading(uiLoader)
        self.uiDlgFindExp(uiLoader)
        self.uiDlgMix(uiLoader)
        self.uiDlgSettings(uiLoader)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 메뉴
    def uiDlgMenu(self, uiLoader):
        self.ui_menu_dlg = uiLoader.load(
            "./ui/ui_menu.ui")
        self.ui_menu_dlg.ui_menu_btn_quit.clicked.connect(
            self.uiMenuBtnQuit)
        self.ui_menu_dlg.pb_smell.clicked.connect(
            self.uiMenuPbSmell)
        self.ui_menu_dlg.pb_find.clicked.connect(
            self.uiMenuPbFind)
        self.ui_menu_dlg.pb_mix.clicked.connect(
            self.uiMenuPbMix)
        self.ui_menu_dlg.ui_menu_btn_settings.clicked.connect(
            self.uiMenuBtnSettings)
        self.ui_menu_dlg.pb_protocol.clicked.connect(
            self.uiMenuPbProtocol)
        self.setWindowBySetting(self.ui_menu_dlg)

    def uiDlgSmell(self, uiLoader):
        self.ui_smell_dlg = uiLoader.load(
            "./ui/ui_smell.ui")
        
        # 터치 스크롤
        QtWidgets.QScroller.grabGesture(self.ui_smell_dlg.scrollArea.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)

        self.ui_smell_dlg.pb_back.clicked.connect(
            self.smell_pb_back)

        self.ui_smell_dlg.pb_fr_01.clicked.connect(
            self.pb_fr_01)
        self.ui_smell_dlg.pb_fr_02.clicked.connect(
            self.pb_fr_02)
        self.ui_smell_dlg.pb_fr_03.clicked.connect(
            self.pb_fr_03)
        self.ui_smell_dlg.pb_fr_04.clicked.connect(
            self.pb_fr_04)
        self.ui_smell_dlg.pb_fr_05.clicked.connect(
            self.pb_fr_05)
        self.ui_smell_dlg.pb_fr_06.clicked.connect(
            self.pb_fr_06)
        self.ui_smell_dlg.pb_fr_07.clicked.connect(
            self.pb_fr_07)
        self.ui_smell_dlg.pb_fr_08.clicked.connect(
            self.pb_fr_08)
        # self.ui_smell_dlg.pb_fr_09.clicked.connect(
        #     self.pb_fr_09)
        # self.ui_smell_dlg.pb_fr_10.clicked.connect(
        #     self.pb_fr_10)
        # self.ui_smell_dlg.pb_fr_11.clicked.connect(
        #     self.pb_fr_11)
        # self.ui_smell_dlg.pb_fr_12.clicked.connect(
        #     self.pb_fr_12)

    def uiDlgSmellExp(self, uiLoader):
        self.ui_smell_exp_dlg = uiLoader.load(
            "./ui/ui_smell_exp.ui")
        self.ui_smell_exp_dlg.pb_back.clicked.connect(
            self.smell_exp_pb_fr_back)
        self.ui_smell_exp_dlg.pb_test.clicked.connect(
            self.smell_exp_pb_fr_test)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def uiDlgFind(self, uiLoader):
        self.ui_find_dlg = uiLoader.load(
            "./ui/ui_find.ui")
        # 터치 스크롤
        QtWidgets.QScroller.grabGesture(self.ui_find_dlg.scrollArea.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)

        self.ui_find_dlg.pb_find_back.clicked.connect(
            self.pb_find_back)

        self.ui_find_dlg.pb_age_teens.clicked.connect(
            self.pb_age_teens)
        self.ui_find_dlg.pb_age_twenties.clicked.connect(
            self.pb_age_twenties)
        self.ui_find_dlg.pb_age_thirties.clicked.connect(
            self.pb_age_thirties)
        self.ui_find_dlg.pb_age_forties.clicked.connect(
            self.pb_age_forties)
        self.ui_find_dlg.pb_age_fifties.clicked.connect(
            self.pb_age_fifties)
        self.ui_find_dlg.pb_age_sixties.clicked.connect(
            self.pb_age_sixties)
        self.ui_find_dlg.pb_per_extraversion.clicked.connect(
            self.pb_per_extraversion)
        self.ui_find_dlg.pb_per_openness.clicked.connect(
            self.pb_per_openness)
        self.ui_find_dlg.pb_per_neuroticism.clicked.connect(
            self.pb_per_neuroticism)
        self.ui_find_dlg.pb_per_diligence.clicked.connect(
            self.pb_per_diligence)
        self.ui_find_dlg.pb_per_agreeableness.clicked.connect(
            self.pb_per_agreeableness)
        self.ui_find_dlg.pb_gender_man.clicked.connect(
            self.pb_gender_man)
        self.ui_find_dlg.pb_gender_woman.clicked.connect(
            self.pb_gender_woman)
        self.ui_find_dlg.pb_pref_aromatic.clicked.connect(
            self.pb_pref_aromatic)
        self.ui_find_dlg.pb_pref_citrus.clicked.connect(
            self.pb_pref_citrus)
        self.ui_find_dlg.pb_pref_woody.clicked.connect(
            self.pb_pref_woody)
        self.ui_find_dlg.pb_pref_floral.clicked.connect(
            self.pb_pref_floral)
        self.ui_find_dlg.pb_pref_spicy.clicked.connect(
            self.pb_pref_spicy)
        self.ui_find_dlg.pb_pref_chypre.clicked.connect(
            self.pb_pref_chypre)
        self.ui_find_dlg.pb_pref_fougere.clicked.connect(
            self.pb_pref_fougere)
        self.ui_find_dlg.pb_pref_fruity.clicked.connect(
            self.pb_pref_fruity)
        self.ui_find_dlg.pb_pref_animalic.clicked.connect(
            self.pb_pref_animalic)
        self.ui_find_dlg.pb_pref_oriental.clicked.connect(
            self.pb_pref_oriental)
        self.ui_find_dlg.pb_pref_amber.clicked.connect(
            self.pb_pref_amber)
        self.ui_find_dlg.pb_pref_aldehyde.clicked.connect(
            self.pb_pref_aldehyde)
        self.ui_find_dlg.pb_color_red.clicked.connect(
            self.pb_color_red)
        self.ui_find_dlg.pb_color_orange.clicked.connect(
            self.pb_color_orange)
        self.ui_find_dlg.pb_color_yellow.clicked.connect(
            self.pb_color_yellow)
        self.ui_find_dlg.pb_color_green.clicked.connect(
            self.pb_color_green)
        self.ui_find_dlg.pb_color_blue.clicked.connect(
            self.pb_color_blue)
        self.ui_find_dlg.pb_color_navy.clicked.connect(
            self.pb_color_navy)
        self.ui_find_dlg.pb_color_purple.clicked.connect(
            self.pb_color_purple)
        self.ui_find_dlg.pb_price_entry.clicked.connect(
            self.pb_price_entry)
        self.ui_find_dlg.pb_price_middle.clicked.connect(
            self.pb_price_middle)
        self.ui_find_dlg.pb_price_highend.clicked.connect(
            self.pb_price_highend)
        
        self.ui_find_dlg.pb_find_recommend.clicked.connect(
            self.pb_find_recommend)
        
        self.init_find_age_range()
        self.init_find_per_range()
        self.init_find_gender_range()
        self.init_find_pref_range()
        self.init_find_color_range()
        self.init_find_price_range()

    def uiDlgFindLoading(self, uiLoader):
        # Find loading
        self.ui_find_loading_dlg = uiLoader.load(
            "./ui/ui_find_loading.ui")

    def uiDlgFindExp(self, uiLoader):
        # Find Exp
        self.ui_find_exp_dlg = uiLoader.load(
            "./ui/ui_find_exp.ui")
        self.ui_find_exp_dlg.pb_back.clicked.connect(
            self.find_exp_pb_back)
        self.ui_find_exp_dlg.pb_test.clicked.connect(
            self.find_exp_pb_test)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def uiDlgMix(self, uiLoader):
        self.ui_mix_dlg = uiLoader.load(
            "./ui/ui_mix.ui")
        
        # 터치 스크롤
        QtWidgets.QScroller.grabGesture(self.ui_mix_dlg.scrollArea.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)

        self.ui_mix_dlg.pb_mix_back.clicked.connect(
            self.pb_mix_back)
        self.ui_mix_dlg.pb_mix_01.clicked.connect(
            self.pb_mix_01)
        self.ui_mix_dlg.pb_mix_02.clicked.connect(
            self.pb_mix_02)
        self.ui_mix_dlg.pb_mix_03.clicked.connect(
            self.pb_mix_03)
        self.ui_mix_dlg.pb_mix_04.clicked.connect(
            self.pb_mix_04)
        self.ui_mix_dlg.pb_mix_05.clicked.connect(
            self.pb_mix_05)
        self.ui_mix_dlg.pb_mix_06.clicked.connect(
            self.pb_mix_06)
        self.ui_mix_dlg.pb_mix_test.clicked.connect(
            self.pb_mix_test)
        # self.ui_mix_dlg.pb_mix_download.clicked.connect(
        #     self.pb_mix_download)
        self.ui_mix_dlg.pg_scent.setVisible(False)        

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 설정
    def uiDlgSettings(self, uiLoader):
        self.ui_settings_dlg = uiLoader.load(
            "./ui/ui_settings.ui")
        self.ui_settings_dlg.hs_scent_power.valueChanged.connect(
            self.uiSettingsScentPowerChanged)
        self.ui_settings_dlg.hs_scent_run_time.valueChanged.connect(
            self.uiSettingsScentRunTimeChanged)
        self.ui_settings_dlg.hs_scent_post_delay.valueChanged.connect(
            self.uiSettingsScentPostDelayChanged)
        self.ui_settings_dlg.hs_cleaning_power.valueChanged.connect(
            self.uiSettingsCleaningPowerChanged)
        self.ui_settings_dlg.hs_cleaning_run_time.valueChanged.connect(
            self.uiSettingsCleaningRunTimeChanged)
        self.ui_settings_dlg.hs_cleaning_post_delay.valueChanged.connect(
            self.uiSettingsCleaningPostDelayChanged)
        self.ui_settings_dlg.hs_scent_emit_interval.valueChanged.connect(
            self.uiSettingsScentEmitIntervalChanged)
        self.ui_settings_dlg.hs_thres_test_max_level.valueChanged.connect(
            self.uiSettingsThresTestMaxLevelChanged)
        self.ui_settings_dlg.hs_thres_node_max_num.valueChanged.connect(
            self.uiSettingsThresNodeMaxNumChanged)
        self.ui_settings_dlg.hs_thres_node_score_num.valueChanged.connect(
            self.uiSettingsThresNodeScoreNumChanged)
        self.ui_settings_dlg.cb_voice_onoff.setCurrentIndex(1)
        self.ui_settings_dlg.cb_result_show_onoff.setCurrentIndex(0)
        self.ui_settings_dlg.pushButton_back.clicked.connect(
            self.uiSettingsBackClicked)
        self.ui_settings_dlg.pushButton_update_settings.clicked.connect(
            self.uiSettingUpdateSettings)
        self.setWindowBySetting(self.ui_settings_dlg)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 프로토콜 메시지 통신 확인
    def uiDlgProtocol(self, uiLoader):
        self.ui_data_protocol_dlg = uiLoader.load(
            "./ui/ui_data_protocol.ui")
        self.available_port_list = dsSerial._get_available_ports()
        self.ui_data_protocol_dlg.comboBox_port.insertItems(
            0, [x.portName() for x in self.available_port_list])
        self.ui_data_protocol_dlg.comboBox_baudrate.insertItems(
            0, [str(x) for x in dsSerial.BAUDRATES])
        self.ui_data_protocol_dlg.comboBox_databits.insertItems(
            0, [str(x) for x in dsSerial.DATABITS])
        self.ui_data_protocol_dlg.comboBox_flowcontrol.insertItems(
            0, [str(x) for x in dsSerial.FLOWCONTROL])
        self.ui_data_protocol_dlg.comboBox_parity.insertItems(
            0, [str(x) for x in dsSerial.PARITY])
        self.ui_data_protocol_dlg.comboBox_stopbits.insertItems(
            0, [str(x) for x in dsSerial.STOPBITS])
        self.ui_data_protocol_dlg.pushButton_connect.clicked.connect(
            self.pushButton_connect_clicked)
        self.ui_data_protocol_dlg.pushButton_emit.clicked.connect(
            self.pushButton_emit_clicked)
        self.ui_data_protocol_dlg.pushButton_clean.clicked.connect(
            self.pushButton_clean_clicked)
        self.ui_data_protocol_dlg.pushButton_emit_clean.clicked.connect(
            self.pushButton_emit_clean_clicked)
        self.ui_data_protocol_dlg.pushButton_stop.clicked.connect(
            self.pushButton_stop_clicked)
        self.ui_data_protocol_dlg.pushButton_temperature.clicked.connect(
            self.pushButton_temperature_clicked)
        self.ui_data_protocol_dlg.pushButton_pressure.clicked.connect(
            self.pushButton_pressure_clicked)
        self.ui_data_protocol_dlg.pushButton_temperature_pressure.clicked.connect(
            self.pushButton_temperature_pressure_clicked)
        self.ui_data_protocol_dlg.pushButton_back.clicked.connect(
            self.pushButton_back_clicked)
        self.setWindowBySetting(self.ui_data_protocol_dlg)

        # 시리얼 통신 기본 설정
        self.ui_data_protocol_dlg.comboBox_baudrate.setCurrentIndex(0)
        self.ui_data_protocol_dlg.comboBox_databits.setCurrentIndex(3)
        # 시리얼 통신 수신 연결
        self.available_port_list = dsSerial._get_available_ports()
        # 시리얼 콘솔로 Text edit 설정
        self.setSerialConsole(self.ui_data_protocol_dlg.textEdit_console)
        # 기본 설정으로 시리얼 연결 COM
        if len(self.available_port_list) > 0:
            # self.connect_serial_default(self.available_port_list[0].portName())
            dsSerial._connect_default(self._serial, self._serial_read_thread,
                                      port_name=self.available_port_list[0].portName())
        self.ui_data_protocol_dlg.pushButton_connect.setText(
           {False: dsText.serialText['status_connect'], True: dsText.serialText['status_disconnect']}[dsSerial._is_open(self._serial)])

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 수신 데이터 파싱
    def parseReadData(self, data):
        print("parseReadData: ", data)
        # try:
        #     mid, mfunc, maddress = struct.unpack_from('>BBH', data, offset=0)
        #     self.ui_data_protocol_dlg.textEdit_console.append("ID:%d, FUNC:%d, ADDR:%d" % (mid, mfunc, maddress))
        #     self.ui_data_protocol_dlg.textEdit_console.moveCursor(QtGui.QTextCursor.End)
        #     # print(mid, mfunc, maddress)
        # except Exception as err:
        #     print("Protocol Error: ", err)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''        
    def requestScentNo(self, scent_no, command): # 발향, 세정 통합 메시지
        # print("requestScentNo: ", scent_no)
        sendMsg= dsComm.sendMsgForEmitClean(id=1, 
                            func=16, 
                            address=4200,
                            qor=8,
                            data_length=16,
                            data_command=command,
                            data_scent_no=scent_no,
                            data_scent_pump_power=dsSetting.dsParam['scent_power'], 
                            data_clean_pump_power=dsSetting.dsParam['cleaning_power'],
                            data_scent_period=dsSetting.dsParam['scent_run_time'],
                            data_clean_period=dsSetting.dsParam['cleaning_run_time'],
                            data_scent_delay=dsSetting.dsParam['scent_post_delay'],
                            data_cleanup_delay=dsSetting.dsParam['cleaning_post_delay'])
        self.write_data(sendMsg)
                
    # CES 2025 전시용 코드 (추후 삭제 시작)
    def requestScentNoScale(self, scent_no, command): # 발향, 세정 통합 메시지
        # print("requestScentNo: ", scent_no)
        if scent_no < 12:
            sendMsg= dsComm.sendMsgForEmitClean(id=1, 
                            func=16, 
                            address=4200,
                            qor=8,
                            data_length=16,
                            data_command=command,
                            data_scent_no=scent_no,
                            data_scent_pump_power=dsSetting.dsParam['scent_power'], 
                            data_clean_pump_power=dsSetting.dsParam['cleaning_power'],
                            data_scent_period=dsSetting.dsParam['scent_run_time'],
                            data_clean_period=dsSetting.dsParam['cleaning_run_time'],
                            data_scent_delay=dsSetting.dsParam['scent_post_delay'],
                            data_cleanup_delay=dsSetting.dsParam['cleaning_post_delay'])
        else:
            sendMsg= dsComm.sendMsgForEmitClean(id=1, 
                            func=16, 
                            address=4200,
                            qor=8,
                            data_length=16,
                            data_command=command,
                            data_scent_no=scent_no,
                            data_scent_pump_power=int(dsSetting.dsParam['scent_power'] * 0.8),
                            data_clean_pump_power=dsSetting.dsParam['cleaning_power'],
                            data_scent_period=dsSetting.dsParam['scent_run_time'],
                            data_clean_period=dsSetting.dsParam['cleaning_run_time'],
                            data_scent_delay=dsSetting.dsParam['scent_post_delay'],
                            data_cleanup_delay=dsSetting.dsParam['cleaning_post_delay'])
        self.write_data(sendMsg)
    # CES 2025 전시용 코드 (추후 삭제 끝)
        
    def requestScentNoAndTime(self, scent_no, command, scent_run_time): # 발향, 세정 통합 메시지
        # print("requestBySettingValues: ", scent_no)
        sendMsg = dsComm.sendMsgForEmitClean(id=1, 
                            func=16, 
                            address=4200,
                            qor=8,
                            data_length=16,
                            data_command=command,
                            data_scent_no=scent_no,
                            data_scent_pump_power=dsSetting.dsParam['scent_power'], 
                            data_clean_pump_power=dsSetting.dsParam['cleaning_power'],
                            data_scent_period=scent_run_time,
                            data_clean_period=dsSetting.dsParam['cleaning_run_time'],
                            data_scent_delay=dsSetting.dsParam['scent_post_delay'],
                            data_cleanup_delay=dsSetting.dsParam['cleaning_post_delay'])      
        self.write_data(sendMsg)  
    
    def requestScentWithValues(self, scent_no, command, \
                        scent_pump_power, clean_pump_power, scent_period, clean_period, scent_delay,cleanup_delay): # 발향, 세정 통합 메시지
        # print("requestScentWithValues: ", scent_no)
        sendMsg = dsComm.sendMsgForEmitClean(id=1, 
                            func=16, 
                            address=4200,
                            qor=8,
                            data_length=16,
                            data_command=command,
                            data_scent_no=scent_no,
                            data_scent_pump_power=scent_pump_power, 
                            data_clean_pump_power=clean_pump_power,
                            data_scent_period=scent_period,
                            data_clean_period=clean_period,
                            data_scent_delay=scent_delay,
                            data_cleanup_delay=cleanup_delay)
        self.write_data(sendMsg)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def progressBarScentAndCleanSimple(self, scent_no, progress_bar):
        scent_time = int(dsSetting.dsParam['scent_run_time'])
        cleaning_time = int(dsSetting.dsParam['cleaning_run_time'])
        all_time = scent_time + cleaning_time
        scent_time_rate = int((scent_time * 100) / all_time)

        progress_bar.setVisible(True)
        # 명령 전달
        # self.requestScentNo(scent_no, command=4)
        self.requestScentNoScale(scent_no, command=4) # CES 2025 용 코드 추후 수정정
        # 발향 Progress
        for i in range(1, scent_time_rate):
            QtTest.QTest.qWait(all_time * 10)
            progress_bar.setValue(i)

        # 세정 Progress
        # dsSound.playGuideSound('cleaning_caution')
        for i in range(scent_time_rate+1, 101):
            QtTest.QTest.qWait(all_time * 10)
            progress_bar.setValue(i)
        
        # 발향 간격 시간
        QtTest.QTest.qWait(dsSetting.dsParam['scent_emit_interval']*1000)
        progress_bar.setVisible(False)

    def progressBarScentAndClean(self, scent_no, progress_bar):
        progress_bar.setVisible(True)
        # 명령 전달
        self.requestScentNo(scent_no, command=4)
        # 발향 Progress
        scent_time = int(dsSetting.dsParam['scent_run_time'])
        for i in range(1, 101):
            QtTest.QTest.qWait(scent_time * 9)
            progress_bar.setValue(i)

        # 세정 Progress
        progress_bar.setStyleSheet(dsStyle.pb_red_style)
        # 사운드
        # dsSound.playGuideSound('cleaning_caution')
        cleaning_time = int(dsSetting.dsParam['cleaning_run_time'])
        for i in range(1, 101):
            QtTest.QTest.qWait(cleaning_time * 9)
            progress_bar.setValue(i)
        progress_bar.setStyleSheet(dsStyle.pb_blue_style)
        
        # 발향 간격 시간
        QtTest.QTest.qWait(dsSetting.dsParam['scent_emit_interval']*1000)
        progress_bar.setVisible(False)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # UI Protocol
    def pushButton_connect_clicked(self):
        if dsSerial._is_open(self._serial):
            dsSerial._disconnect(self._serial, self._serial_read_thread)
        else:
            serial_info = {
                "port_name": self.ui_data_protocol_dlg.comboBox_port.currentText(),
                "baudrate": dsSerial.BAUDRATES[self.ui_data_protocol_dlg.comboBox_baudrate.currentIndex()],
                "bytesize": dsSerial.DATABITS[self.ui_data_protocol_dlg.comboBox_databits.currentIndex()],
                "flow_control": dsSerial.FLOWCONTROL[self.ui_data_protocol_dlg.comboBox_flowcontrol.currentIndex()],
                "parity": dsSerial.PARITY[self.ui_data_protocol_dlg.comboBox_parity.currentIndex()],
                "stop_bits": dsSerial.STOPBITS[self.ui_data_protocol_dlg.comboBox_stopbits.currentIndex()],
            }
            dsSerial._connect(self._serial, self._serial_read_thread, **serial_info)
        self.ui_data_protocol_dlg.pushButton_connect.setText(
            {False: dsText.serialText['status_connect'], True: dsText.serialText['status_disconnect']}[dsSerial._is_open(self._serial)])

    def pushButton_emit_clicked(self):
        self.requestScentTest(1)
        
    def pushButton_clean_clicked(self):
        self.requestScentTest(2)

    def pushButton_emit_clean_clicked(self):
        self.requestScentTest(4)

    def pushButton_stop_clicked(self):
        sendMsg = dsComm.sendMsgForOneCommand(id=1, 
                            func=6, 
                            address=4200,
                            data_command=3)
        self.write_data(sendMsg)
        
    def pushButton_temperature_clicked(self):
        sendMsg = dsComm.sendMsgReadRegister(id=1,
                                func=4,
                                address=4043,
                                qor=2)
        self.write_data(sendMsg)
        
    def pushButton_pressure_clicked(self):
        sendMsg = dsComm.sendMsgReadRegister(id=1,
                                func=4,
                                address=4045,
                                qor=1)
        self.write_data(sendMsg)
        
    def pushButton_temperature_pressure_clicked(self):
        self.requestTempPress()

    def pushButton_back_clicked(self):
        # self.ui_data_protocol_dlg.hide()
        # self.ui_menu_dlg.showMaximized()
        self.uiDlgChange(self.ui_data_protocol_dlg, self.ui_menu_dlg)

    def requestScentTest(self, command):
        scent_no = self.ui_data_protocol_dlg.sb_scentnum.value()
        scent_power = int(self.ui_data_protocol_dlg.textEdit_emit_power.toPlainText())
        clean_power = int(self.ui_data_protocol_dlg.textEdit_clean_power.toPlainText())
        scent_period = int(self.ui_data_protocol_dlg.textEdit_emit_period.toPlainText())
        clean_period = int(self.ui_data_protocol_dlg.textEdit_clean_period.toPlainText())
        scent_delay = int(self.ui_data_protocol_dlg.textEdit_scent_delay.toPlainText())
        cleanup_delay = int(self.ui_data_protocol_dlg.textEdit_cleanup_delay.toPlainText())
        self.requestScentWithValues(scent_no,
                             command,
                             scent_power,
                             clean_power,
                             scent_period,
                             clean_period,
                             scent_delay,
                             cleanup_delay)

    def requestTempPress(self):
        sendMsg = dsComm.sendMsgReadRegister(id=1,
                                func=4,
                                address=4043,
                                qor=3)
        self.write_data(sendMsg)
        
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    # 메인 장치 종료
    def uiMainBtnExit(self):
        # os.system('shutdown -s -t 0') # PC 전원 종료
        QCoreApplication.instance().quit() # 프로그램 종료
        
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # UI Menu Widgets
    def uiMenuBtnQuit(self):
        # # 새로운 다이얼로그를 보인다.
        # self.ui_main_dlg.showMaximized()
        # # 기존 다이얼로그를 숨긴다.
        # self.ui_menu_dlg.hide()
        # # 사운드 (메인)
        # dsSound.playGuideSound('intro_main')
        QCoreApplication.instance().quit() # 프로그램 종료

    def uiMenuPbSmell(self):
        self.fr_num = 0
        # 메뉴 -> 시험
        # self.ui_smell_dlg.showMaximized()
        # self.ui_menu_dlg.hide()
        self.uiDlgChange(self.ui_menu_dlg, self.ui_smell_dlg)
    
    def uiMenuPbFind(self):
        # 메뉴 -> 시험
        # self.ui_find_dlg.showMaximized()
        # self.ui_menu_dlg.hide()
        
        self.init_find_age_range()
        self.set_ui_find_age()
        self.init_find_per_range()
        self.set_ui_find_per()
        self.init_find_gender_range()
        self.set_ui_find_gender()
        self.init_find_pref_range()
        self.set_ui_find_pref()
        self.init_find_color_range()
        self.set_ui_find_color()
        self.init_find_price_range()
        self.set_ui_find_price()
        self.ui_find_dlg.scrollArea.verticalScrollBar().setValue(0)

        self.uiDlgChange(self.ui_menu_dlg, self.ui_find_dlg)

    def uiMenuPbMix(self):
        # 메뉴 -> 시험
        self.mix_num = 1
        self.setMix(self.mix_num)
        # self.ui_mix_dlg.showMaximized()
        # self.ui_menu_dlg.hide()
        self.uiDlgChange(self.ui_menu_dlg, self.ui_mix_dlg)

    def uiMenuBtnSettings(self):
        # 메뉴 -> 설정
        self.updateSettingsUI()
        # self.ui_settings_dlg.showMaximized()
        # self.ui_menu_dlg.hide()
        self.uiDlgChange(self.ui_menu_dlg, self.ui_settings_dlg)

    def uiMenuPbProtocol(self):
        # 메뉴 -> 시험
        # self.ui_data_protocol_dlg.showMaximized()
        # self.ui_menu_dlg.hide()
        self.uiDlgChange(self.ui_menu_dlg, self.ui_data_protocol_dlg)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # 설정
    def uiSettingsBackClicked(self):
        # self.ui_settings_dlg.hide()
        # self.ui_menu_dlg.showMaximized()
        self.uiDlgChange(self.ui_settings_dlg, self.ui_menu_dlg)
        # 사운드 (메뉴)
        dsSound.playGuideSound('intro_menu')

    def uiSettingsScentPowerChanged(self):
        self.ui_settings_dlg.te_scent_power.setPlainText(str(self.ui_settings_dlg.hs_scent_power.value()))

    def uiSettingsScentRunTimeChanged(self):
        self.ui_settings_dlg.te_scent_run_time.setPlainText(str(self.ui_settings_dlg.hs_scent_run_time.value()))

    def uiSettingsScentPostDelayChanged(self):
        self.ui_settings_dlg.te_scent_post_delay.setPlainText(str(self.ui_settings_dlg.hs_scent_post_delay.value()))

    def uiSettingsCleaningPowerChanged(self):
        self.ui_settings_dlg.te_cleaning_power.setPlainText(str(self.ui_settings_dlg.hs_cleaning_power.value()))

    def uiSettingsCleaningRunTimeChanged(self):
        self.ui_settings_dlg.te_cleaning_run_time.setPlainText(str(self.ui_settings_dlg.hs_cleaning_run_time.value()))

    def uiSettingsCleaningPostDelayChanged(self):
        self.ui_settings_dlg.te_cleaning_post_delay.setPlainText(str(self.ui_settings_dlg.hs_cleaning_post_delay.value()))
    
    def uiSettingsScentEmitIntervalChanged(self):
        self.ui_settings_dlg.te_scent_emit_interval.setPlainText(str(self.ui_settings_dlg.hs_scent_emit_interval.value()))

    def uiSettingsThresTestMaxLevelChanged(self):
        self.ui_settings_dlg.te_thres_test_max_level.setPlainText(
            str(self.ui_settings_dlg.hs_thres_test_max_level.value()))

    def uiSettingsThresNodeMaxNumChanged(self):
        self.ui_settings_dlg.te_thres_node_max_num.setPlainText(
            str(self.ui_settings_dlg.hs_thres_node_max_num.value()))

    def uiSettingsThresNodeScoreNumChanged(self):
        self.ui_settings_dlg.te_thres_node_score_num.setPlainText(
            str(self.ui_settings_dlg.hs_thres_node_score_num.value()))

    # 설정 파일을 로드한다.
    def loadSettingsFile(self):
        if os.path.isfile('settings.json'):
            json_data = open('settings.json').read()
            dsSetting.dsParam = json.loads(json_data)
            print(dsSetting.dsParam)

    # 설정을 파일에 저장한다.
    def saveSettingsFile(self):
        with open('settings.json', 'w', encoding='utf-8') as make_file:
            json.dump(dsSetting.dsParam, make_file, ensure_ascii=False, indent='\t')

    # json 파일을 로드하여 설정 값을 반영한다.
    def updateSettingsUI(self):
        self.loadSettingsFile()
        self.ui_settings_dlg.te_scent_power.setPlainText(str(dsSetting.dsParam['scent_power']))
        self.ui_settings_dlg.hs_scent_power.setValue(dsSetting.dsParam['scent_power'])
        self.ui_settings_dlg.te_scent_run_time.setPlainText(str(dsSetting.dsParam['scent_run_time']))
        self.ui_settings_dlg.hs_scent_run_time.setValue(dsSetting.dsParam['scent_run_time'])
        self.ui_settings_dlg.te_scent_post_delay.setPlainText(str(dsSetting.dsParam['scent_post_delay']))
        self.ui_settings_dlg.hs_scent_post_delay.setValue(dsSetting.dsParam['scent_post_delay'])
        self.ui_settings_dlg.te_cleaning_power.setPlainText(str(dsSetting.dsParam['cleaning_power']))
        self.ui_settings_dlg.hs_cleaning_power.setValue(dsSetting.dsParam['cleaning_power'])
        self.ui_settings_dlg.te_cleaning_run_time.setPlainText(str(dsSetting.dsParam['cleaning_run_time']))
        self.ui_settings_dlg.hs_cleaning_run_time.setValue(dsSetting.dsParam['cleaning_run_time'])
        self.ui_settings_dlg.te_cleaning_post_delay.setPlainText(str(dsSetting.dsParam['cleaning_post_delay']))
        self.ui_settings_dlg.hs_cleaning_post_delay.setValue(dsSetting.dsParam['cleaning_post_delay'])
        self.ui_settings_dlg.te_scent_emit_interval.setPlainText(str(dsSetting.dsParam['scent_emit_interval']))
        self.ui_settings_dlg.hs_scent_emit_interval.setValue(dsSetting.dsParam['scent_emit_interval'])
        self.ui_settings_dlg.te_thres_test_max_level.setPlainText(str(dsSetting.dsParam['thres_test_max_level']))
        self.ui_settings_dlg.hs_thres_test_max_level.setValue(dsSetting.dsParam['thres_test_max_level'])
        self.ui_settings_dlg.te_thres_node_max_num.setPlainText(str(dsSetting.dsParam['thres_node_max_num']))
        self.ui_settings_dlg.hs_thres_node_max_num.setValue(dsSetting.dsParam['thres_node_max_num'])
        self.ui_settings_dlg.te_thres_node_score_num.setPlainText(str(dsSetting.dsParam['thres_node_score_num']))
        self.ui_settings_dlg.hs_thres_node_score_num.setValue(dsSetting.dsParam['thres_node_score_num'])
        self.ui_settings_dlg.cb_voice_onoff.setCurrentIndex(dsSetting.dsParam['voice_onoff'])
        # self.ui_settings_dlg.cb_monitoring_onoff.setCurrentIndex(dsSetting.dsParam['monitoring_onoff'])
        self.ui_settings_dlg.cb_result_show_onoff.setCurrentIndex(dsSetting.dsParam['result_show_onoff'])
        self.ui_settings_dlg.cb_front_onoff.setCurrentIndex(dsSetting.dsParam['front_onoff'])
        self.ui_settings_dlg.cb_window_bars_onoff.setCurrentIndex(dsSetting.dsParam['window_bars_onoff'])

    # 설정 UI의 변경사항을 반영하고 json 파일에 저장한다.
    def uiSettingUpdateSettings(self):
        dsSetting.dsParam['scent_power'] = int(self.ui_settings_dlg.te_scent_power.toPlainText())
        dsSetting.dsParam['scent_run_time'] = int(self.ui_settings_dlg.te_scent_run_time.toPlainText())
        dsSetting.dsParam['scent_post_delay'] = int(self.ui_settings_dlg.te_scent_post_delay.toPlainText())
        dsSetting.dsParam['cleaning_power'] = int(self.ui_settings_dlg.te_cleaning_power.toPlainText())
        dsSetting.dsParam['cleaning_run_time'] = int(self.ui_settings_dlg.te_cleaning_run_time.toPlainText())
        dsSetting.dsParam['cleaning_post_delay'] = int(self.ui_settings_dlg.te_cleaning_post_delay.toPlainText())
        dsSetting.dsParam['scent_emit_interval'] = int(self.ui_settings_dlg.te_scent_emit_interval.toPlainText())
        dsSetting.dsParam['thres_test_max_level'] = int(self.ui_settings_dlg.te_thres_test_max_level.toPlainText())
        dsSetting.dsParam['thres_node_max_num'] = int(self.ui_settings_dlg.te_thres_node_max_num.toPlainText())
        dsSetting.dsParam['thres_node_score_num'] = int(self.ui_settings_dlg.te_thres_node_score_num.toPlainText())
        dsSetting.dsParam['voice_onoff'] = self.ui_settings_dlg.cb_voice_onoff.currentIndex()
        # dsSetting.dsParam['monitoring_onoff'] = self.ui_settings_dlg.cb_monitoring_onoff.currentIndex()
        dsSetting.dsParam['result_show_onoff'] = self.ui_settings_dlg.cb_result_show_onoff.currentIndex()
        dsSetting.dsParam['front_onoff'] = self.ui_settings_dlg.cb_front_onoff.currentIndex()
        dsSetting.dsParam['window_bars_onoff'] = self.ui_settings_dlg.cb_window_bars_onoff.currentIndex()
        print(dsSetting.dsParam)
        self.saveSettingsFile()

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    def smell_pb_back(self):
        self.fr_num = 0
        # self.ui_smell_dlg.hide()
        # self.ui_menu_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_menu_dlg)

    def pb_fr_01(self):
        self.fr_num = 1
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)

    def pb_fr_02(self):
        self.fr_num = 2
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_03(self):
        self.fr_num = 3
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_04(self):
        self.fr_num = 4
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_05(self):
        self.fr_num = 5
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_06(self):
        self.fr_num = 6
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_07(self):
        self.fr_num = 7
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_08(self):
        self.fr_num = 8
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_09(self):
        self.fr_num = 9
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_10(self):
        self.fr_num = 10
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_11(self):
        self.fr_num = 11
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    def pb_fr_12(self):
        self.fr_num = 12
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_dlg.hide()
        # self.ui_smell_exp_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_dlg, self.ui_smell_exp_dlg)
    
    def setUiSmellExpDlg(self, number):
        self.ui_smell_exp_dlg.label_background.setStyleSheet(
            dsImage.dsDetailImg[number])

    def smell_exp_pb_fr_back(self):
        self.fr_num = 0
        self.setUiSmellExpDlg(self.fr_num)
        # self.ui_smell_exp_dlg.hide()
        # self.ui_smell_dlg.showMaximized()
        self.uiDlgChange(self.ui_smell_exp_dlg, self.ui_smell_dlg)

    def smell_exp_pb_fr_test(self):
        self.ui_smell_exp_dlg.pb_back.setVisible(False)
        self.ui_smell_exp_dlg.pb_test.setVisible(False)
        self.progressBarScentAndCleanSimple(scent_no=self.fr_num,
                                      progress_bar=self.ui_smell_exp_dlg.pg_scent)
        self.ui_smell_exp_dlg.pb_back.setVisible(True)
        self.ui_smell_exp_dlg.pb_test.setVisible(True)

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def pb_find_back(self):
        # self.ui_find_dlg.hide()
        # self.ui_menu_dlg.showMaximized()
        self.uiDlgChange(self.ui_find_dlg, self.ui_menu_dlg)

    # Ages
    def init_find_age_range(self):
        self.find_age_range_num = dsNum.FIND_AGE_NONE
        
    def toggle_find_age_range(self, num):
        if self.find_age_range_num == num:
            self.init_find_age_range()
        else:
            self.find_age_range_num = num
        self.set_ui_find_age()

    def check_find_age_range(self, num):
        if self.find_age_range_num == num:
            return True
        else:
            return False
        
    def set_ui_find_age(self):
        self.ui_find_dlg.pb_age_teens.setStyleSheet(
           {False: dsStyle.pb_age_teens, True: dsStyle.pb_age_teens_selected}\
            [self.check_find_age_range(dsNum.FIND_AGE_TEENS)])
        self.ui_find_dlg.pb_age_twenties.setStyleSheet(
           {False: dsStyle.pb_age_twenties, True: dsStyle.pb_age_twenties_selected}\
            [self.check_find_age_range(dsNum.FIND_AGE_TWENTIES)])
        self.ui_find_dlg.pb_age_thirties.setStyleSheet(
           {False: dsStyle.pb_age_thirties, True: dsStyle.pb_age_thirties_selected}\
            [self.check_find_age_range(dsNum.FIND_AGE_THIRTIES)])
        self.ui_find_dlg.pb_age_forties.setStyleSheet(
           {False: dsStyle.pb_age_forties, True: dsStyle.pb_age_forties_selected}\
            [self.check_find_age_range(dsNum.FIND_AGE_FORTIES)])
        self.ui_find_dlg.pb_age_fifties.setStyleSheet(
           {False: dsStyle.pb_age_fifties, True: dsStyle.pb_age_fifties_selected}\
            [self.check_find_age_range(dsNum.FIND_AGE_FIFTIES)])
        self.ui_find_dlg.pb_age_sixties.setStyleSheet(
           {False: dsStyle.pb_age_sixties, True: dsStyle.pb_age_sixties_selected}\
            [self.check_find_age_range(dsNum.FIND_AGE_SIXTIES)])

    def pb_age_teens(self):
        self.toggle_find_age_range(dsNum.FIND_AGE_TEENS)
        
    def pb_age_twenties(self):
        self.toggle_find_age_range(dsNum.FIND_AGE_TWENTIES)
        
    def pb_age_thirties(self):
        self.toggle_find_age_range(dsNum.FIND_AGE_THIRTIES)
        
    def pb_age_forties(self):
        self.toggle_find_age_range(dsNum.FIND_AGE_FORTIES)
        
    def pb_age_fifties(self):
        self.toggle_find_age_range(dsNum.FIND_AGE_FIFTIES)
        
    def pb_age_sixties(self):
        self.toggle_find_age_range(dsNum.FIND_AGE_SIXTIES)
        

    # Personality
    def init_find_per_range(self):
        self.find_per_range_num = dsNum.FIND_PER_NONE
        
    def toggle_find_per_ranges(self, num):
        if self.find_per_range_num == num:
            self.init_find_per_range()
        else:
            self.find_per_range_num = num
        self.set_ui_find_per()

    def check_find_per_range(self, num):
        if self.find_per_range_num == num:
            return True
        else:
            return False
        
    def set_ui_find_per(self):
        self.ui_find_dlg.pb_per_extraversion.setStyleSheet(
           {False: dsStyle.pb_per_extraversion, True: dsStyle.pb_per_extraversion_selected}\
            [self.check_find_per_range(dsNum.FIND_PER_EXTRAVERSION)])
        self.ui_find_dlg.pb_per_openness.setStyleSheet(
           {False: dsStyle.pb_per_openness, True: dsStyle.pb_per_openness_selected}\
            [self.check_find_per_range(dsNum.FIND_PER_OPENNESS)])
        self.ui_find_dlg.pb_per_neuroticism.setStyleSheet(
           {False: dsStyle.pb_per_neuroticism, True: dsStyle.pb_per_neuroticism_selected}\
            [self.check_find_per_range(dsNum.FIND_PER_NEUROTICISM)])
        self.ui_find_dlg.pb_per_diligence.setStyleSheet(
           {False: dsStyle.pb_per_diligence, True: dsStyle.pb_per_diligence_selected}\
            [self.check_find_per_range(dsNum.FIND_PER_DILIGENCE)])
        self.ui_find_dlg.pb_per_agreeableness.setStyleSheet(
           {False: dsStyle.pb_per_agreeableness, True: dsStyle.pb_per_agreeableness_selected}\
            [self.check_find_per_range(dsNum.FIND_PER_AGREEABLENESS)])
        
    def pb_per_extraversion(self):
        self.toggle_find_per_ranges(dsNum.FIND_PER_EXTRAVERSION)
        
    def pb_per_openness(self):
        self.toggle_find_per_ranges(dsNum.FIND_PER_OPENNESS)
        
    def pb_per_neuroticism(self):
        self.toggle_find_per_ranges(dsNum.FIND_PER_NEUROTICISM)
        
    def pb_per_diligence(self):
        self.toggle_find_per_ranges(dsNum.FIND_PER_DILIGENCE)
        
    def pb_per_agreeableness(self):
        self.toggle_find_per_ranges(dsNum.FIND_PER_AGREEABLENESS)


    # Gender
    def init_find_gender_range(self):
        self.find_gender_range_num = dsNum.FIND_GENDER_NONE
        
    def toggle_find_gender_range(self, num):
        if self.find_gender_range_num == num:
            self.init_find_gender_range()
        else:
            self.find_gender_range_num = num
        self.set_ui_find_gender()

    def check_find_gender_range(self, num):
        if self.find_gender_range_num == num:
            return True
        else:
            return False
        
    def set_ui_find_gender(self):
        self.ui_find_dlg.pb_gender_man.setStyleSheet(
           {False: dsStyle.pb_gender_man, True: dsStyle.pb_gender_man_selected}\
            [self.check_find_gender_range(dsNum.FIND_GENDER_MAN)])
        self.ui_find_dlg.pb_gender_woman.setStyleSheet(
           {False: dsStyle.pb_gender_woman, True: dsStyle.pb_gender_woman_selected}\
            [self.check_find_gender_range(dsNum.FIND_GENDER_WOMAN)])

    def pb_gender_man(self):
        self.toggle_find_gender_range(dsNum.FIND_GENDER_MAN)
        
    def pb_gender_woman(self):
        self.toggle_find_gender_range(dsNum.FIND_GENDER_WOMAN)


    # Pref scent
    def init_find_pref_range(self):
        self.find_pref_range_num = dsNum.FIND_PREF_NONE
        
    def toggle_find_pref_range(self, num):
        if self.find_pref_range_num == num:
            self.init_find_pref_range()
        else:
            self.find_pref_range_num = num
        self.set_ui_find_pref()

    def check_find_pref_range(self, num):
        if self.find_pref_range_num == num:
            return True
        else:
            return False
        
    def set_ui_find_pref(self):
        self.ui_find_dlg.pb_pref_aromatic.setStyleSheet(
           {False: dsStyle.pb_pref_aromatic, True: dsStyle.pb_pref_aromatic_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_AROMATIC)])
        self.ui_find_dlg.pb_pref_citrus.setStyleSheet(
           {False: dsStyle.pb_pref_citrus, True: dsStyle.pb_pref_citrus_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_CITRUS)])
        self.ui_find_dlg.pb_pref_woody.setStyleSheet(
           {False: dsStyle.pb_pref_woody, True: dsStyle.pb_pref_woody_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_WOODY)])
        self.ui_find_dlg.pb_pref_floral.setStyleSheet(
           {False: dsStyle.pb_pref_floral, True: dsStyle.pb_pref_floral_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_FLORAL)])
        self.ui_find_dlg.pb_pref_spicy.setStyleSheet(
           {False: dsStyle.pb_pref_spicy, True: dsStyle.pb_pref_spicy_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_SPICY)])
        self.ui_find_dlg.pb_pref_chypre.setStyleSheet(
           {False: dsStyle.pb_pref_chypre, True: dsStyle.pb_pref_chypre_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_CHYPRE)])
        self.ui_find_dlg.pb_pref_fougere.setStyleSheet(
           {False: dsStyle.pb_pref_fougere, True: dsStyle.pb_pref_fougere_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_FOUGERE)])
        self.ui_find_dlg.pb_pref_fruity.setStyleSheet(
           {False: dsStyle.pb_pref_fruity, True: dsStyle.pb_pref_fruity_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_FRUITY)])
        self.ui_find_dlg.pb_pref_animalic.setStyleSheet(
           {False: dsStyle.pb_pref_animalic, True: dsStyle.pb_pref_animalic_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_ANIMALIC)])
        self.ui_find_dlg.pb_pref_oriental.setStyleSheet(
           {False: dsStyle.pb_pref_oriental, True: dsStyle.pb_pref_oriental_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_ORIENTAL)])
        self.ui_find_dlg.pb_pref_amber.setStyleSheet(
           {False: dsStyle.pb_pref_amber, True: dsStyle.pb_pref_amber_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_AMBER)])
        self.ui_find_dlg.pb_pref_aldehyde.setStyleSheet(
           {False: dsStyle.pb_pref_aldehyde, True: dsStyle.pb_pref_aldehyde_selected}\
            [self.check_find_pref_range(dsNum.FIND_PREF_ALDEHYDE)])

    def pb_pref_aromatic(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_AROMATIC)
        
    def pb_pref_citrus(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_CITRUS)
        
    def pb_pref_woody(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_WOODY)
        
    def pb_pref_floral(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_FLORAL)
        
    def pb_pref_spicy(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_SPICY)
        
    def pb_pref_chypre(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_CHYPRE)
        
    def pb_pref_fougere(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_FOUGERE)
        
    def pb_pref_fruity(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_FRUITY)
        
    def pb_pref_animalic(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_ANIMALIC)
        
    def pb_pref_oriental(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_ORIENTAL)
        
    def pb_pref_amber(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_AMBER)
        
    def pb_pref_aldehyde(self):
        self.toggle_find_pref_range(dsNum.FIND_PREF_ALDEHYDE)
        
    # Color
    def init_find_color_range(self):
        self.find_color_range_num = dsNum.FIND_COLOR_NONE
        
    def toggle_find_color_ranges(self, num):
        if self.find_color_range_num == num:
            self.init_find_color_range()
        else:
            self.find_color_range_num = num
        self.set_ui_find_color()

    def check_find_color_range(self, num):
        if self.find_color_range_num == num:
            return True
        else:
            return False
        
    def set_ui_find_color(self):
        self.ui_find_dlg.pb_color_red.setStyleSheet(
           {False: dsStyle.pb_color_red, True: dsStyle.pb_color_red_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_RED)])
        self.ui_find_dlg.pb_color_orange.setStyleSheet(
           {False: dsStyle.pb_color_orange, True: dsStyle.pb_color_orange_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_ORANGE)])
        self.ui_find_dlg.pb_color_yellow.setStyleSheet(
           {False: dsStyle.pb_color_yellow, True: dsStyle.pb_color_yellow_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_YELLOW)])
        self.ui_find_dlg.pb_color_green.setStyleSheet(
           {False: dsStyle.pb_color_green, True: dsStyle.pb_color_green_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_GREEN)])
        self.ui_find_dlg.pb_color_blue.setStyleSheet(
           {False: dsStyle.pb_color_blue, True: dsStyle.pb_color_blue_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_BLUE)])
        self.ui_find_dlg.pb_color_navy.setStyleSheet(
           {False: dsStyle.pb_color_navy, True: dsStyle.pb_color_navy_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_NAVY)])
        self.ui_find_dlg.pb_color_purple.setStyleSheet(
           {False: dsStyle.pb_color_purple, True: dsStyle.pb_color_purple_selected}\
            [self.check_find_color_range(dsNum.FIND_COLOR_PURPLE)])
                
    def pb_color_red(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_RED)
        
    def pb_color_orange(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_ORANGE)
        
    def pb_color_yellow(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_YELLOW)
        
    def pb_color_green(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_GREEN)
        
    def pb_color_blue(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_BLUE)
        
    def pb_color_navy(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_NAVY)
        
    def pb_color_purple(self):
        self.toggle_find_color_ranges(dsNum.FIND_COLOR_PURPLE)
        

    # Price
    def init_find_price_range(self):
        self.find_price_range_num = dsNum.FIND_PRICE_NONE
        
    def toggle_find_price_range(self, num):
        if self.find_price_range_num == num:
            self.init_find_price_range()
        else:
            self.find_price_range_num = num
        self.set_ui_find_price()

    def check_find_price_range(self, num):
        if self.find_price_range_num == num:
            return True
        else:
            return False
        
    def set_ui_find_price(self):
        self.ui_find_dlg.pb_price_entry.setStyleSheet(
           {False: dsStyle.pb_price_entry, True: dsStyle.pb_price_entry_selected}\
            [self.check_find_price_range(dsNum.FIND_PRICE_ENTRY)])
        self.ui_find_dlg.pb_price_middle.setStyleSheet(
           {False: dsStyle.pb_price_middle, True: dsStyle.pb_price_middle_selected}\
            [self.check_find_price_range(dsNum.FIND_PRICE_MIDDLE)])
        self.ui_find_dlg.pb_price_highend.setStyleSheet(
           {False: dsStyle.pb_price_highend, True: dsStyle.pb_price_highend_selected}\
            [self.check_find_price_range(dsNum.FIND_PRICE_HIGHEND)])

    def pb_price_entry(self):
        self.toggle_find_price_range(dsNum.FIND_PRICE_ENTRY)
        
    def pb_price_middle(self):
        self.toggle_find_price_range(dsNum.FIND_PRICE_MIDDLE)
        
    def pb_price_highend(self):
        self.toggle_find_price_range(dsNum.FIND_PRICE_HIGHEND)

    def pb_find_recommend(self):
        self.find_recommend(self.find_age_range_num, 
                            self.find_per_range_num,
                            self.find_gender_range_num,
                            self.find_pref_range_num,
                            self.find_color_range_num,
                            self.find_price_range_num)
        print("Age: %d" % (self.find_age_range_num))
        print("Personality: %d" % (self.find_per_range_num))
        print("Gender: %d" % (self.find_gender_range_num))
        print("Pref scent: %d" % (self.find_pref_range_num))
        print("Color: %d" % (self.find_color_range_num))
        print("Price: %d" % (self.find_price_range_num))


    # Fine Recommend
    def find_recommend(self, age, personlity, gender, pref_scent, color, price):
        self.find_num = 0
        self.uiDlgChange(self.ui_find_dlg, self.ui_find_loading_dlg)
        # QtTest.QTest.qWait(3000)
        # self.find_num = random.randint(1, 8)
        # self.setUiFindExpDlg(self.find_num)
        # self.uiDlgChange(self.ui_find_loading_dlg, self.ui_find_exp_dlg)

        find_input_data = {
            'Age': age*10,
            'Gender': dsNum.find_gender_text[gender], #'Woman',
            'Personality': dsNum.find_per_text[personlity], #'Agreeableness',
            'Preferred_Scent': dsNum.find_pref_text[pref_scent], #'Floral',
            'Preferred_Color': dsNum.find_color_text[color], #'Yellow',
            'Price': dsNum.find_price_text[price], #'Entry'
        }
        print(find_input_data)

        result = testModel.find_scent(find_input_data)
        self.find_num = result['predicted_id'] + 1 # 0부터 결과여서 1 더함
        
        self.setUiFindExpDlg(self.find_num)
        self.uiDlgChange(self.ui_find_loading_dlg, self.ui_find_exp_dlg)

    # Find Exp
    def setUiFindExpDlg(self, number):
        # 배경 이미지 설정
        self.ui_find_exp_dlg.label_background.setStyleSheet(
            dsImage.dsFindDetailImg[number])
        
        # QR 코드 생성 및 우측 상단에 표시
        try:
            # QR 코드 생성 (number-1을 인덱스로 사용)
            qr_path = dsQRcode.generate_qr_code(idx=number-1, save_path=f"temp_qr_{number}.png")
            
            # QR 코드를 표시할 QLabel 생성 (우측 상단에 배치)
            if not hasattr(self, 'qr_label'):
                self.qr_label = QtWidgets.QLabel(self.ui_find_exp_dlg)
                self.qr_label.setFixedSize(100, 100)
                self.qr_label.setStyleSheet("border: none; background: transparent;")
            
            # QR 코드 이미지 로드 및 설정
            qr_pixmap = QtGui.QPixmap(qr_path)
            self.qr_label.setPixmap(qr_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            
            # 우측 상단에 배치
            self.qr_label.move(self.ui_find_exp_dlg.width() - 120, 20)
            self.qr_label.show()
            
        except Exception as e:
            print(f"QR 코드 생성 오류: {e}")
            # QR 코드 생성 실패시 QR 라벨 숨김
            if hasattr(self, 'qr_label'):
                self.qr_label.hide()

    def find_exp_pb_back(self):
        self.find_num = 0
        # QR 라벨 숨기기
        if hasattr(self, 'qr_label'):
            self.qr_label.hide()
        # self.setUiFindExpDlg(self.find_num)
        # self.ui_find_exp_dlg.hide()
        # self.ui_menu_dlg.showMaximized()
        self.uiDlgChange(self.ui_find_exp_dlg, self.ui_menu_dlg)

    def find_exp_pb_test(self):
        self.ui_find_exp_dlg.pb_back.setVisible(False)
        self.ui_find_exp_dlg.pb_test.setVisible(False)
        self.progressBarScentAndCleanSimple(scent_no=self.find_num,
                                      progress_bar=self.ui_find_exp_dlg.pg_scent)
        self.ui_find_exp_dlg.pb_back.setVisible(True)
        self.ui_find_exp_dlg.pb_test.setVisible(True)


    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def pb_mix_back(self):
        self.mix_num = 1
        # self.ui_mix_dlg.hide()
        # self.ui_menu_dlg.showMaximized()
        self.uiDlgChange(self.ui_mix_dlg, self.ui_menu_dlg)

    def pb_mix_01(self):
        self.mix_num = 1
        self.setMix(self.mix_num)
        
    def pb_mix_02(self):
        self.mix_num = 2
        self.setMix(self.mix_num)
        
    def pb_mix_03(self):
        self.mix_num = 3
        self.setMix(self.mix_num)
        
    def pb_mix_04(self):
        self.mix_num = 4
        self.setMix(self.mix_num)
        
    def pb_mix_05(self):
        self.mix_num = 5
        self.setMix(self.mix_num)
        
    def pb_mix_06(self):
        self.mix_num = 6
        self.setMix(self.mix_num)
    
    def pb_mix_test(self):
        self.ui_mix_dlg.pb_mix_back.setVisible(False)
        self.ui_mix_dlg.pb_mix_test.setVisible(False)
        self.ui_mix_dlg.pb_mix_download.setVisible(False)
        self.progressBarScentAndCleanSimple(scent_no=self.mix_num+12,
                                      progress_bar=self.ui_mix_dlg.pg_scent)
        self.ui_mix_dlg.pb_mix_back.setVisible(True)
        self.ui_mix_dlg.pb_mix_test.setVisible(True)
        self.ui_mix_dlg.pb_mix_download.setVisible(True)


    def setMix(self, num):
        self.ui_mix_dlg.label_info.setStyleSheet(
            dsImage.dsMixInfoImg[num])
        
        self.ui_mix_dlg.pb_mix_01.setStyleSheet(
                dsImage.dsMixBtnImg['1'])
        self.ui_mix_dlg.pb_mix_02.setStyleSheet(
                dsImage.dsMixBtnImg['2'])
        self.ui_mix_dlg.pb_mix_03.setStyleSheet(
                dsImage.dsMixBtnImg['3'])
        self.ui_mix_dlg.pb_mix_04.setStyleSheet(
                dsImage.dsMixBtnImg['4'])
        self.ui_mix_dlg.pb_mix_05.setStyleSheet(
                dsImage.dsMixBtnImg['5'])
        self.ui_mix_dlg.pb_mix_06.setStyleSheet(
                dsImage.dsMixBtnImg['6'])

        if num == 1:
            self.ui_mix_dlg.pb_mix_01.setStyleSheet(
                dsImage.dsMixBtnImg['1_selected'])
        elif num == 2:
            self.ui_mix_dlg.pb_mix_02.setStyleSheet(
                dsImage.dsMixBtnImg['2_selected'])
        elif num == 3:
            self.ui_mix_dlg.pb_mix_03.setStyleSheet(
                dsImage.dsMixBtnImg['3_selected'])
        elif num == 4:
            self.ui_mix_dlg.pb_mix_04.setStyleSheet(
                dsImage.dsMixBtnImg['4_selected'])
        elif num == 5:
            self.ui_mix_dlg.pb_mix_05.setStyleSheet(
                dsImage.dsMixBtnImg['5_selected'])
        elif num == 6:
            self.ui_mix_dlg.pb_mix_06.setStyleSheet(
                dsImage.dsMixBtnImg['6_selected'])



''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Main 함수
if __name__ == '__main__':
    """Main"""
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    # excepthook = sys.excepthook
    # sys.excepthook = lambda t, val, tb: excepthook(t, val, tb)

    # 폰트를 로딩한다.
    # QFontDatabase.addApplicationFont("./ui/font/PAYBOOCBOLD.TTF")
    # app.setFont(QFont("PAYBOOCBOLD"))
    
    # 다이얼로그를 모두 생성한다.
    uiDlg = UiDlg()
    uiDlg.uiDlgStart()
    sys.exit(app.exec())