import os
import sys
import json
from downloader import check_url, downloader
from threading import Thread
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

CONFIG = dict()
VIDEOS = dict()

class Ui_MainWindow(QMainWindow):

    def __init__(self):
        super(Ui_MainWindow,self).__init__()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName('MainWindow')
        MainWindow.setMaximumSize(1280, 720)
        MainWindow.setMinimumSize(1280, 720)
        MainWindow.setWindowFlags(Qt.FramelessWindowHint) # 无边框
        MainWindow.setStyleSheet("#MainWindow{border-image: url(img/bg1.png)}")
    
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName('centralWidget')

        self.list = QListWidget(self.centralWidget)
        self.list.setGeometry(40, 60, 280, 40)
        self.list.setObjectName('list')

        self.listItem = QListWidgetItem(self.list)
        self.listItem.setSizeHint(QSize(80, 20))
        self.listItem.setTextAlignment(Qt.AlignCenter)
        self.listItem_1 = QListWidgetItem(self.list)
        self.listItem_1.setSizeHint(QSize(120, 20))
        self.listItem_1.setTextAlignment(Qt.AlignCenter)
        self.listItem_2 = QListWidgetItem(self.list)
        self.listItem_2.setSizeHint(QSize(80, 20))
        self.listItem_2.setTextAlignment(Qt.AlignCenter)

        self.list.setFlow(QListView.LeftToRight)
        self.list.setStyleSheet('font-size:24px;font-family:微软雅黑;border-width:0px;border-style:solid;background-color:rgba(150,150,150,20%);')
        self.list.currentRowChanged.connect(self.switch)

        self.stack_1 = QWidget(self.centralWidget)
        self.stack_2 = QWidget(self.centralWidget)
        self.stack_3 = QWidget(self.centralWidget)

        self.lineEdit = QLineEdit(self.stack_1)
        self.lineEdit.setGeometry(QtCore.QRect(200, 200, 800, 40))
        self.lineEdit.setText('')
        self.lineEdit.setObjectName('lineEdit')
        self.lineEdit.returnPressed.connect(self.download)
        self.lineEdit.setStyleSheet('font-size:20px;font-family:微软雅黑;background-color:rgba(150,150,150,60%);' +
                    'border-width:1px;border-style:solid;border-color:#d1d1d1;border-radius:3px;color:#FFFFFF')
        
        self.pushButton = QPushButton(self.stack_1)
        self.pushButton.setGeometry(QtCore.QRect(500, 280, 200, 40))
        self.pushButton.setObjectName('pushButton')
        self.pushButton.setDefault(True)
        self.pushButton.clicked.connect(self.download)
        self.pushButton.setStyleSheet('font-size:20px;font-family:微软雅黑;background-color:rgba(150,150,150,50%);' +
                    'color:#FFFFFF;border-radius:5px')

        self.pushButton_1 = QPushButton(self.centralWidget)
        self.pushButton_1.setGeometry(QtCore.QRect(1220, 20, 40, 40))
        self.pushButton_1.setObjectName('pushButton_1')
        self.pushButton_1.setDefault(True)
        self.pushButton_1.clicked.connect(MainWindow.close)
        self.pushButton_1.setStyleSheet("#pushButton_1{font-size:20px;font-family:微软雅黑;" +
                    "color:#FFFFFF;border-radius:5px;border-image: url(img/close.png)}")

        self.pushButton_2 = QPushButton(self.centralWidget)
        self.pushButton_2.setGeometry(QtCore.QRect(1160, 20, 40, 40))
        self.pushButton_2.setObjectName('pushButton_2')
        self.pushButton_2.setDefault(True)
        self.pushButton_2.clicked.connect(MainWindow.showMinimized)
        self.pushButton_2.setStyleSheet("#pushButton_2{font-size:20px;font-family:微软雅黑;" +
                    "color:#FFFFFF;border-radius:5px;border-image: url(img/minimize.png)}")

        self.list_1 = QListWidget(self.stack_2)
        self.list_1.setGeometry(0, 20, 1200, 530)
        self.list_1.setObjectName('list_1')
        self.flush()
        self.list_1.itemDoubleClicked.connect(self.open_dir)
        self.list_1.setStyleSheet('font-size:20px;font-family:微软雅黑;background-color:rgba(80,80,80,20%);' +
                    'border-width:0px;border-style:solid;border-color:#d1d1d1;border-radius:3px;color:#FFFFFF')

        self.textEdit = QTextEdit(self.stack_1)
        self.textEdit.setGeometry(0, 340, 1200, 230)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName('textEdit')
        self.textEdit.setStyleSheet('font-size:20px;font-family:微软雅黑;background-color:rgba(80,80,80,20%);' +
                    'border-width:0px;border-style:solid;border-color:#d1d1d1;border-radius:3px;color:#FFFFFF')
        
        self.textEdit_1 = QTextEdit(self.stack_3)
        self.textEdit_1.setGeometry(0, 20, 1200, 530)
        self.textEdit_1.setReadOnly(True)
        self.textEdit_1.setObjectName('textEdit_1')
        self.textEdit_1.setStyleSheet('font-size:20px;font-family:微软雅黑;background-color:rgba(80,80,80,20%);' +
                    'border-width:0px;border-style:solid;border-color:#d1d1d1;border-radius:3px;color:#FFFFFF')
        self.stack = QStackedWidget(self.centralWidget)
        self.stack.setGeometry(QtCore.QRect(40, 120, 1200, 550))
        self.stack.addWidget(self.stack_1)
        self.stack.addWidget(self.stack_2)
        self.stack.addWidget(self.stack_3)

        # print重定向，显示在textedit中
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)

        MainWindow.setCentralWidget(self.centralWidget)
        MainWindow.setWindowOpacity(0.95)  # 设置窗口透明度
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate('MainWindow', 'bilibili downloader'))
        self.lineEdit.setPlaceholderText(_translate('MainWindow', 'https://www.bilibili.com/av10086'))
        self.pushButton.setText(_translate('MainWindow', '下    载'))
        self.listItem.setText(_translate('MainWindow', '首页'))
        self.listItem_1.setText(_translate('MainWindow', '下载管理'))
        self.listItem_2.setText(_translate('MainWindow', '关于'))
        self.textEdit.setPlaceholderText(_translate("MainWindow", "[Info] 初始化完成！"))
        self.textEdit_1.setPlaceholderText(_translate("MainWindow", "大三在读，信息安全\n" +
                "Github: https://github.com/entropy2333"))
    
    def normalOutputWritten(self, text):
        cursor = self.textEdit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.textEdit.setTextCursor(cursor)
        self.textEdit.ensureCursorVisible()

    def switch(self, i):
        self.stack.setCurrentIndex(i)

    def download(self):
        self.flush()
        url = self.lineEdit.text()
        self.lineEdit.setText('')
        # 检查url是否为空
        if not check_url(url):
            print('[Error] 请输入正确的视频链接！')
            return 
        else:
            try:
                with open("config.json", 'r', encoding='utf-8') as f:
                    CONFIG = json.load(f)
                CONFIG['url'] = url
                t = Thread(target=downloader, args=(CONFIG, ))
                t.setDaemon(True)
                t.start()
            except Exception as e:
                print(e)
    
    def flush(self, path=None):
        if not path:
            path = os.getcwd()
        dirs = os.listdir(path)
        for d in dirs:
            if d.split('-')[-1] == 'bilibili':
                tmp = os.listdir(d)
                for t in tmp:
                    if t.split('.')[-1] == 'mp4':
                        VIDEOS[t] = os.path.join(path, d, t)
        self.list_1.clear()
        for video in VIDEOS.keys():
            self.list_1.addItem(video)
    
    def open_dir(self, item):
        def play_mp4(path):
            os.system("E:\PotPlayer\PotPlayerMini64.exe {}".format(path))
        try:
            path = VIDEOS[item.text()]
            t = Thread(target=play_mp4, args=(path, ))
            t.start()
        except Exception as e:
            print(e)

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())