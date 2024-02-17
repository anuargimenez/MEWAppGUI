# -*- coding: utf-8 -*-

# LIBRERÍAS DE LA GUI DE PYQT5
from Custom_Widgets.Widgets import QCustomSlideMenu, QCustomStackedWidget
import resources_rc
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGridLayout, QLabel, QTextEdit, QPushButton, QVBoxLayout
from PyQt5.QtGui import QDropEvent, QIcon
from PyQt5.QtCore import Qt

# LIBRERÍAS DE LAS APIs Y CONEXIONES SERIE
from pipython import GCSDevice, pitools
import serial
from serial.serialutil import SerialException

# LIBRERÍAS CON RECURSOS DEL SISTEMA
import re
import os
import time
import sys

# Configuraciónd de los drivers y motores utilizados en los stages para la solicitud de la API
CONTROLLERNAME = 'C-663.12'  # Nombre controlador utilizado
STAGES = ['L-509.20SD00']  # Nombre de los stages utilizados
# Hace un movimiento de referencia al negative limit switch para establecer el 0
REFMODES = 'FNL'

# Clase definiendo el lector de g-code con drag and drop


class TextFileReader(QMainWindow):
    def _init_(self):
        super()._init_()

        self.initUI()

    def initUI(self):
        # Configurar la ventana principal
        self.setGeometry(100, 100, 400, 400)
        self.setWindowTitle("Arrastra y suelta archivos de texto")
        # Reemplaza 'icon.png' con la ruta de tu propio ícono
        self.setWindowIcon(QIcon('icon.png'))

        # Configurar el estilo CSS para una interfaz oscura
        self.setStyleSheet("""
            QMainWindow {
                background-color: #333;
                color: #fff;
            }
            QTextEdit {
                background-color: #444;
                border: 1px solid #555;
                padding: 5px;
                color: #fff;
            }
            QPushButton {
                background-color: #0078d4;
                color: #fff;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #005cbf;
            }
            QLabel#dragLabel {
                background-color: rgba(0, 0, 0, 0.5);
                color: #fff;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #555;
            }
        """)

        # Configurar el diseño de cuadrícula
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        # Campo de solo lectura para mostrar el nombre del archivo
        self.file_name_field = QTextEdit(self)
        self.file_name_field.setReadOnly(True)
        grid_layout.addWidget(self.file_name_field, 0, 0,
                              1, 2)  # Ocupa dos columnas

        # Botón para imprimir contenido en la terminal
        self.print_button = QPushButton('Start Printing from G-Code', self)
        self.print_button.clicked.connect(self.print_content)
        grid_layout.addWidget(self.print_button, 1, 0,
                              1, 2)  # Ocupa dos columnas

        # Etiqueta para mostrar mensaje de arrastrar y soltar
        self.drag_label = QLabel('Drag a .txt file with G-Code', self)
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setObjectName('dragLabel')
        grid_layout.addWidget(self.drag_label, 2, 0, 1,
                              2)  # Ocupa dos columnas

        # Habilitar la recepción de archivos arrastrados
        self.setAcceptDrops(True)

    def dropEvent(self, event: QDropEvent):
        # Manejar el evento de arrastrar y soltar
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.txt'):
                file_name = os.path.basename(file_path)
                self.current_file_path = file_path  # Guardar la ruta del archivo
                # Mostrar el nombre del archivo
                self.file_name_field.setPlainText(file_name)
                # Actualizar el mensaje
                self.drag_label.setText('Archivo cargado: ' + file_name)

    def dragEnterEvent(self, event: QDropEvent):
        # Aceptar solo archivos de texto (.txt)
        if event.mimeData().hasUrls() and all(url.toLocalFile().endswith('.txt') for url in event.mimeData().urls()):
            event.accept()
            # Actualizar el mensaje
            self.drag_label.setText('Drop file and click on Print')
        else:
            event.ignore()
            # Actualizar el mensaje
            self.drag_label.setText('Drag a .txt file with G-Code')

    def print_content(self):
        # Imprimir el contenido del archivo en la terminal
        if hasattr(self, 'current_file_path'):
            with open(self.current_file_path, 'r') as file:
                file_content = file.read()
                print(
                    f"Contenido del archivo {self.current_file_path}:\n{file_content}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextFileReader()
    window.show()
    sys.exit(app.exec_())

# Clase principal de la aplicación con los métodos para cada función


class Ui_MainWindow(object):

    ## -----------------------------------------------------------------##
    # Métodos de la clase para definir las funciones de botones y otros
    ## -----------------------------------------------------------------##

    # METHOD 1 - Stage XY Conection Button
    def stageConect(self):
        if not self.stage_connected:
            # Iniciando API...
            self.outputConText.append('Conecting Stages...')
            cursor = self.outputConText.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.outputConText.setTextCursor(cursor)

            # Connect, setup system and move stages and display the positions in a loop.
            # Se utiliza "with" para que la conexión se cierre si aparece algun error
            self.stageY = GCSDevice(CONTROLLERNAME)

            # Establecer la comunicación serie con el USB del controlador. Los dos drivers están conectados en una daisy chain en serie.
            self.stageY.OpenUSBDaisyChain(description='0022550779')
            daisychainid = self.stageY.dcid
            self.stageY.ConnectDaisyChainDevice(1, daisychainid)
            self.outputConText.append('\n{}:\n{}'.format(
                self.stageY.GetInterfaceDescription(), self.stageY.qIDN()))
            cursor = self.outputConText.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.outputConText.setTextCursor(cursor)

            self.stageX = GCSDevice(CONTROLLERNAME)
            self.stageX.ConnectDaisyChainDevice(8, daisychainid)
            self.outputConText.append('\n{}:\n{}'.format(
                self.stageX.GetInterfaceDescription(), self.stageX.qIDN()))
            cursor = self.outputConText.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.outputConText.setTextCursor(cursor)

            # Se inicializa el sistema con la función de pitools startup. Todos los ejes conectados se pararán si están en movimiento y su servo se activará
            self.stage_connected = True  # Actualizar el estado de conexión
            self.outputConText.append('Stages are conected and initialized!')
            cursor = self.outputConText.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.outputConText.setTextCursor(cursor)
            pitools.startup(self.stageY, stages=STAGES, refmodes=REFMODES)
            pitools.startup(self.stageX, stages=STAGES, refmodes=REFMODES)

        else:
            self.outputConText.append(
                'Device is already connected. Restart system.')

    # METHOD 2 - Calibrate X Stage
    def calibrateXStage(self):
        # Obtenemos el rango de movimiento del Stage X
        rangemin2 = self.stageX.qTMN()
        rangemax2 = self.stageX.qTMX()

        for axis in self.stageX.axes:  # obtiene los ejes conectados de la propiedad axes
            # Mueve los ejes entre su valor mínimo y máximo
            for target in (rangemin2[axis], rangemax2[axis]):
                # Muestra estado en pantalla
                self.outputCalibrText.append(
                    'move axis X to {:.2f}'.format(target))
                cursor = self.outputCalibrText.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                self.outputCalibrText.setTextCursor(cursor)

                # set velocity
                self.stageX.VEL(1, 12)  # Max vel is 17 mm/s
                self.stageX.MOV(axis, target)

                # "waitontarget" espera a que termine el movimiento
                pitools.waitontarget(self.stageX, axes=axis)
                position = self.stageX.qPOS(axis)[axis]  # query single axis
                self.outputCalibrText.append(
                    'current position of axis {} is {:.2f}'.format(axis, position))
                cursor = self.outputCalibrText.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                self.outputCalibrText.setTextCursor(cursor)

    # METHOD 3 - Calibrate Y Stage

    def calibrateYStage(self):
        # Obtenemos el rango de movimiento de cada stage.
        rangemin = self.stageY.qTMN()
        rangemax = self.stageY.qTMX()

        # Movimiento de los stages
        for axis in self.stageY.axes:  # obtiene los ejes conectados de la propiedad axes
            # Mueve los ejes entre su valor mínimo y máximo
            for target in (rangemin[axis], rangemax[axis]):
                # Muestra estado de calibración en pantalla
                self.outputCalibrText.append(
                    'move axis Y to {:.2f}'.format(target))
                cursor = self.outputCalibrText.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                self.outputCalibrText.setTextCursor(cursor)

                self.stageY.VEL(1, 12)  # Max vel is 17 mm/s
                self.stageY.MOV(axis, target)

                # "waitontarget" espera a que termine el movimiento
                pitools.waitontarget(self.stageY, axes=axis)

                position = self.stageY.qPOS(axis)[axis]  # query single axis
                self.outputCalibrText.append(
                    'current position of axis {} is {:.2f}'.format(axis, position))
                cursor = self.outputCalibrText.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                self.outputCalibrText.setTextCursor(cursor)

    # METHOD 4.1 - manual relative move up 1 mm

    def manualMoveUp(self):
        self.stageY.VEL(1, 10)
        self.stageY.MVR(1, 1)
        pitools.waitontarget(self.stageY, axes=1)

        self.outputManualText.append('Stage XY moved 1 mm up')
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 4.2 - manual relative move down 1 mm

    def manualMoveDown(self):
        self.stageY.VEL(1, 10)
        self.stageY.MVR(1, -1)
        pitools.waitontarget(self.stageY, axes=1)

        self.outputManualText.append('Stage XY moved 1 mm down')
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 4.3 - manual relative move left 1 mm

    def manualMoveLeft(self):
        self.stageX.VEL(1, 10)
        self.stageX.MVR(1, 1)
        pitools.waitontarget(self.stageX, axes=1)

        self.outputManualText.append('Stage XY moved 1 mm left')
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 4.4 - manual relative move right 1 mm

    def manualMoveRight(self):
        self.stageX.VEL(1, 10)
        self.stageX.MVR(1, -1)
        pitools.waitontarget(self.stageX, axes=1)

        self.outputManualText.append('Stage XY moved 1 mm right')
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 4.5 - manual move to (0,0)

    def manualMoveZero(self):
        self.stageY.VEL(1, 10)
        self.stageX.VEL(1, 10)
        self.stageY.MOV(1, 0)
        self.stageX.MOV(1, 0)
        pitools.waitontarget(self.stageX, axes=1)
        pitools.waitontarget(self.stageY, axes=1)

        self.outputManualText.append('Stage XY moved to (0,0)')
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 5.1 - Absolute Motion X

    def absoluteMoveX(self):
        input_textX = self.Xinput.text()  # Obtiene el texto introducido por el usuario

        # Comandos de movimiendo absoluto
        self.stageX.VEL(1, 10)
        self.stageX.MOV(1, input_textX)

        # Muestra movimiento en pantalla
        self.outputManualText.append('Moving to {} mm'.format(input_textX))
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 5.2 - Absolute Motion Y

    def absoluteMoveY(self):
        input_textY = self.Yinput.text()  # Obtiene el texto introducido por el usuario

        # Comandos de movimiendo absoluto
        self.stageY.VEL(1, 10)
        self.stageY.MOV(1, input_textY)

        # Muestra movimiento en pantalla
        self.outputManualText.append('Moving to {} mm'.format(input_textY))
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 6.1 - Conect with printer extruder motherboard via serial communication

    def conectExtruder(self):
        try:  # Se utiliza un bloque de manejo de excepciones para interceptar errores en la elección de puertos
            # Set serial communication with Arduino Mega 2560 (Marlin) / RUMBA controller

            # Selecciona los valores COM y Baud Rate por defecto para evitar errores si no se seleccionan
            self.COM_selected = self.comboBox.currentText()
            self.BR_selected = self.comboBox_2.currentText()

            # Establece la conexión serial
            self.ser1 = serial.Serial(
                self.COM_selected, self.BR_selected)  # Arduino Mega Marlin
            time.sleep(1)  # Must be here to avoid errors

            # Check if both serial connections are active
            if self.ser1.is_open:
                self.outputArdText.append(
                    '\nSerial connections are active and ready.')
                cursor = self.outputArdText.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                self.outputArdText.setTextCursor(cursor)
            else:
                self.outputArdText.append(
                    '\nError: Serial communications failed.')
                cursor = self.outputArdText.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)
                self.outputArdText.setTextCursor(cursor)

        except SerialException as e:
            error_message = str(e)
            self.outputArdText.append('\nError: ' + error_message)
            cursor = self.outputArdText.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.outputArdText.setTextCursor(cursor)

        canvas_widget = self.graph()  # Llama a la función para obtener el widget
        self.frame_50.setLayout(QVBoxLayout())
        self.frame_50.layout().addWidget(canvas_widget)

    # METHOD 6.2 - Conect with printer extruder motherboard via serial communication
    def COMvariable(self, index):
        self.COM_selected = self.comboBox.itemText(index)

    # METHOD 6.2 - Conect with printer extruder motherboard via serial communication
    def BRvariable(self, index):
        self.BR_selected = self.comboBox_2.itemText(index)

    # METHOD 7.1 - Set upper extruder heater temperature
    def upperExtrTemp(self):
        # Obtiene el texto introducido por el usuario
        input_tempUp = self.inputTemp1.text()

        # Comanda en GCode el calentamiento del bloque superior
        self.ser1.write(('M104 T0 S{}\n'.format(input_tempUp)).encode())

        # Muestra acción en pantalla
        self.outputManualText.append(
            'Heating Upper Block to {} C'.format(input_tempUp))
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 7.2 - Set lower extruder heater temperature
    def lowerExtrTemp(self):
        # Obtiene el texto introducido por el usuario
        input_tempDown = self.inputTemp2.text()

        # Comanda en GCode el calentamiento del bloque inferior
        self.ser1.write(('M104 T1 S{}\n'.format(input_tempDown)).encode())

        # Muestra acción en pantalla
        self.outputManualText.append(
            'Heating Lower Block to {} C'.format(input_tempDown))
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 7.3 - Set bed temperature
    def bedTemp(self):
        # Obtiene el texto introducido por el usuario
        input_tempBed = self.inputTemp3.text()

        # Comanda en GCode el calentamiento del sustrato
        self.ser1.write(('M140 S{}\n'.format(input_tempBed)).encode())

        # Muestra acción en pantalla
        self.outputManualText.append(
            'Heating bed to {} C'.format(input_tempBed))
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 8 - Set extrusion parameters and extrude
    def manualExtrude(self):
        # Obtiene el texto introducido por el usuario
        input_velExtr = self.inputDistextr.text()
        # Obtiene el texto introducido por el usuario
        input_distExtr = self.inputVelextr.text()

        if not input_velExtr or not input_distExtr:
            self.outputManualText.append(
                'Error: Introduzca valor en las casillas de distancia o velocidad.')
            cursor = self.outputManualText.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.outputManualText.setTextCursor(cursor)
            return  # Sale de la función si no se ingresaron valores

        # Comanda en GCode el movimiento del extrusor
        self.ser1.write(('M83\n').encode())
        self.ser1.write(
            ('G0 E-{} F{}\n'.format(input_distExtr, input_velExtr)).encode())

        # Muestra acción en pantalla
        self.outputManualText.append(
            'Extruding {} mm with {} mm/s'.format(input_distExtr, input_velExtr))
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # METHOD 9 - Manual Gcode
    def manualGcode(self):
        input_gcode = self.GcodeInput.toPlainText()
        gcode_lines = input_gcode.split('\n')

        for line in gcode_lines:
            if line.strip():  # Verifica si la línea no está vacía después de eliminar espacios en blanco
                self.ser1.write((line + '\n').encode())
        # Muestra acción en pantalla
        self.outputManualText.append('Sending G-Code...')
        cursor = self.outputManualText.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outputManualText.setTextCursor(cursor)

    # Método principal del GUI
    def setupUi(self, MainWindow):

        # VARIABLES DE LA INTERFAZ Y CONEXIÓN:
        self.stage_connected = False  # Flag para controlar la conexión

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(954, 549)
        font = QtGui.QFont()
        font.setPointSize(10)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet("*{\n"
                                 " border: none;\n"
                                 " background-color: transparent;\n"
                                 " background: transparent;\n"
                                 " padding:0;\n"
                                 " margin:0;\n"
                                 " color:#fff;\n"
                                 "}\n"
                                 "#centralwidget{\n"
                                 "   background-color: #1f232a;\n"
                                 "}\n"
                                 "#leftMenuSubContainer{\n"
                                 "   background-color: #16191d;\n"
                                 "}\n"
                                 "#leftMenuContainer QPushButton{\n"
                                 "text-align:left;\n"
                                 "padding:5px 10px;\n"
                                 "border-top-left-radius:10px;\n"
                                 "border-bottom-left-radius:10px;\n"
                                 "}\n"
                                 "#centerMenuSubContainer,#rightMenuSubContainer{\n"
                                 "background-color:#2c313c;\n"
                                 "}\n"
                                 "#frame_4,#frame_8{\n"
                                 "background-color:#16191d;\n"
                                 "border-radius:10px;\n"
                                 "}\n"
                                 "#headerContainer,#footerContainer{\n"
                                 "background-color:#2c313c;\n"
                                 "}\n"
                                 "#conectingStageBtn{\n"
                                 "background-color:#1c2126;\n"
                                 "border-radius:10px;\n"
                                 "}\n"
                                 "#outputConText,#outputArdText,#outputCalibrText,#outputManualText{\n"
                                 "background-color:#000000;\n"
                                 "}\n"
                                 "#zeroyBtn,#zeroxBtn,#conectSerialBtn{\n"
                                 "background-color: rgba(128, 0, 0, 0.6);\n"
                                 "border-radius:10px;\n"
                                 "}\n"
                                 "#Xinput,#Yinput,#inputTemp1,#inputTemp2,#inputTemp3,#inputDistextr,#inputVelextr{\n"
                                 "background-color: #8494a3;\n"
                                 "}\n"
                                 "#centerMenuSubContainer,#rightMenuSubContainer,#GcodeInput{\n"
                                 "background-color:#2c313c;\n"
                                 "border-radius:10px;\n"
                                 "}")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setMinimumSize(QtCore.QSize(0, 0))
        self.centralwidget.setObjectName("centralwidget")

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.leftMenuContainer = QCustomSlideMenu(self.centralwidget)
        self.leftMenuContainer.setMaximumSize(QtCore.QSize(50, 16777215))
        self.leftMenuContainer.setObjectName("leftMenuContainer")

        self.verticalLayout = QtWidgets.QVBoxLayout(self.leftMenuContainer)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")

        self.leftMenuSubContainer = QtWidgets.QWidget(self.leftMenuContainer)
        self.leftMenuSubContainer.setObjectName("leftMenuSubContainer")

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(
            self.leftMenuSubContainer)
        self.verticalLayout_2.setContentsMargins(5, 5, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.frame = QtWidgets.QFrame(self.leftMenuSubContainer)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        self.menuBtn = QtWidgets.QPushButton(self.frame)
        self.menuBtn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/align-justify.svg"),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.menuBtn.setIcon(icon)
        self.menuBtn.setIconSize(QtCore.QSize(24, 24))
        self.menuBtn.setObjectName("menuBtn")

        self.horizontalLayout_3.addWidget(self.menuBtn)

        self.verticalLayout_2.addWidget(self.frame, 0, QtCore.Qt.AlignTop)

        self.frame_2 = QtWidgets.QFrame(self.leftMenuSubContainer)
        self.frame_2.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")

        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_3.setContentsMargins(0, 10, 0, 10)
        self.verticalLayout_3.setSpacing(5)
        self.verticalLayout_3.setObjectName("verticalLayout_3")

        self.homeBtn = QtWidgets.QPushButton(self.frame_2)
        self.homeBtn.setStyleSheet("background-color: #1f232a;")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/home.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.homeBtn.setIcon(icon1)
        self.homeBtn.setIconSize(QtCore.QSize(24, 24))
        self.homeBtn.setObjectName("homeBtn")

        self.verticalLayout_3.addWidget(self.homeBtn)

        self.manualBtn = QtWidgets.QPushButton(self.frame_2)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/sliders.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.manualBtn.setIcon(icon2)
        self.manualBtn.setIconSize(QtCore.QSize(24, 24))
        self.manualBtn.setObjectName("manualBtn")

        self.verticalLayout_3.addWidget(self.manualBtn)

        self.gcodeBtn = QtWidgets.QPushButton(self.frame_2)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/code.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.gcodeBtn.setIcon(icon3)
        self.gcodeBtn.setIconSize(QtCore.QSize(24, 24))
        self.gcodeBtn.setObjectName("gcodeBtn")

        self.verticalLayout_3.addWidget(self.gcodeBtn)

        self.verticalLayout_2.addWidget(self.frame_2, 0, QtCore.Qt.AlignTop)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)

        self.frame_3 = QtWidgets.QFrame(self.leftMenuSubContainer)
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")

        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_4.setContentsMargins(0, 10, 0, 10)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")

        self.calibrationBtn = QtWidgets.QPushButton(self.frame_3)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/icons/settings.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.calibrationBtn.setIcon(icon4)
        self.calibrationBtn.setIconSize(QtCore.QSize(24, 24))
        self.calibrationBtn.setObjectName("calibrationBtn")

        self.verticalLayout_4.addWidget(self.calibrationBtn)

        self.helpBtn = QtWidgets.QPushButton(self.frame_3)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/icons/help-circle.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.helpBtn.setIcon(icon5)
        self.helpBtn.setIconSize(QtCore.QSize(24, 24))
        self.helpBtn.setObjectName("helpBtn")

        self.verticalLayout_4.addWidget(self.helpBtn)

        self.verticalLayout_2.addWidget(self.frame_3, 0, QtCore.Qt.AlignBottom)

        self.verticalLayout.addWidget(self.leftMenuSubContainer)

        self.horizontalLayout.addWidget(
            self.leftMenuContainer, 0, QtCore.Qt.AlignLeft)

        self.centerMenuContainer = QCustomSlideMenu(self.centralwidget)
        self.centerMenuContainer.setMinimumSize(QtCore.QSize(200, 0))
        self.centerMenuContainer.setObjectName("centerMenuContainer")

        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.centerMenuContainer)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")

        self.centerMenuSubContainer = QtWidgets.QWidget(
            self.centerMenuContainer)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.centerMenuSubContainer.sizePolicy().hasHeightForWidth())
        self.centerMenuSubContainer.setSizePolicy(sizePolicy)
        self.centerMenuSubContainer.setMinimumSize(QtCore.QSize(300, 0))
        self.centerMenuSubContainer.setObjectName("centerMenuSubContainer")

        self.verticalLayout_6 = QtWidgets.QVBoxLayout(
            self.centerMenuSubContainer)
        self.verticalLayout_6.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_6.setSpacing(5)
        self.verticalLayout_6.setObjectName("verticalLayout_6")

        self.frame_4 = QtWidgets.QFrame(self.centerMenuSubContainer)
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame_4)
        self.horizontalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.frame_4)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label, 0, QtCore.Qt.AlignLeft)

        self.closeCenterMenuBtn = QtWidgets.QPushButton(self.frame_4)
        self.closeCenterMenuBtn.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/icons/x-circle.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.closeCenterMenuBtn.setIcon(icon6)
        self.closeCenterMenuBtn.setIconSize(QtCore.QSize(24, 24))
        self.closeCenterMenuBtn.setObjectName("closeCenterMenuBtn")

        self.horizontalLayout_2.addWidget(
            self.closeCenterMenuBtn, 0, QtCore.Qt.AlignRight)

        self.verticalLayout_6.addWidget(self.frame_4, 0, QtCore.Qt.AlignTop)

        self.centerMenuPages = QCustomStackedWidget(
            self.centerMenuSubContainer)
        self.centerMenuPages.setObjectName("centerMenuPages")

        self.calibrationPage = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.calibrationPage.sizePolicy().hasHeightForWidth())
        self.calibrationPage.setSizePolicy(sizePolicy)
        self.calibrationPage.setObjectName("calibrationPage")

        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.calibrationPage)
        self.verticalLayout_7.setContentsMargins(0, 9, 0, 0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")

        self.widget = QtWidgets.QWidget(self.calibrationPage)
        self.widget.setObjectName("widget")

        self.verticalLayout_32 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_32.setObjectName("verticalLayout_32")

        self.frame_22 = QtWidgets.QFrame(self.widget)
        self.frame_22.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_22.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_22.setObjectName("frame_22")

        self.verticalLayout_28 = QtWidgets.QVBoxLayout(self.frame_22)
        self.verticalLayout_28.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_28.setSpacing(0)
        self.verticalLayout_28.setObjectName("verticalLayout_28")

        self.label_2 = QtWidgets.QLabel(self.frame_22)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")

        self.verticalLayout_28.addWidget(
            self.label_2, 0, QtCore.Qt.AlignHCenter)

        self.verticalLayout_32.addWidget(self.frame_22)

        self.frame_20 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(
            self.frame_20.sizePolicy().hasHeightForWidth())
        self.frame_20.setSizePolicy(sizePolicy)
        self.frame_20.setMinimumSize(QtCore.QSize(0, 80))
        self.frame_20.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_20.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_20.setObjectName("frame_20")

        self.verticalLayout_31 = QtWidgets.QVBoxLayout(self.frame_20)
        self.verticalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_31.setSpacing(0)
        self.verticalLayout_31.setObjectName("verticalLayout_31")

        self.label_19 = QtWidgets.QLabel(self.frame_20)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_19.setFont(font)
        self.label_19.setObjectName("label_19")

        self.verticalLayout_31.addWidget(
            self.label_19, 0, QtCore.Qt.AlignHCenter)

        self.zeroxBtn = QtWidgets.QPushButton(self.frame_20)
        self.zeroxBtn.setMinimumSize(QtCore.QSize(120, 30))
        self.zeroxBtn.setMaximumSize(QtCore.QSize(120, 30))
        self.zeroxBtn.setIconSize(QtCore.QSize(24, 24))
        self.zeroxBtn.setObjectName("zeroxBtn")

        self.verticalLayout_31.addWidget(
            self.zeroxBtn, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.verticalLayout_32.addWidget(
            self.frame_20, 0, QtCore.Qt.AlignVCenter)

        self.frame_19 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(
            self.frame_19.sizePolicy().hasHeightForWidth())
        self.frame_19.setSizePolicy(sizePolicy)
        self.frame_19.setMinimumSize(QtCore.QSize(0, 80))
        self.frame_19.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_19.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_19.setObjectName("frame_19")

        self.verticalLayout_30 = QtWidgets.QVBoxLayout(self.frame_19)
        self.verticalLayout_30.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_30.setSpacing(0)
        self.verticalLayout_30.setObjectName("verticalLayout_30")

        self.label_18 = QtWidgets.QLabel(self.frame_19)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_18.setFont(font)
        self.label_18.setObjectName("label_18")

        self.verticalLayout_30.addWidget(
            self.label_18, 0, QtCore.Qt.AlignHCenter)

        self.zeroyBtn = QtWidgets.QPushButton(self.frame_19)
        self.zeroyBtn.setMinimumSize(QtCore.QSize(120, 30))
        self.zeroyBtn.setMaximumSize(QtCore.QSize(120, 30))
        self.zeroyBtn.setIconSize(QtCore.QSize(24, 24))
        self.zeroyBtn.setObjectName("zeroyBtn")

        self.verticalLayout_30.addWidget(
            self.zeroyBtn, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.verticalLayout_32.addWidget(
            self.frame_19, 0, QtCore.Qt.AlignVCenter)

        self.frame_21 = QtWidgets.QFrame(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_21.sizePolicy().hasHeightForWidth())
        self.frame_21.setSizePolicy(sizePolicy)
        self.frame_21.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_21.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_21.setObjectName("frame_21")

        self.verticalLayout_29 = QtWidgets.QVBoxLayout(self.frame_21)
        self.verticalLayout_29.setContentsMargins(0, 20, 0, 5)
        self.verticalLayout_29.setSpacing(0)
        self.verticalLayout_29.setObjectName("verticalLayout_29")

        self.outputCalibrText = QtWidgets.QTextEdit(self.frame_21)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.outputCalibrText.sizePolicy().hasHeightForWidth())
        self.outputCalibrText.setSizePolicy(sizePolicy)
        self.outputCalibrText.setMinimumSize(QtCore.QSize(300, 0))
        self.outputCalibrText.setMaximumSize(QtCore.QSize(0, 120))
        self.outputCalibrText.setObjectName("outputCalibrText")
        self.outputCalibrText.setReadOnly(True)

        self.verticalLayout_29.addWidget(
            self.outputCalibrText, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.verticalLayout_32.addWidget(
            self.frame_21, 0, QtCore.Qt.AlignHCenter)

        self.verticalLayout_7.addWidget(self.widget, 0, QtCore.Qt.AlignHCenter)

        self.centerMenuPages.addWidget(self.calibrationPage)

        self.helpPage = QtWidgets.QWidget()
        self.helpPage.setObjectName("helpPage")

        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.helpPage)
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_9.setObjectName("verticalLayout_9")

        self.label_4 = QtWidgets.QLabel(self.helpPage)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")

        self.verticalLayout_9.addWidget(self.label_4)

        self.label_12 = QtWidgets.QLabel(self.helpPage)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy)
        self.label_12.setObjectName("label_12")

        self.verticalLayout_9.addWidget(
            self.label_12, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        self.centerMenuPages.addWidget(self.helpPage)

        self.verticalLayout_6.addWidget(self.centerMenuPages)

        self.verticalLayout_5.addWidget(
            self.centerMenuSubContainer, 0, QtCore.Qt.AlignHCenter)

        self.horizontalLayout.addWidget(self.centerMenuContainer)

        self.mainBodyContainer = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.mainBodyContainer.sizePolicy().hasHeightForWidth())
        self.mainBodyContainer.setSizePolicy(sizePolicy)
        self.mainBodyContainer.setStyleSheet("")
        self.mainBodyContainer.setObjectName("mainBodyContainer")

        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.mainBodyContainer)
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName("verticalLayout_10")

        self.headerContainer = QtWidgets.QWidget(self.mainBodyContainer)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.headerContainer.sizePolicy().hasHeightForWidth())
        self.headerContainer.setSizePolicy(sizePolicy)
        self.headerContainer.setObjectName("headerContainer")

        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.headerContainer)
        self.horizontalLayout_5.setContentsMargins(0, 9, 0, 9)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")

        self.frame_5 = QtWidgets.QFrame(self.headerContainer)
        self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_5.setObjectName("frame_5")

        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.frame_5)
        self.horizontalLayout_7.setContentsMargins(6, 0, 6, 0)
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")

        self.label_5 = QtWidgets.QLabel(self.frame_5)
        self.label_5.setMaximumSize(QtCore.QSize(100, 26))
        self.label_5.setText("")
        self.label_5.setPixmap(QtGui.QPixmap(":/images/images/usal.png"))
        self.label_5.setScaledContents(True)
        self.label_5.setObjectName("label_5")

        self.horizontalLayout_7.addWidget(self.label_5)

        self.horizontalLayout_5.addWidget(self.frame_5, 0, QtCore.Qt.AlignLeft)

        self.frame_6 = QtWidgets.QFrame(self.headerContainer)
        self.frame_6.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_6.setObjectName("frame_6")

        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.frame_6)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")

        self.stageConectBtn = QtWidgets.QPushButton(self.frame_6)
        self.stageConectBtn.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icons/icons/stage.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.stageConectBtn.setIcon(icon7)
        self.stageConectBtn.setIconSize(QtCore.QSize(25, 25))
        self.stageConectBtn.setObjectName("stageConectBtn")

        self.horizontalLayout_6.addWidget(self.stageConectBtn)

        self.extruderConectBtn = QtWidgets.QPushButton(self.frame_6)
        self.extruderConectBtn.setText("")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icons/icons/extruder.svg"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.extruderConectBtn.setIcon(icon8)
        self.extruderConectBtn.setIconSize(QtCore.QSize(25, 25))
        self.extruderConectBtn.setObjectName("extruderConectBtn")

        self.horizontalLayout_6.addWidget(self.extruderConectBtn)
        self.HVConectBtn = QtWidgets.QPushButton(self.frame_6)
        self.HVConectBtn.setText("")
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(
            ":/icons/icons/high-voltage.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.HVConectBtn.setIcon(icon9)
        self.HVConectBtn.setIconSize(QtCore.QSize(25, 25))
        self.HVConectBtn.setObjectName("HVConectBtn")
        self.horizontalLayout_6.addWidget(self.HVConectBtn)
        self.horizontalLayout_5.addWidget(
            self.frame_6, 0, QtCore.Qt.AlignHCenter)
        self.frame_7 = QtWidgets.QFrame(self.headerContainer)
        self.frame_7.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_7.setObjectName("frame_7")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.frame_7)
        self.horizontalLayout_4.setContentsMargins(6, 0, 6, 0)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.minimizeBtn = QtWidgets.QPushButton(self.frame_7)
        self.minimizeBtn.setText("")
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/icons/icons/minus.svg"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.minimizeBtn.setIcon(icon10)
        self.minimizeBtn.setIconSize(QtCore.QSize(16, 16))
        self.minimizeBtn.setObjectName("minimizeBtn")
        self.horizontalLayout_4.addWidget(self.minimizeBtn)
        self.restoreBtn = QtWidgets.QPushButton(self.frame_7)
        self.restoreBtn.setText("")
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/icons/icons/square.svg"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.restoreBtn.setIcon(icon11)
        self.restoreBtn.setIconSize(QtCore.QSize(16, 16))
        self.restoreBtn.setObjectName("restoreBtn")
        self.horizontalLayout_4.addWidget(self.restoreBtn)
        self.closeBtn = QtWidgets.QPushButton(self.frame_7)
        self.closeBtn.setText("")
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(":/icons/icons/x.svg"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.closeBtn.setIcon(icon12)
        self.closeBtn.setIconSize(QtCore.QSize(16, 16))
        self.closeBtn.setObjectName("closeBtn")
        self.horizontalLayout_4.addWidget(self.closeBtn)
        self.horizontalLayout_5.addWidget(
            self.frame_7, 0, QtCore.Qt.AlignRight)
        self.verticalLayout_10.addWidget(
            self.headerContainer, 0, QtCore.Qt.AlignTop)
        self.mainBodyContent = QtWidgets.QWidget(self.mainBodyContainer)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.mainBodyContent.sizePolicy().hasHeightForWidth())
        self.mainBodyContent.setSizePolicy(sizePolicy)
        self.mainBodyContent.setMinimumSize(QtCore.QSize(510, 351))
        self.mainBodyContent.setObjectName("mainBodyContent")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.mainBodyContent)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.mainContentsContainer = QtWidgets.QWidget(self.mainBodyContent)
        self.mainContentsContainer.setObjectName("mainContentsContainer")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(
            self.mainContentsContainer)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.mainPages = QCustomStackedWidget(self.mainContentsContainer)
        self.mainPages.setObjectName("mainPages")

        self.homePage = QtWidgets.QWidget()
        self.homePage.setObjectName("homePage")
        self.verticalLayout_18 = QtWidgets.QVBoxLayout(self.homePage)
        self.verticalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.frame_48 = QtWidgets.QFrame(self.homePage)
        self.frame_48.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_48.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_48.setObjectName("frame_48")
        self.verticalLayout_59 = QtWidgets.QVBoxLayout(self.frame_48)
        self.verticalLayout_59.setObjectName("verticalLayout_59")
        self.label_40 = QtWidgets.QLabel(self.frame_48)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.label_40.setFont(font)
        self.label_40.setObjectName("label_40")
        self.verticalLayout_59.addWidget(
            self.label_40, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.label_39 = QtWidgets.QLabel(self.frame_48)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_39.setFont(font)
        self.label_39.setObjectName("label_39")
        self.verticalLayout_59.addWidget(
            self.label_39, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.verticalLayout_18.addWidget(self.frame_48)
        self.frame_47 = QtWidgets.QFrame(self.homePage)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_47.sizePolicy().hasHeightForWidth())
        self.frame_47.setSizePolicy(sizePolicy)
        self.frame_47.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_47.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_47.setObjectName("frame_47")
        self.horizontalLayout_26 = QtWidgets.QHBoxLayout(self.frame_47)
        self.horizontalLayout_26.setObjectName("horizontalLayout_26")
        self.frame_49 = QtWidgets.QFrame(self.frame_47)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_49.sizePolicy().hasHeightForWidth())
        self.frame_49.setSizePolicy(sizePolicy)
        self.frame_49.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_49.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_49.setObjectName("frame_49")
        self.horizontalLayout_26.addWidget(self.frame_49)

        # Botones de impresión por defecto: tests, scaffolds, etc.
        self.frame_49 = QtWidgets.QFrame(self.frame_47)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_49.sizePolicy().hasHeightForWidth())
        self.frame_49.setSizePolicy(sizePolicy)
        self.frame_49.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_49.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_49.setObjectName("frame_49")
        self.verticalLayout_52 = QtWidgets.QVBoxLayout(self.frame_49)
        self.verticalLayout_52.setObjectName("verticalLayout_52")
        self.label_42 = QtWidgets.QLabel(self.frame_49)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_42.setFont(font)
        self.label_42.setObjectName("label_42")
        self.verticalLayout_52.addWidget(
            self.label_42, 0, QtCore.Qt.AlignHCenter)
        self.frame_41 = QtWidgets.QFrame(self.frame_49)
        self.frame_41.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_41.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_41.setObjectName("frame_41")
        self.horizontalLayout_24 = QtWidgets.QHBoxLayout(self.frame_41)
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")
        self.frame_51 = QtWidgets.QFrame(self.frame_41)
        self.frame_51.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_51.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_51.setObjectName("frame_51")
        self.verticalLayout_60 = QtWidgets.QVBoxLayout(self.frame_51)
        self.verticalLayout_60.setObjectName("verticalLayout_60")
        self.label_29 = QtWidgets.QLabel(self.frame_51)
        self.label_29.setObjectName("label_29")
        self.verticalLayout_60.addWidget(
            self.label_29, 0, QtCore.Qt.AlignHCenter)
        self.pushButton_2 = QtWidgets.QPushButton(self.frame_51)
        self.pushButton_2.setText("")
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("icons/velocity.png"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon13)
        self.pushButton_2.setIconSize(QtCore.QSize(100, 100))
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_60.addWidget(self.pushButton_2)
        self.horizontalLayout_24.addWidget(
            self.frame_51, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.frame_52 = QtWidgets.QFrame(self.frame_41)
        self.frame_52.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_52.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_52.setObjectName("frame_52")
        self.verticalLayout_61 = QtWidgets.QVBoxLayout(self.frame_52)
        self.verticalLayout_61.setObjectName("verticalLayout_61")
        self.label_32 = QtWidgets.QLabel(self.frame_52)
        self.label_32.setObjectName("label_32")
        self.verticalLayout_61.addWidget(
            self.label_32, 0, QtCore.Qt.AlignHCenter)
        self.pushButton_3 = QtWidgets.QPushButton(self.frame_52)
        self.pushButton_3.setText("")
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("icons/voltage.png"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_3.setIcon(icon14)
        self.pushButton_3.setIconSize(QtCore.QSize(100, 100))
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout_61.addWidget(self.pushButton_3)
        self.horizontalLayout_24.addWidget(
            self.frame_52, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.verticalLayout_52.addWidget(self.frame_41)
        self.frame_42 = QtWidgets.QFrame(self.frame_49)
        self.frame_42.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_42.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_42.setObjectName("frame_42")
        self.horizontalLayout_25 = QtWidgets.QHBoxLayout(self.frame_42)
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        self.frame_54 = QtWidgets.QFrame(self.frame_42)
        self.frame_54.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_54.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_54.setObjectName("frame_54")
        self.verticalLayout_63 = QtWidgets.QVBoxLayout(self.frame_54)
        self.verticalLayout_63.setObjectName("verticalLayout_63")
        self.label_34 = QtWidgets.QLabel(self.frame_54)
        self.label_34.setObjectName("label_34")
        self.verticalLayout_63.addWidget(
            self.label_34, 0, QtCore.Qt.AlignHCenter)
        self.pushButton_4 = QtWidgets.QPushButton(self.frame_54)
        self.pushButton_4.setText("")
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap("icons/2d.png"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_4.setIcon(icon15)
        self.pushButton_4.setIconSize(QtCore.QSize(100, 100))
        self.pushButton_4.setObjectName("pushButton_4")
        self.verticalLayout_63.addWidget(self.pushButton_4)
        self.horizontalLayout_25.addWidget(
            self.frame_54, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.frame_53 = QtWidgets.QFrame(self.frame_42)
        self.frame_53.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_53.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_53.setObjectName("frame_53")
        self.verticalLayout_62 = QtWidgets.QVBoxLayout(self.frame_53)
        self.verticalLayout_62.setObjectName("verticalLayout_62")
        self.label_41 = QtWidgets.QLabel(self.frame_53)
        self.label_41.setObjectName("label_41")
        self.verticalLayout_62.addWidget(
            self.label_41, 0, QtCore.Qt.AlignHCenter)
        self.pushButton_5 = QtWidgets.QPushButton(self.frame_53)
        self.pushButton_5.setText("")
        icon160 = QtGui.QIcon()
        icon160.addPixmap(QtGui.QPixmap("icons/3d.png"),
                          QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_5.setIcon(icon160)
        self.pushButton_5.setIconSize(QtCore.QSize(100, 100))
        self.pushButton_5.setObjectName("pushButton_5")
        self.verticalLayout_62.addWidget(self.pushButton_5)
        self.horizontalLayout_25.addWidget(
            self.frame_53, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.verticalLayout_52.addWidget(self.frame_42)
        self.horizontalLayout_26.addWidget(self.frame_49)

        self.frame_50 = QtWidgets.QFrame(self.frame_47)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_50.sizePolicy().hasHeightForWidth())
        self.frame_50.setSizePolicy(sizePolicy)
        self.frame_50.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_50.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_50.setObjectName("frame_50")
        self.horizontalLayout_26.addWidget(self.frame_50)

        self.verticalLayout_18.addWidget(self.frame_47)
        self.mainPages.addWidget(self.homePage)
        self.manualPage = QtWidgets.QWidget()
        self.manualPage.setObjectName("manualPage")
        self.verticalLayout_17 = QtWidgets.QVBoxLayout(self.manualPage)
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.widget_5 = QtWidgets.QWidget(self.manualPage)
        self.widget_5.setObjectName("widget_5")
        self.verticalLayout_38 = QtWidgets.QVBoxLayout(self.widget_5)
        self.verticalLayout_38.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_38.setSpacing(0)
        self.verticalLayout_38.setObjectName("verticalLayout_38")
        self.frame_27 = QtWidgets.QFrame(self.widget_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_27.sizePolicy().hasHeightForWidth())
        self.frame_27.setSizePolicy(sizePolicy)
        self.frame_27.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_27.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_27.setObjectName("frame_27")
        self.verticalLayout_37 = QtWidgets.QVBoxLayout(self.frame_27)
        self.verticalLayout_37.setContentsMargins(0, 0, 0, 5)
        self.verticalLayout_37.setSpacing(3)
        self.verticalLayout_37.setObjectName("verticalLayout_37")
        self.label_10 = QtWidgets.QLabel(self.frame_27)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_37.addWidget(
            self.label_10, 0, QtCore.Qt.AlignHCenter)
        self.label_11 = QtWidgets.QLabel(self.frame_27)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.verticalLayout_37.addWidget(
            self.label_11, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout_38.addWidget(
            self.frame_27, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.widget_6 = QtWidgets.QWidget(self.widget_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.widget_6.sizePolicy().hasHeightForWidth())
        self.widget_6.setSizePolicy(sizePolicy)
        self.widget_6.setObjectName("widget_6")
        self.verticalLayout_36 = QtWidgets.QVBoxLayout(self.widget_6)
        self.verticalLayout_36.setContentsMargins(0, 15, 0, 0)
        self.verticalLayout_36.setSpacing(0)
        self.verticalLayout_36.setObjectName("verticalLayout_36")
        self.widget_7 = QtWidgets.QWidget(self.widget_6)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.widget_7.sizePolicy().hasHeightForWidth())
        self.widget_7.setSizePolicy(sizePolicy)
        self.widget_7.setObjectName("widget_7")
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout(self.widget_7)
        self.horizontalLayout_14.setContentsMargins(30, 5, -1, 3)
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.frame_25 = QtWidgets.QFrame(self.widget_7)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_25.sizePolicy().hasHeightForWidth())
        self.frame_25.setSizePolicy(sizePolicy)
        self.frame_25.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_25.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_25.setObjectName("frame_25")
        self.verticalLayout_39 = QtWidgets.QVBoxLayout(self.frame_25)
        self.verticalLayout_39.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_39.setSpacing(0)
        self.verticalLayout_39.setObjectName("verticalLayout_39")
        self.label_20 = QtWidgets.QLabel(self.frame_25)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_20.setFont(font)
        self.label_20.setObjectName("label_20")
        self.verticalLayout_39.addWidget(
            self.label_20, 0, QtCore.Qt.AlignHCenter)
        self.frameUp = QtWidgets.QFrame(self.frame_25)
        self.frameUp.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameUp.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frameUp.setObjectName("frameUp")
        self.verticalLayout_41 = QtWidgets.QVBoxLayout(self.frameUp)
        self.verticalLayout_41.setContentsMargins(0, 8, 0, 5)
        self.verticalLayout_41.setSpacing(0)
        self.verticalLayout_41.setObjectName("verticalLayout_41")
        self.upBtn = QtWidgets.QPushButton(self.frameUp)
        self.upBtn.setText("")
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap(
            ":/icons/icons/arrow-up-circle.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.upBtn.setIcon(icon13)
        self.upBtn.setIconSize(QtCore.QSize(25, 25))
        self.upBtn.setObjectName("upBtn")
        self.verticalLayout_41.addWidget(self.upBtn)
        # Llama a la función con el código que lanza el botón
        self.upBtn.clicked.connect(self.manualMoveUp)

        self.verticalLayout_39.addWidget(self.frameUp)
        self.frame_30 = QtWidgets.QFrame(self.frame_25)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_30.sizePolicy().hasHeightForWidth())
        self.frame_30.setSizePolicy(sizePolicy)
        self.frame_30.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_30.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_30.setObjectName("frame_30")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.frame_30)
        self.horizontalLayout_15.setContentsMargins(0, 1, 0, 1)
        self.horizontalLayout_15.setSpacing(10)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.frameLeft = QtWidgets.QFrame(self.frame_30)
        self.frameLeft.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frameLeft.setObjectName("frameLeft")
        self.verticalLayout_42 = QtWidgets.QVBoxLayout(self.frameLeft)
        self.verticalLayout_42.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_42.setSpacing(0)
        self.verticalLayout_42.setObjectName("verticalLayout_42")
        self.leftBtn = QtWidgets.QPushButton(self.frameLeft)
        self.leftBtn.setText("")
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap(
            ":/icons/icons/arrow-left-circle.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.leftBtn.setIcon(icon14)
        self.leftBtn.setIconSize(QtCore.QSize(25, 25))
        self.leftBtn.setObjectName("leftBtn")
        self.verticalLayout_42.addWidget(self.leftBtn)
        # Llama a la función con el código que lanza el botón
        self.leftBtn.clicked.connect(self.manualMoveLeft)

        self.horizontalLayout_15.addWidget(self.frameLeft)
        self.zeroFrame = QtWidgets.QFrame(self.frame_30)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.zeroFrame.sizePolicy().hasHeightForWidth())
        self.zeroFrame.setSizePolicy(sizePolicy)
        self.zeroFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.zeroFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.zeroFrame.setObjectName("zeroFrame")
        self.verticalLayout_44 = QtWidgets.QVBoxLayout(self.zeroFrame)
        self.verticalLayout_44.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_44.setSpacing(0)
        self.verticalLayout_44.setObjectName("verticalLayout_44")
        self.zeroBtn = QtWidgets.QPushButton(self.zeroFrame)
        self.zeroBtn.setText("")
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap(":/icons/icons/circle.svg"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.zeroBtn.setIcon(icon15)
        self.zeroBtn.setObjectName("zeroBtn")
        self.verticalLayout_44.addWidget(self.zeroBtn)
        # Llama a la función con el código que lanza el botón
        self.zeroBtn.clicked.connect(self.manualMoveZero)

        self.horizontalLayout_15.addWidget(self.zeroFrame)
        self.frameRight = QtWidgets.QFrame(self.frame_30)
        self.frameRight.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameRight.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frameRight.setObjectName("frameRight")
        self.verticalLayout_43 = QtWidgets.QVBoxLayout(self.frameRight)
        self.verticalLayout_43.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_43.setSpacing(0)
        self.verticalLayout_43.setObjectName("verticalLayout_43")
        self.rightBtn = QtWidgets.QPushButton(self.frameRight)
        self.rightBtn.setText("")
        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap(
            ":/icons/icons/arrow-right-circle.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.rightBtn.setIcon(icon16)
        self.rightBtn.setIconSize(QtCore.QSize(25, 25))
        self.rightBtn.setObjectName("rightBtn")
        self.verticalLayout_43.addWidget(self.rightBtn)
        # Llama a la función con el código que lanza el botón
        self.rightBtn.clicked.connect(self.manualMoveRight)

        self.horizontalLayout_15.addWidget(self.frameRight)
        self.verticalLayout_39.addWidget(self.frame_30)
        self.frame_down = QtWidgets.QFrame(self.frame_25)
        self.frame_down.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_down.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_down.setObjectName("frame_down")
        self.verticalLayout_40 = QtWidgets.QVBoxLayout(self.frame_down)
        self.verticalLayout_40.setContentsMargins(0, 5, 0, 5)
        self.verticalLayout_40.setSpacing(0)
        self.verticalLayout_40.setObjectName("verticalLayout_40")
        self.downBtn = QtWidgets.QPushButton(self.frame_down)
        self.downBtn.setText("")
        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap(
            ":/icons/icons/arrow-down-circle.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.downBtn.setIcon(icon17)
        self.downBtn.setIconSize(QtCore.QSize(25, 25))
        self.downBtn.setObjectName("downBtn")
        # Llama a la función con el código que lanza el botón
        self.downBtn.clicked.connect(self.manualMoveDown)

        self.verticalLayout_40.addWidget(self.downBtn)
        self.verticalLayout_39.addWidget(self.frame_down)
        self.horizontalLayout_14.addWidget(self.frame_25)
        self.frame_26 = QtWidgets.QFrame(self.widget_7)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_26.sizePolicy().hasHeightForWidth())
        self.frame_26.setSizePolicy(sizePolicy)
        self.frame_26.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_26.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_26.setObjectName("frame_26")
        self.horizontalLayout_20 = QtWidgets.QHBoxLayout(self.frame_26)
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")
        self.frame_40 = QtWidgets.QFrame(self.frame_26)
        self.frame_40.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_40.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_40.setObjectName("frame_40")
        self.verticalLayout_47 = QtWidgets.QVBoxLayout(self.frame_40)
        self.verticalLayout_47.setContentsMargins(60, 0, 50, 0)
        self.verticalLayout_47.setSpacing(0)
        self.verticalLayout_47.setObjectName("verticalLayout_47")
        self.widget_11 = QtWidgets.QWidget(self.frame_40)
        self.widget_11.setObjectName("widget_11")
        self.verticalLayout_48 = QtWidgets.QVBoxLayout(self.widget_11)
        self.verticalLayout_48.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_48.setSpacing(0)
        self.verticalLayout_48.setObjectName("verticalLayout_48")
        self.label_28 = QtWidgets.QLabel(self.widget_11)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_28.setFont(font)
        self.label_28.setObjectName("label_28")
        self.verticalLayout_48.addWidget(
            self.label_28, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.verticalLayout_47.addWidget(
            self.widget_11, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.widget_10 = QtWidgets.QWidget(self.frame_40)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.widget_10.sizePolicy().hasHeightForWidth())
        self.widget_10.setSizePolicy(sizePolicy)
        self.widget_10.setObjectName("widget_10")
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout(self.widget_10)
        self.horizontalLayout_21.setContentsMargins(0, 0, 0, 15)
        self.horizontalLayout_21.setSpacing(0)
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.frame_33 = QtWidgets.QFrame(self.widget_10)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_33.sizePolicy().hasHeightForWidth())
        self.frame_33.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.frame_33.setFont(font)
        self.frame_33.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_33.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_33.setObjectName("frame_33")
        self.verticalLayout_49 = QtWidgets.QVBoxLayout(self.frame_33)
        self.verticalLayout_49.setObjectName("verticalLayout_49")
        self.label_25 = QtWidgets.QLabel(self.frame_33)
        self.label_25.setMinimumSize(QtCore.QSize(0, 0))
        self.label_25.setObjectName("label_25")
        self.verticalLayout_49.addWidget(
            self.label_25, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        self.inputTemp1 = QtWidgets.QLineEdit(self.frame_33)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inputTemp1.sizePolicy().hasHeightForWidth())
        self.inputTemp1.setSizePolicy(sizePolicy)
        self.inputTemp1.setMinimumSize(QtCore.QSize(0, 0))
        self.inputTemp1.setMaximumSize(QtCore.QSize(60, 16777215))
        self.inputTemp1.setObjectName("inputTemp1")
        self.verticalLayout_49.addWidget(self.inputTemp1)
        # Lanza la función cuando el usuario pulsa intro
        self.inputTemp1.returnPressed.connect(self.upperExtrTemp)

        self.horizontalLayout_21.addWidget(
            self.frame_33, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.frame_36 = QtWidgets.QFrame(self.widget_10)
        self.frame_36.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_36.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_36.setObjectName("frame_36")
        self.verticalLayout_50 = QtWidgets.QVBoxLayout(self.frame_36)
        self.verticalLayout_50.setObjectName("verticalLayout_50")
        self.label_27 = QtWidgets.QLabel(self.frame_36)
        self.label_27.setMinimumSize(QtCore.QSize(0, 0))
        self.label_27.setObjectName("label_27")
        self.verticalLayout_50.addWidget(
            self.label_27, 0, QtCore.Qt.AlignHCenter)

        self.inputTemp2 = QtWidgets.QLineEdit(self.frame_36)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inputTemp2.sizePolicy().hasHeightForWidth())
        self.inputTemp2.setSizePolicy(sizePolicy)
        self.inputTemp2.setMaximumSize(QtCore.QSize(60, 16777215))
        self.inputTemp2.setObjectName("inputTemp2")
        self.verticalLayout_50.addWidget(self.inputTemp2)
        # Lanza la función cuando el usuario pulsa intro
        self.inputTemp2.returnPressed.connect(self.lowerExtrTemp)

        self.horizontalLayout_21.addWidget(
            self.frame_36, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.frame_39 = QtWidgets.QFrame(self.widget_10)
        self.frame_39.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_39.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_39.setObjectName("frame_39")
        self.verticalLayout_51 = QtWidgets.QVBoxLayout(self.frame_39)
        self.verticalLayout_51.setObjectName("verticalLayout_51")
        self.label_26 = QtWidgets.QLabel(self.frame_39)
        self.label_26.setObjectName("label_26")
        self.verticalLayout_51.addWidget(
            self.label_26, 0, QtCore.Qt.AlignHCenter)

        self.inputTemp3 = QtWidgets.QLineEdit(self.frame_39)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inputTemp3.sizePolicy().hasHeightForWidth())
        self.inputTemp3.setSizePolicy(sizePolicy)
        self.inputTemp3.setMaximumSize(QtCore.QSize(60, 16777215))
        self.inputTemp3.setObjectName("inputTemp3")
        self.verticalLayout_51.addWidget(self.inputTemp3)
        # Lanza la función cuando el usuario pulsa intro
        self.inputTemp3.returnPressed.connect(self.bedTemp)

        self.horizontalLayout_21.addWidget(
            self.frame_39, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.verticalLayout_47.addWidget(
            self.widget_10, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.horizontalLayout_20.addWidget(self.frame_40)
        self.frame_34 = QtWidgets.QFrame(self.frame_26)
        self.frame_34.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_34.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_34.setObjectName("frame_34")
        self.verticalLayout_46 = QtWidgets.QVBoxLayout(self.frame_34)
        self.verticalLayout_46.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_46.setSpacing(0)
        self.verticalLayout_46.setObjectName("verticalLayout_46")
        self.label_24 = QtWidgets.QLabel(self.frame_34)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_24.setFont(font)
        self.label_24.setObjectName("label_24")
        self.verticalLayout_46.addWidget(
            self.label_24, 0, QtCore.Qt.AlignHCenter)
        self.frame_38 = QtWidgets.QFrame(self.frame_34)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_38.sizePolicy().hasHeightForWidth())
        self.frame_38.setSizePolicy(sizePolicy)
        self.frame_38.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_38.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_38.setObjectName("frame_38")
        self.horizontalLayout_23 = QtWidgets.QHBoxLayout(self.frame_38)
        self.horizontalLayout_23.setContentsMargins(0, 60, 0, 10)
        self.horizontalLayout_23.setSpacing(0)
        self.horizontalLayout_23.setObjectName("horizontalLayout_23")
        self.label_30 = QtWidgets.QLabel(self.frame_38)
        self.label_30.setMinimumSize(QtCore.QSize(0, 0))
        self.label_30.setObjectName("label_30")
        self.horizontalLayout_23.addWidget(
            self.label_30, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.inputDistextr = QtWidgets.QLineEdit(self.frame_38)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        sizePolicy.setHeightForWidth(
            self.inputDistextr.sizePolicy().hasHeightForWidth())
        self.inputDistextr.setSizePolicy(sizePolicy)
        self.inputDistextr.setMinimumSize(QtCore.QSize(0, 0))
        self.inputDistextr.setMaximumSize(QtCore.QSize(60, 16777215))
        self.inputDistextr.setObjectName("inputDistextr")
        self.horizontalLayout_23.addWidget(
            self.inputDistextr, 0, QtCore.Qt.AlignLeft)
        # Lanza la función cuando el usuario pulsa intro
        self.inputDistextr.returnPressed.connect(self.manualExtrude)

        self.verticalLayout_46.addWidget(
            self.frame_38, 0, QtCore.Qt.AlignHCenter)
        self.frame_37 = QtWidgets.QFrame(self.frame_34)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_37.sizePolicy().hasHeightForWidth())
        self.frame_37.setSizePolicy(sizePolicy)
        self.frame_37.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_37.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_37.setObjectName("frame_37")
        self.horizontalLayout_22 = QtWidgets.QHBoxLayout(self.frame_37)
        self.horizontalLayout_22.setContentsMargins(0, 0, 0, 20)
        self.horizontalLayout_22.setSpacing(0)
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")
        self.label_31 = QtWidgets.QLabel(self.frame_37)
        self.label_31.setMinimumSize(QtCore.QSize(0, 0))
        self.label_31.setObjectName("label_31")
        self.horizontalLayout_22.addWidget(
            self.label_31, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.inputVelextr = QtWidgets.QLineEdit(self.frame_37)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        sizePolicy.setHeightForWidth(
            self.inputVelextr.sizePolicy().hasHeightForWidth())
        self.inputVelextr.setSizePolicy(sizePolicy)
        self.inputVelextr.setMinimumSize(QtCore.QSize(0, 0))
        self.inputVelextr.setMaximumSize(QtCore.QSize(60, 16777215))
        self.inputVelextr.setObjectName("inputVelextr")
        self.horizontalLayout_22.addWidget(self.inputVelextr)
        # Lanza la función cuando el usuario pulsa intro
        self.inputVelextr.returnPressed.connect(self.manualExtrude)

        self.verticalLayout_46.addWidget(
            self.frame_37, 0, QtCore.Qt.AlignHCenter)
        self.horizontalLayout_20.addWidget(
            self.frame_34, 0, QtCore.Qt.AlignVCenter)
        self.horizontalLayout_14.addWidget(self.frame_26)
        self.verticalLayout_36.addWidget(self.widget_7)
        self.widget_8 = QtWidgets.QWidget(self.widget_6)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.widget_8.sizePolicy().hasHeightForWidth())
        self.widget_8.setSizePolicy(sizePolicy)
        self.widget_8.setObjectName("widget_8")
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout(self.widget_8)
        self.horizontalLayout_17.setContentsMargins(20, 0, -1, 10)
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.frame_29 = QtWidgets.QFrame(self.widget_8)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_29.sizePolicy().hasHeightForWidth())
        self.frame_29.setSizePolicy(sizePolicy)
        self.frame_29.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_29.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_29.setObjectName("frame_29")
        self.verticalLayout_45 = QtWidgets.QVBoxLayout(self.frame_29)
        self.verticalLayout_45.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_45.setSpacing(0)
        self.verticalLayout_45.setObjectName("verticalLayout_45")
        self.label_21 = QtWidgets.QLabel(self.frame_29)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_21.setFont(font)
        self.label_21.setObjectName("label_21")
        self.verticalLayout_45.addWidget(
            self.label_21, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.frame_31 = QtWidgets.QFrame(self.frame_29)
        self.frame_31.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_31.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_31.setObjectName("frame_31")
        self.horizontalLayout_18 = QtWidgets.QHBoxLayout(self.frame_31)
        self.horizontalLayout_18.setContentsMargins(0, 3, 0, 0)
        self.horizontalLayout_18.setSpacing(0)
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.label_22 = QtWidgets.QLabel(self.frame_31)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label_22.setFont(font)
        self.label_22.setObjectName("label_22")
        self.horizontalLayout_18.addWidget(self.label_22)
        self.Xinput = QtWidgets.QLineEdit(self.frame_31)
        self.Xinput.setMinimumSize(QtCore.QSize(70, 0))
        self.Xinput.setMaximumSize(QtCore.QSize(70, 20))
        self.Xinput.setObjectName("Xinput")
        self.horizontalLayout_18.addWidget(self.Xinput)
        # Lanza la función cuando el usuario pulsa intro
        self.Xinput.returnPressed.connect(self.absoluteMoveX)

        self.verticalLayout_45.addWidget(
            self.frame_31, 0, QtCore.Qt.AlignHCenter)
        self.frame_32 = QtWidgets.QFrame(self.frame_29)
        self.frame_32.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_32.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_32.setObjectName("frame_32")
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout(self.frame_32)
        self.horizontalLayout_16.setContentsMargins(0, 0, 0, 20)
        self.horizontalLayout_16.setSpacing(0)
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label_23 = QtWidgets.QLabel(self.frame_32)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setBold(True)
        font.setWeight(75)
        self.label_23.setFont(font)
        self.label_23.setObjectName("label_23")
        self.horizontalLayout_16.addWidget(self.label_23)
        self.Yinput = QtWidgets.QLineEdit(self.frame_32)
        self.Yinput.setMinimumSize(QtCore.QSize(70, 0))
        self.Yinput.setMaximumSize(QtCore.QSize(70, 20))
        self.Yinput.setObjectName("Yinput")
        self.horizontalLayout_16.addWidget(self.Yinput)
        # Lanza la función cuando el usuario pulsa intro
        self.Yinput.returnPressed.connect(self.absoluteMoveY)

        self.verticalLayout_45.addWidget(
            self.frame_32, 0, QtCore.Qt.AlignHCenter)
        self.horizontalLayout_17.addWidget(self.frame_29)
        self.frame_28 = QtWidgets.QFrame(self.widget_8)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_28.sizePolicy().hasHeightForWidth())
        self.frame_28.setSizePolicy(sizePolicy)
        self.frame_28.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_28.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_28.setObjectName("frame_28")
        self.verticalLayout_53 = QtWidgets.QVBoxLayout(self.frame_28)
        self.verticalLayout_53.setContentsMargins(130, 12, 0, 0)
        self.verticalLayout_53.setSpacing(0)
        self.verticalLayout_53.setObjectName("verticalLayout_53")
        self.widget_13 = QtWidgets.QWidget(self.frame_28)
        self.widget_13.setObjectName("widget_13")
        self.verticalLayout_56 = QtWidgets.QVBoxLayout(self.widget_13)
        self.verticalLayout_56.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_56.setSpacing(0)
        self.verticalLayout_56.setObjectName("verticalLayout_56")
        self.label_33 = QtWidgets.QLabel(self.widget_13)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_33.setFont(font)
        self.label_33.setObjectName("label_33")
        self.verticalLayout_56.addWidget(
            self.label_33, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.verticalLayout_53.addWidget(
            self.widget_13, 0, QtCore.Qt.AlignHCenter)
        self.widget_12 = QtWidgets.QWidget(self.frame_28)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.widget_12.sizePolicy().hasHeightForWidth())
        self.widget_12.setSizePolicy(sizePolicy)
        self.widget_12.setObjectName("widget_12")
        self.horizontalLayout_27 = QtWidgets.QHBoxLayout(self.widget_12)
        self.horizontalLayout_27.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_27.setSpacing(0)
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.frame_44 = QtWidgets.QFrame(self.widget_12)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_44.sizePolicy().hasHeightForWidth())
        self.frame_44.setSizePolicy(sizePolicy)
        self.frame_44.setMaximumSize(QtCore.QSize(1000, 1000))
        self.frame_44.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_44.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_44.setObjectName("frame_44")
        self.verticalLayout_55 = QtWidgets.QVBoxLayout(self.frame_44)
        self.verticalLayout_55.setContentsMargins(0, 8, 5, 7)
        self.verticalLayout_55.setSpacing(0)
        self.verticalLayout_55.setObjectName("verticalLayout_55")
        self.GcodeInput = QtWidgets.QPlainTextEdit(self.frame_44)
        self.GcodeInput.setMinimumSize(QtCore.QSize(400, 10))
        self.GcodeInput.setMaximumSize(QtCore.QSize(300, 70))
        self.GcodeInput.setObjectName("GcodeInput")
        self.verticalLayout_55.addWidget(self.GcodeInput)
        self.horizontalLayout_27.addWidget(
            self.frame_44, 0, QtCore.Qt.AlignHCenter)
        self.frame_43 = QtWidgets.QFrame(self.widget_12)
        self.frame_43.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_43.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_43.setObjectName("frame_43")
        self.verticalLayout_54 = QtWidgets.QVBoxLayout(self.frame_43)
        self.verticalLayout_54.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_54.setSpacing(0)
        self.verticalLayout_54.setObjectName("verticalLayout_54")

        # Botón - Enviar Gcode manual
        self.pushButton = QtWidgets.QPushButton(self.frame_43)
        self.pushButton.setText("")
        icon18 = QtGui.QIcon()
        icon18.addPixmap(QtGui.QPixmap(
            ":/icons/icons/corner-down-left.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon18)
        self.pushButton.setIconSize(QtCore.QSize(20, 20))
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_54.addWidget(self.pushButton)
        self.pushButton.clicked.connect(self.manualGcode)

        self.horizontalLayout_27.addWidget(self.frame_43)
        self.verticalLayout_53.addWidget(
            self.widget_12, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.horizontalLayout_17.addWidget(self.frame_28)
        self.verticalLayout_36.addWidget(self.widget_8)
        self.widget_9 = QtWidgets.QWidget(self.widget_6)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.widget_9.sizePolicy().hasHeightForWidth())
        self.widget_9.setSizePolicy(sizePolicy)
        self.widget_9.setMaximumSize(QtCore.QSize(16777215, 500))
        self.widget_9.setSizeIncrement(QtCore.QSize(0, 0))
        self.widget_9.setObjectName("widget_9")
        self.horizontalLayout_19 = QtWidgets.QHBoxLayout(self.widget_9)
        self.horizontalLayout_19.setContentsMargins(0, 15, 0, 0)
        self.horizontalLayout_19.setSpacing(0)
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.outputManualText = QtWidgets.QTextEdit(self.widget_9)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.outputManualText.sizePolicy().hasHeightForWidth())
        self.outputManualText.setSizePolicy(sizePolicy)
        self.outputManualText.setMinimumSize(QtCore.QSize(715, 0))
        self.outputManualText.setMaximumSize(QtCore.QSize(0, 100))
        self.outputManualText.setObjectName("outputManualText")
        self.horizontalLayout_19.addWidget(self.outputManualText)
        self.outputManualText.setReadOnly(True)

        self.verticalLayout_36.addWidget(self.widget_9)
        self.verticalLayout_38.addWidget(
            self.widget_6, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout_17.addWidget(
            self.widget_5, 0, QtCore.Qt.AlignHCenter)
        self.mainPages.addWidget(self.manualPage)
        self.gcodePage = QtWidgets.QWidget()
        self.gcodePage.setObjectName("gcodePage")
        self.verticalLayout_16 = QtWidgets.QVBoxLayout(self.gcodePage)
        self.verticalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.frame_45 = QtWidgets.QFrame(self.gcodePage)
        self.frame_45.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_45.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_45.setObjectName("frame_45")
        self.verticalLayout_58 = QtWidgets.QVBoxLayout(self.frame_45)
        self.verticalLayout_58.setObjectName("verticalLayout_58")
        self.label_36 = QtWidgets.QLabel(self.frame_45)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.label_36.setFont(font)
        self.label_36.setObjectName("label_36")
        self.verticalLayout_58.addWidget(
            self.label_36, 0, QtCore.Qt.AlignHCenter)
        self.label_37 = QtWidgets.QLabel(self.frame_45)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_37.setFont(font)
        self.label_37.setObjectName("label_37")
        self.verticalLayout_58.addWidget(
            self.label_37, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.label_35 = QtWidgets.QLabel(self.frame_45)
        self.label_35.setText("")
        self.label_35.setObjectName("label_35")
        self.verticalLayout_58.addWidget(
            self.label_35, 0, QtCore.Qt.AlignHCenter)
        self.label_38 = QtWidgets.QLabel(self.frame_45)
        self.label_38.setObjectName("label_38")
        self.verticalLayout_58.addWidget(
            self.label_38, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout_16.addWidget(self.frame_45)

        # Create a QMainWindow instance for TextFileReader
        text_file_reader_window = TextFileReader()

        # Call the initUI() method to initialize the user interface components
        text_file_reader_window.initUI()

        # Create a QFrame instance for your existing code
        self.frame_35 = QtWidgets.QFrame(self.gcodePage)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_35.sizePolicy().hasHeightForWidth())
        self.frame_35.setSizePolicy(sizePolicy)
        self.frame_35.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_35.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_35.setObjectName("frame_35")

        # Create a QVBoxLayout for the QFrame to hold the TextFileReader window
        frame_layout = QVBoxLayout(self.frame_35)
        frame_layout.addWidget(text_file_reader_window)

        # Add the QFrame to your existing layout
        self.verticalLayout_16.addWidget(self.frame_35)

        # Optionally, show the TextFileReader window
        text_file_reader_window.show()

        self.frame_46 = QtWidgets.QFrame(self.gcodePage)
        self.frame_46.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_46.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_46.setObjectName("frame_46")
        self.verticalLayout_57 = QtWidgets.QVBoxLayout(self.frame_46)
        self.verticalLayout_57.setObjectName("verticalLayout_57")

        self.verticalLayout_16.addWidget(
            self.frame_46, 0, QtCore.Qt.AlignVCenter)
        self.mainPages.addWidget(self.gcodePage)
        self.verticalLayout_8.addWidget(self.mainPages)
        self.horizontalLayout_8.addWidget(self.mainContentsContainer)
        self.rightMenuContainer = QCustomSlideMenu(self.mainBodyContent)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.rightMenuContainer.sizePolicy().hasHeightForWidth())
        self.rightMenuContainer.setSizePolicy(sizePolicy)
        self.rightMenuContainer.setMinimumSize(QtCore.QSize(300, 0))
        self.rightMenuContainer.setMaximumSize(QtCore.QSize(200, 333))
        self.rightMenuContainer.setObjectName("rightMenuContainer")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.rightMenuContainer)
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.rightMenuSubContainer = QtWidgets.QWidget(self.rightMenuContainer)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.rightMenuSubContainer.sizePolicy().hasHeightForWidth())
        self.rightMenuSubContainer.setSizePolicy(sizePolicy)
        self.rightMenuSubContainer.setObjectName("rightMenuSubContainer")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(
            self.rightMenuSubContainer)
        self.verticalLayout_12.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_12.setSpacing(5)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.frame_8 = QtWidgets.QFrame(self.rightMenuSubContainer)
        self.frame_8.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_8.setObjectName("frame_8")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.frame_8)
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_6 = QtWidgets.QLabel(self.frame_8)
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_9.addWidget(self.label_6, 0, QtCore.Qt.AlignLeft)
        self.closeRightMenuBtn = QtWidgets.QPushButton(self.frame_8)
        self.closeRightMenuBtn.setText("")
        self.closeRightMenuBtn.setIcon(icon6)
        self.closeRightMenuBtn.setIconSize(QtCore.QSize(24, 24))
        self.closeRightMenuBtn.setObjectName("closeRightMenuBtn")
        self.horizontalLayout_9.addWidget(
            self.closeRightMenuBtn, 0, QtCore.Qt.AlignRight)
        self.verticalLayout_12.addWidget(self.frame_8)
        self.leftMenuPages = QCustomStackedWidget(self.rightMenuSubContainer)
        self.leftMenuPages.setObjectName("leftMenuPages")
        self.hvPage = QtWidgets.QWidget()
        self.hvPage.setObjectName("hvPage")
        self.verticalLayout_14 = QtWidgets.QVBoxLayout(self.hvPage)
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_14.setObjectName("verticalLayout_14")
        self.widget_4 = QtWidgets.QWidget(self.hvPage)
        self.widget_4.setObjectName("widget_4")
        self.verticalLayout_34 = QtWidgets.QVBoxLayout(self.widget_4)
        self.verticalLayout_34.setObjectName("verticalLayout_34")
        self.frame_23 = QtWidgets.QFrame(self.widget_4)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_23.sizePolicy().hasHeightForWidth())
        self.frame_23.setSizePolicy(sizePolicy)
        self.frame_23.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_23.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_23.setObjectName("frame_23")
        self.verticalLayout_35 = QtWidgets.QVBoxLayout(self.frame_23)
        self.verticalLayout_35.setObjectName("verticalLayout_35")
        self.label_7 = QtWidgets.QLabel(self.frame_23)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_35.addWidget(
            self.label_7, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.verticalLayout_34.addWidget(self.frame_23, 0, QtCore.Qt.AlignTop)
        self.frame_24 = QtWidgets.QFrame(self.widget_4)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_24.sizePolicy().hasHeightForWidth())
        self.frame_24.setSizePolicy(sizePolicy)
        self.frame_24.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_24.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_24.setObjectName("frame_24")
        self.verticalLayout_34.addWidget(self.frame_24)
        self.verticalLayout_14.addWidget(self.widget_4)
        self.leftMenuPages.addWidget(self.hvPage)
        self.extruderPage = QtWidgets.QWidget()
        self.extruderPage.setObjectName("extruderPage")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout(self.extruderPage)
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.widget_2 = QtWidgets.QWidget(self.extruderPage)
        self.widget_2.setObjectName("widget_2")
        self.verticalLayout_27 = QtWidgets.QVBoxLayout(self.widget_2)
        self.verticalLayout_27.setObjectName("verticalLayout_27")
        self.frame_15 = QtWidgets.QFrame(self.widget_2)
        self.frame_15.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_15.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_15.setObjectName("frame_15")
        self.verticalLayout_23 = QtWidgets.QVBoxLayout(self.frame_15)
        self.verticalLayout_23.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_23.setSpacing(0)
        self.verticalLayout_23.setObjectName("verticalLayout_23")
        self.label_8 = QtWidgets.QLabel(self.frame_15)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_8.setFont(font)
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_23.addWidget(self.label_8, 0, QtCore.Qt.AlignTop)
        self.frame_16 = QtWidgets.QFrame(self.frame_15)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(
            self.frame_16.sizePolicy().hasHeightForWidth())
        self.frame_16.setSizePolicy(sizePolicy)
        self.frame_16.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_16.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_16.setObjectName("frame_16")
        self.verticalLayout_24 = QtWidgets.QVBoxLayout(self.frame_16)
        self.verticalLayout_24.setContentsMargins(0, 30, 0, 10)
        self.verticalLayout_24.setSpacing(0)
        self.verticalLayout_24.setObjectName("verticalLayout_24")
        self.label_16 = QtWidgets.QLabel(self.frame_16)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy)
        self.label_16.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_16.setFont(font)
        self.label_16.setObjectName("label_16")
        self.verticalLayout_24.addWidget(
            self.label_16, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        # Selección del puerto COM
        self.comboBox = QtWidgets.QComboBox(self.frame_16)
        self.comboBox.addItem("COM1")
        self.comboBox.addItem("COM2")
        self.comboBox.addItem("COM3")
        self.comboBox.addItem("COM4")
        self.comboBox.addItem("COM5")
        self.comboBox.addItem("COM6")
        self.comboBox.addItem("COM7")
        self.comboBox.addItem("COM8")
        self.comboBox.addItem("COM9")

        self.comboBox.setCurrentIndex(1)  # COM por defecto

        self.comboBox.currentIndexChanged.connect(self.COMvariable)

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(
            self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setInsertPolicy(QtWidgets.QComboBox.InsertAtBottom)
        self.comboBox.setObjectName("comboBox")
        self.verticalLayout_24.addWidget(
            self.comboBox, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.verticalLayout_23.addWidget(self.frame_16, 0, QtCore.Qt.AlignTop)
        self.frame_17 = QtWidgets.QFrame(self.frame_15)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(
            self.frame_17.sizePolicy().hasHeightForWidth())
        self.frame_17.setSizePolicy(sizePolicy)
        self.frame_17.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_17.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_17.setObjectName("frame_17")
        self.verticalLayout_25 = QtWidgets.QVBoxLayout(self.frame_17)
        self.verticalLayout_25.setContentsMargins(0, 20, 0, 20)
        self.verticalLayout_25.setSpacing(0)
        self.verticalLayout_25.setObjectName("verticalLayout_25")

        self.label_17 = QtWidgets.QLabel(self.frame_17)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_17.sizePolicy().hasHeightForWidth())
        self.label_17.setSizePolicy(sizePolicy)
        self.label_17.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_17.setFont(font)
        self.label_17.setObjectName("label_17")
        self.verticalLayout_25.addWidget(
            self.label_17, 0, QtCore.Qt.AlignHCenter)

        self.comboBox_2 = QtWidgets.QComboBox(self.frame_17)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(
            self.comboBox_2.sizePolicy().hasHeightForWidth())
        self.comboBox_2.setSizePolicy(sizePolicy)
        self.comboBox_2.setObjectName("comboBox_2")
        self.verticalLayout_25.addWidget(
            self.comboBox_2, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.comboBox_2.addItem("9600")
        self.comboBox_2.addItem("19200")
        self.comboBox_2.addItem("38400")
        self.comboBox_2.addItem("57600")
        self.comboBox_2.addItem("115200")

        self.comboBox_2.setCurrentIndex(4)  # COM por defecto

        self.comboBox_2.currentIndexChanged.connect(self.BRvariable)

        self.verticalLayout_23.addWidget(self.frame_17, 0, QtCore.Qt.AlignTop)
        self.verticalLayout_27.addWidget(self.frame_15)
        self.frame_18 = QtWidgets.QFrame(self.widget_2)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_18.sizePolicy().hasHeightForWidth())
        self.frame_18.setSizePolicy(sizePolicy)
        self.frame_18.setMinimumSize(QtCore.QSize(0, 120))
        self.frame_18.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_18.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_18.setObjectName("frame_18")
        self.verticalLayout_26 = QtWidgets.QVBoxLayout(self.frame_18)
        self.verticalLayout_26.setContentsMargins(0, 20, 0, 0)
        self.verticalLayout_26.setSpacing(0)
        self.verticalLayout_26.setObjectName("verticalLayout_26")

        self.conectSerialBtn = QtWidgets.QPushButton(self.frame_18)
        self.conectSerialBtn.setMinimumSize(QtCore.QSize(80, 20))
        self.conectSerialBtn.setMaximumSize(QtCore.QSize(80, 20))
        self.conectSerialBtn.setSizeIncrement(QtCore.QSize(0, 0))
        self.conectSerialBtn.setObjectName("conectSerialBtn")
        self.verticalLayout_26.addWidget(
            self.conectSerialBtn, 0, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        # Llama a la función con el código que lanza el botón
        self.conectSerialBtn.clicked.connect(self.conectExtruder)

        self.outputArdText = QtWidgets.QTextEdit(self.frame_18)
        self.outputArdText.setMinimumSize(QtCore.QSize(0, 60))
        self.outputArdText.setMaximumSize(QtCore.QSize(300, 120))
        self.outputArdText.setObjectName("outputArdText")
        self.verticalLayout_26.addWidget(self.outputArdText)
        self.outputArdText.setReadOnly(True)

        self.verticalLayout_27.addWidget(self.frame_18)
        self.verticalLayout_15.addWidget(
            self.widget_2, 0, QtCore.Qt.AlignHCenter)
        self.leftMenuPages.addWidget(self.extruderPage)
        self.stagePage = QtWidgets.QWidget()
        self.stagePage.setObjectName("stagePage")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.stagePage)
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.widget_3 = QtWidgets.QWidget(self.stagePage)
        self.widget_3.setObjectName("widget_3")
        self.verticalLayout_33 = QtWidgets.QVBoxLayout(self.widget_3)
        self.verticalLayout_33.setObjectName("verticalLayout_33")
        self.frame_13 = QtWidgets.QFrame(self.widget_3)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_13.sizePolicy().hasHeightForWidth())
        self.frame_13.setSizePolicy(sizePolicy)
        self.frame_13.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_13.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_13.setObjectName("frame_13")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout(self.frame_13)
        self.verticalLayout_21.setContentsMargins(0, 9, 0, 0)
        self.verticalLayout_21.setSpacing(0)
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.frame_10 = QtWidgets.QFrame(self.frame_13)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_10.sizePolicy().hasHeightForWidth())
        self.frame_10.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.frame_10.setFont(font)
        self.frame_10.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_10.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_10.setObjectName("frame_10")
        self.verticalLayout_20 = QtWidgets.QVBoxLayout(self.frame_10)
        self.verticalLayout_20.setContentsMargins(0, 0, 0, 7)
        self.verticalLayout_20.setSpacing(0)
        self.verticalLayout_20.setObjectName("verticalLayout_20")
        self.label_9 = QtWidgets.QLabel(self.frame_10)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setAlignment(QtCore.Qt.AlignCenter)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_20.addWidget(self.label_9)
        self.verticalLayout_21.addWidget(self.frame_10)
        self.frame_11 = QtWidgets.QFrame(self.frame_13)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_11.sizePolicy().hasHeightForWidth())
        self.frame_11.setSizePolicy(sizePolicy)
        self.frame_11.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_11.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_11.setObjectName("frame_11")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.frame_11)
        self.horizontalLayout_13.setContentsMargins(5, 10, 5, 30)
        self.horizontalLayout_13.setSpacing(0)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_14 = QtWidgets.QLabel(self.frame_11)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setItalic(True)
        self.label_14.setFont(font)
        self.label_14.setTextFormat(QtCore.Qt.AutoText)
        self.label_14.setScaledContents(False)
        self.label_14.setAlignment(
            QtCore.Qt.AlignJustify | QtCore.Qt.AlignVCenter)
        self.label_14.setWordWrap(True)
        self.label_14.setIndent(0)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_13.addWidget(
            self.label_14, 0, QtCore.Qt.AlignVCenter)
        self.verticalLayout_21.addWidget(self.frame_11)
        self.frame_12 = QtWidgets.QFrame(self.frame_13)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_12.sizePolicy().hasHeightForWidth())
        self.frame_12.setSizePolicy(sizePolicy)
        self.frame_12.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_12.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_12.setObjectName("frame_12")
        self.verticalLayout_22 = QtWidgets.QVBoxLayout(self.frame_12)
        self.verticalLayout_22.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_22.setSpacing(3)
        self.verticalLayout_22.setObjectName("verticalLayout_22")
        self.label_15 = QtWidgets.QLabel(self.frame_12)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_15.sizePolicy().hasHeightForWidth())
        self.label_15.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(7)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        font.setStrikeOut(False)
        self.label_15.setFont(font)
        self.label_15.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.label_15.setObjectName("label_15")
        self.verticalLayout_22.addWidget(
            self.label_15, 0, QtCore.Qt.AlignHCenter)
        self.conectingStageBtn = QtWidgets.QPushButton(self.frame_12)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.conectingStageBtn.sizePolicy().hasHeightForWidth())
        self.conectingStageBtn.setSizePolicy(sizePolicy)
        self.conectingStageBtn.setMinimumSize(QtCore.QSize(40, 40))
        self.conectingStageBtn.setMaximumSize(QtCore.QSize(40, 40))
        self.conectingStageBtn.setText("")
        icon19 = QtGui.QIcon()
        icon19.addPixmap(QtGui.QPixmap(":/icons/icons/rss.svg"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.conectingStageBtn.setIcon(icon19)
        self.conectingStageBtn.setIconSize(QtCore.QSize(20, 20))
        self.conectingStageBtn.setObjectName("conectingStageBtn")
        self.verticalLayout_22.addWidget(
            self.conectingStageBtn, 0, QtCore.Qt.AlignHCenter)
        # Llama a la función con el código que lanza el botón
        self.conectingStageBtn.clicked.connect(self.stageConect)

        self.frame_14 = QtWidgets.QFrame(self.frame_12)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frame_14.sizePolicy().hasHeightForWidth())
        self.frame_14.setSizePolicy(sizePolicy)
        self.frame_14.setMinimumSize(QtCore.QSize(120, 0))
        self.frame_14.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_14.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_14.setObjectName("frame_14")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.frame_14)
        self.horizontalLayout_12.setContentsMargins(0, 40, 0, 10)
        self.horizontalLayout_12.setSpacing(0)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.outputConText = QtWidgets.QTextEdit(self.frame_14)
        self.outputConText.setReadOnly(True)
        self.outputConText.setMinimumSize(QtCore.QSize(0, 60))
        self.outputConText.setMaximumSize(QtCore.QSize(300, 120))
        self.outputConText.setObjectName("outputConText")
        self.horizontalLayout_12.addWidget(self.outputConText)
        self.verticalLayout_22.addWidget(
            self.frame_14, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout_21.addWidget(
            self.frame_12, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout_33.addWidget(self.frame_13)
        self.verticalLayout_13.addWidget(self.widget_3)
        self.leftMenuPages.addWidget(self.stagePage)
        self.verticalLayout_12.addWidget(self.leftMenuPages)
        self.verticalLayout_11.addWidget(self.rightMenuSubContainer)
        self.horizontalLayout_8.addWidget(
            self.rightMenuContainer, 0, QtCore.Qt.AlignRight)
        self.verticalLayout_10.addWidget(self.mainBodyContent)
        self.footerContainer = QtWidgets.QWidget(self.mainBodyContainer)
        self.footerContainer.setObjectName("footerContainer")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.footerContainer)
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.frame_9 = QtWidgets.QFrame(self.footerContainer)
        font = QtGui.QFont()
        font.setPointSize(5)
        font.setKerning(True)
        self.frame_9.setFont(font)
        self.frame_9.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_9.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_9.setObjectName("frame_9")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.frame_9)
        self.horizontalLayout_11.setContentsMargins(2, 3, 9, 3)
        self.horizontalLayout_11.setSpacing(2)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_3 = QtWidgets.QLabel(self.frame_9)
        font = QtGui.QFont()
        font.setPointSize(7)
        font.setItalic(False)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_11.addWidget(
            self.label_3, 0, QtCore.Qt.AlignHCenter)
        self.horizontalLayout_10.addWidget(self.frame_9)
        self.sizeGrip = QtWidgets.QFrame(self.footerContainer)
        self.sizeGrip.setMinimumSize(QtCore.QSize(15, 15))
        self.sizeGrip.setMaximumSize(QtCore.QSize(15, 15))
        self.sizeGrip.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.sizeGrip.setFrameShadow(QtWidgets.QFrame.Raised)
        self.sizeGrip.setObjectName("sizeGrip")
        self.verticalLayout_19 = QtWidgets.QVBoxLayout(self.sizeGrip)
        self.verticalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName("verticalLayout_19")
        self.label_13 = QtWidgets.QLabel(self.sizeGrip)
        self.label_13.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
        self.label_13.setText("")
        self.label_13.setObjectName("label_13")
        self.verticalLayout_19.addWidget(self.label_13)
        self.horizontalLayout_10.addWidget(self.sizeGrip)
        self.verticalLayout_10.addWidget(self.footerContainer)
        self.horizontalLayout.addWidget(self.mainBodyContainer)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.centerMenuPages.setCurrentIndex(0)
        self.mainPages.setCurrentIndex(0)
        self.leftMenuPages.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.frame.setToolTip(_translate("MainWindow", "Menu"))
        self.menuBtn.setToolTip(_translate("MainWindow", "Menu"))
        self.homeBtn.setToolTip(_translate("MainWindow", "Home"))
        self.homeBtn.setText(_translate("MainWindow", " Home"))
        self.manualBtn.setToolTip(_translate("MainWindow", "Manual Mode"))
        self.manualBtn.setText(_translate("MainWindow", " Manual Mode"))
        self.gcodeBtn.setToolTip(_translate("MainWindow", "Print from G-Code"))
        self.gcodeBtn.setText(_translate("MainWindow", " G-Code"))
        self.calibrationBtn.setToolTip(_translate(
            "MainWindow", "Stage Zero Calibration"))
        self.calibrationBtn.setText(_translate("MainWindow", " Calibration"))
        self.helpBtn.setToolTip(_translate("MainWindow", "Get more help"))
        self.helpBtn.setText(_translate("MainWindow", " Help"))
        self.label.setText(_translate("MainWindow", "  Settings"))
        self.closeCenterMenuBtn.setToolTip(
            _translate("MainWindow", "Close Menu"))
        self.label_2.setText(_translate("MainWindow", "Calibration"))
        self.label_19.setText(_translate(
            "MainWindow", "Reference Movement Stage X:"))
        self.zeroxBtn.setText(_translate("MainWindow", "Zero Calibration X"))
        # Llama a la función con el código que lanza el botón
        self.zeroxBtn.clicked.connect(self.calibrateXStage)

        self.label_18.setText(_translate(
            "MainWindow", "Reference Movement Stage Y:"))
        self.zeroyBtn.setText(_translate("MainWindow", "Zero Calibration Y"))
        # Llama a la función con el código que lanza el botón
        self.zeroyBtn.clicked.connect(self.calibrateYStage)

        self.label_4.setText(_translate("MainWindow", "Help"))
        self.label_12.setText(_translate("MainWindow", "anuargimenez@usal.es"))
        self.stageConectBtn.setToolTip(
            _translate("MainWindow", "Stage XY Conection"))
        self.extruderConectBtn.setToolTip(
            _translate("MainWindow", "Extruder Conection"))
        self.HVConectBtn.setToolTip(_translate(
            "MainWindow", "High Voltage Source Conection"))
        self.minimizeBtn.setToolTip(
            _translate("MainWindow", "Minimize Window"))
        self.restoreBtn.setToolTip(_translate("MainWindow", "Restore Window"))
        self.closeBtn.setToolTip(_translate("MainWindow", "Close Window"))
        self.label_40.setText(_translate("MainWindow", "MEW 3D PRINTER"))
        self.label_39.setText(_translate(
            "MainWindow", "HOME - PRINTING STATUS"))
        self.label_42.setText(_translate("MainWindow", "Default Prints"))
        self.label_29.setText(_translate("MainWindow", "Stage Velocity Test"))
        self.label_32.setText(_translate("MainWindow", "Voltage Test"))
        self.label_34.setText(_translate(
            "MainWindow", "2D Reticular Scaffold"))
        self.label_41.setText(_translate(
            "MainWindow", "3D Reticular Scaffold"))
        self.label_10.setText(_translate("MainWindow", "MEW 3D PRINTER"))
        self.label_11.setText(_translate("MainWindow", "MANUAL CONTROL"))
        self.label_20.setText(_translate("MainWindow", "Relative Motion"))
        self.label_28.setText(_translate(
            "MainWindow", "Printhead Temperatures (ºC)"))
        self.label_25.setText(_translate("MainWindow", "Upper Heater"))
        self.label_27.setText(_translate("MainWindow", "Lower Heater"))
        self.label_26.setText(_translate("MainWindow", "Bed Heater"))
        self.label_24.setText(_translate("MainWindow", "Extrusion Parameters"))
        self.label_30.setText(_translate(
            "MainWindow", "Extrusion Velocity (mm/s):  "))
        self.label_31.setText(_translate(
            "MainWindow", "Extruded Distance (mm):   "))
        self.label_21.setText(_translate("MainWindow", "Absolute Motion"))
        self.label_22.setText(_translate("MainWindow", "X (mm):   "))
        self.label_23.setText(_translate("MainWindow", "Y (mm):    "))
        self.label_33.setText(_translate(
            "MainWindow", "Enter G-Code Manually:"))
        self.label_36.setText(_translate("MainWindow", "MEW 3D PRINTER"))
        self.label_37.setText(_translate("MainWindow", "UPLOAD G-CODE FILE"))
        self.label_38.setText(_translate(
            "MainWindow", "Drag and Drop your file:"))
        self.label_6.setText(_translate("MainWindow", "   Conection"))
        self.closeRightMenuBtn.setToolTip(
            _translate("MainWindow", "Close Menu"))
        self.label_7.setText(_translate(
            "MainWindow", "High Voltage Supply Conection"))
        self.label_8.setText(_translate("MainWindow", "Extruder Conection"))
        self.label_16.setText(_translate("MainWindow", "Select COM port:"))
        self.label_17.setText(_translate("MainWindow", "Select Baud Rate:"))
        self.conectSerialBtn.setText(_translate("MainWindow", "Conect Serial"))
        self.label_9.setText(_translate("MainWindow", "Stage XY Conection"))
        self.label_14.setText(_translate(
            "MainWindow", "The X and Y stage drivers are daisy-chained, with the Y controller acting as the master. Serial communication is established between the two controllers, as well as between the master controller and the computer."))
        self.label_15.setText(_translate(
            "MainWindow", "Conect and Initialize XY Stages:"))
        self.label_3.setText(_translate(
            "MainWindow", "ETSII Béjar | Ingeniería Eléctrica | Anuar R. Giménez El Amrani"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
