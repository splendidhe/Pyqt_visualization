from OpenGL.GLUT import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *
from PyQt5.QtGui import *
import OpenGLControl as DrawRB
import numpy as np
import pymysql
import pyqtgraph as pg
from Robot import *
from Trajectory import *
from Ui_management import Ui_MainWindow

# 主窗口类
class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args): # 初始化
        super(MyWindow, self).__init__(*args)
        self.setupUi(self)  # 设置UI
        self.isconnect = False  # 初始化数据库连接状态
        self.autoupdate = False # 初始化自动刷新状态
        self.graphics_scene = QGraphicsScene()
        self.timer = QTimer()   # 创建定时器对象
        self.count = 0  # 计数器
        self.timer.timeout.connect(self.timeEvent)  # 将定时器的timeout信号连接到timeEvent方法上
        self.objRB = Robot()    # 创建机器人对象
        self.RB = DrawRB.GLWidget(self, self.objRB) # 创建一个GLWidget对象RB，该对象用于绘制机器人
        self.fileName = None    # 初始化文件名
        self.AllPoints = np.array([[None, None, None]]) # 初始化所有点
        self.AllJVars = np.array([[None, None, None, None]])    # 初始化所有关节角度
        self.toolstatus = np.array([None])  # 初始化工具状态
        self.layout = QVBoxLayout(self.openGLWidget)
        self.layout.addWidget(self.RB)

        # 按键事件绑定
        self.pushButton.clicked.connect(self.ConnectDB)
        self.pushButton_2.clicked.connect(self.PageSwitch)
        self.pushButton_3.clicked.connect(self.PageSwitch) 
        self.pushButton_4.clicked.connect(self.PageSwitch) 
        self.pushButton_7.clicked.connect(self.PageSwitch)
        self.pushButton_5.clicked.connect(self.ReadDB)
        self.pushButton_12.clicked.connect(self.Manual_refreshDB)
        self.radioButton.toggled.connect(self.RefreshDB)
        self.radioButton_2.toggled.connect(self.RefreshDB)
        self.checkBox.stateChanged.connect(self.ViewGrid)
        self.buttonGroup_3.setExclusive(False)
        self.radioButton_3.toggled.connect(self.Pos_curve)
        self.radioButton_4.toggled.connect(self.Pos_curve)
        self.radioButton_5.toggled.connect(self.Pos_curve)

        # 创建 QTimer 定时器，每隔一定时间执行 update_data 函数
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Update_data)
        self.timer.start(5000)  # 设置时间间隔为5秒（单位：毫秒）
        self.timer = QTimer(self)   # 创建定时器对象
        self.timer.timeout.connect(self.Gesture)
        self.timer.start(5000)  # 设置时间间隔为5秒（单位：毫秒）

    # XYZ坐标曲线
    def Pos_curve(self):
        if (self.isconnect == False) & self.autoupdate:
            self.isconnect = True  # 设置数据库连接状态
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.database = self.lineEdit_2.text()  # 获取数据库名
            self.password = self.lineEdit_3.text()  # 获取密码
            # 创建数据库连接
            self.conn = pymysql.connect(
                host = self.host,         # 连接主机, 默认127.0.0.1 
                user = 'root',            # 用户名
                passwd = self.password,   # 密码
                port = 3306,              # 端口，默认为3306
                db = self.database,       # 数据库名称
                charset = 'utf8'          # 字符编码
            )
            self.cursor = self.conn.cursor() # 生成游标对象 cursor
            # 执行查询语句
            self.query = "SELECT pitch FROM ship_state LIMIT 100"
            self.cursor.execute(self.query)
            self.graph_data = self.cursor.fetchall()
            # 将数据转换为列表
            pitch_list = [row[0] for row in self.graph_data]
            # 执行查询语句
            self.cursor = self.conn.cursor()
            self.query = "SELECT roll FROM ship_state LIMIT 100"
            self.cursor.execute(self.query)
            self.graph_data = self.cursor.fetchall()
            roll_list = [row[0] for row in self.graph_data]
            # 执行查询语句
            self.cursor = self.conn.cursor()
            self.query = "SELECT yaw FROM ship_state LIMIT 100"
            self.cursor.execute(self.query)
            self.graph_data = self.cursor.fetchall()
            yaw_list = [row[0] for row in self.graph_data]
            # 清空视图内容
            self.graphics_scene.clear()
            # 绘制曲线图
            self.plot_widget = pg.PlotWidget()
            # 创建三条曲线并添加到PlotWidget中
            self.curve_pitch = self.plot_widget.plot(pitch_list, stepMode='left', antialias=False)
            self.pen = pg.mkPen(color='#f38b00', width=2)
            self.curve_pitch.setPen(self.pen)
            self.curve_roll = self.plot_widget.plot(roll_list, stepMode='left', antialias=False)
            self.pen = pg.mkPen(color='#32874f', width=2)
            self.curve_roll.setPen(self.pen)
            self.curve_yaw = self.plot_widget.plot(yaw_list, stepMode='left', antialias=False)
            self.pen = pg.mkPen(color='#9a86fd', width=2)
            self.curve_yaw.setPen(self.pen)
            
            
            if self.radioButton_3.isChecked():
                self.curve_pitch.setVisible(True)
            else :
                self.curve_pitch.setVisible(False)

            if self.radioButton_4.isChecked():
                self.curve_roll.setVisible(True)
            else :
                self.curve_roll.setVisible(False)

            if self.radioButton_5.isChecked():
                self.curve_yaw.setVisible(True)
            else :
                self.curve_yaw.setVisible(False)

            self.plot_widget.setBackground('#ffffff') # 设置背景颜色
            self.graphics_scene.addWidget(self.plot_widget)
            self.graphicsView.setScene(self.graphics_scene)
            # 关闭数据库连接释放资源
            self.isconnect = False
            self.cursor.close() 
            self.conn.close()

    #  定时器调用的函数，用于更新数据
    def Update_data(self):
        if (self.isconnect == False) & self.autoupdate:
            self.isconnect = True  # 设置数据库连接状态
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.database = self.lineEdit_2.text()  # 获取数据库名
            self.password = self.lineEdit_3.text()  # 获取密码
            # 创建数据库连接
            self.conn = pymysql.connect(
                host = self.host,         # 连接主机, 默认127.0.0.1 
                user = 'root',            # 用户名
                passwd = self.password,   # 密码
                port = 3306,              # 端口，默认为3306
                db = self.database,       # 数据库名称
                charset = 'utf8'          # 字符编码
            )
            self.cursor = self.conn.cursor() # 生成游标对象 cursor
            self.selected_option = self.comboBox.currentText()
            # 数据库查询数据
            self.sql = "SELECT * FROM " + self.selected_option + "" # 查询数据表中的所有数据
            self.cursor.execute(self.sql) # 返回值是查询到的数据数量
            self.data = self.cursor.fetchall() # 查询全部数据
            self.cursor.close() # 关闭游标
            self.conn.close()   # 关闭数据库连接
            self.isconnect = False  # 设置数据库连接状态
            # 创建数据模型
            self.model = QStandardItemModel(self)
            self.model.setColumnCount(len(self.data[0]))
            self.model.setRowCount(len(self.data))
            # 填充数据模型
            for row_num, row_data in enumerate(self.data):
                for col_num, col_data in enumerate(row_data):
                    item = QStandardItem(str(col_data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.model.setItem(row_num, col_num, item)
            # 设置数据模型到 QTableView
            self.tableView.setModel(self.model)

    
    
    #  定时器调用的函数，用于更新3D模型姿态
    def Gesture(self):
        if (self.isconnect == False) & self.autoupdate:
            self.isconnect = True  # 设置数据库连接状态
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.database = self.lineEdit_2.text()  # 获取数据库名
            self.password = self.lineEdit_3.text()  # 获取密码
            # 创建数据库连接
            self.conn = pymysql.connect(
                host = self.host,         # 连接主机, 默认127.0.0.1 
                user = 'root',            # 用户名
                passwd = self.password,   # 密码
                port = 3306,              # 端口，默认为3306
                db = self.database,       # 数据库名称
                charset = 'utf8'          # 字符编码
            )
            self.cursor = self.conn.cursor() # 生成游标对象 cursor
            self.sql = "SELECT pitch, roll, yaw FROM ship_state ORDER BY createtime DESC LIMIT 1"
            self.cursor.execute(self.sql)
            self.cursor.close() # 关闭游标
            self.conn.close()   # 关闭数据库连接
            self.isconnect = False  # 设置数据库连接状态
            self.pitch, self.roll, self.yaw = self.cursor.fetchone()
            # print(pitch, roll, yaw)
            self.plainTextEdit.appendPlainText("X: " + str(self.roll) + " Y: " + str(self.pitch) + " Z: " + str(self.yaw))
            self.textEdit.setText(str(self.roll))
            self.textEdit_2.setText(str(self.pitch))
            self.textEdit_3.setText(str(self.yaw))
            self.valueChangeJVars(0, self.roll)
            self.valueChangeJVars(1, self.pitch)
            self.valueChangeJVars(2, self.yaw)

    def Manual_refreshDB(self): # 手动刷新tableview数据
        self.ReadDB()
        self.plainTextEdit.appendPlainText("Data Refresh!")
    
    def ReadDB(self):   # 读取数据库
        if not self.isconnect:
            self.isconnect = True
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.database = self.lineEdit_2.text()  # 获取数据库名
            self.password = self.lineEdit_3.text()  # 获取密码
            # 创建数据库连接
            self.conn = pymysql.connect(
                host=self.host,         # 连接主机, 默认127.0.0.1 
                user='root',            # 用户名
                passwd=self.password,   # 密码
                port=3306,              # 端口，默认为3306
                db=self.database,       # 数据库名称
                charset='utf8'          # 字符编码
            )
            # 生成游标对象 cursor
            self.cursor = self.conn.cursor()
            self.selected_option = self.comboBox.currentText()
            # 数据库查询数据
            self.sql = "SELECT * FROM " + self.selected_option + "" # 查询数据表中的所有数据
            self.cursor.execute(self.sql) # 返回值是查询到的数据数量
            self.data = self.cursor.fetchall() # 查询全部数据
            # 设置QTableView
            self.model = QStandardItemModel(self)
            self.model.setColumnCount(len(self.data[0]))
            self.model.setRowCount(len(self.data))
            for row_num, row_data in enumerate(self.data): # 填充数据模型
                for col_num, col_data in enumerate(row_data):
                    item = QStandardItem(str(col_data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.model.setItem(row_num, col_num, item)
            self.tableView.setModel(self.model) # 设置数据模型到 QTableView
            self.plainTextEdit.appendPlainText(str(self.data)) # 显示查询到的数据
            # 设置QTreeView
            self.cursor.execute("SHOW TABLES") # 查询数据库中的所有数据表
            self.tables = self.cursor.fetchall() # 查询全部数据
            self.treemodel = QStandardItemModel()   # 创建数据模型
            self.treeView.setModel(self.treemodel)  # 设置数据模型到 QTreeView
            self.root_item = self.treemodel.invisibleRootItem() # 创建根节点
            for table in self.tables:
                self.table_name = table[0]
                # 创建数据表节点
                self.table_item = QStandardItem(self.table_name)
                self.root_item.appendRow(self.table_item)
                # 查询数据表中的列名称
                self.cursor.execute(f"SHOW COLUMNS FROM {self.table_name}")
                self.columns = self.cursor.fetchall()
                # 创建列名称节点
                for column in self.columns:
                    column_name = column[0]
                    column_item = QStandardItem(column_name)
                    self.table_item.appendRow(column_item)
            # 释放资源
            self.cursor.close()
            self.conn.close()
            self.isconnect = False
        else:
            self.plainTextEdit.appendPlainText("Database Connect!")
            return

    def RefreshDB(self):    # 刷新数据库
        if self.radioButton.isChecked():
            self.autoupdate = False
            self.plainTextEdit.appendPlainText("Manual Refresh!")
        elif self.radioButton_2.isChecked():
            self.autoupdate = True # 设置自动刷新状态
            self.plainTextEdit.appendPlainText("Auto Refresh!")

    def ConnectDB(self):    # 连接数据库
        if self.isconnect:
            self.plainTextEdit.appendPlainText("Data Connect!")
            return
        else:
            self.isconnect = True
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.database = self.lineEdit_2.text()  # 获取数据库名
            self.password = self.lineEdit_3.text()  # 获取密码
            # 创建数据库连接
            self.conn = pymysql.connect(
                host=self.host,         # 连接主机, 默认127.0.0.1 
                user='root',            # 用户名
                passwd=self.password,   # 密码
                port=3306,              # 端口，默认为3306
                db=self.database,       # 数据库名称
                charset='utf8'          # 字符编码
            )
            # 生成游标对象 cursor
            self.cursor = self.conn.cursor()
            self.cursor.execute("select version()") # 查询数据库版本
            self.data = self.cursor.fetchone()
            self.plainTextEdit.appendPlainText("Database Version:%s" % self.data) # 打印数据库版本
            # print("Database Version:%s" % self.data) # 打印数据库版本
            self.sql = "SHOW TABLES"  # 获取数据库中的所有数据表
            self.cursor.execute(self.sql)
            self.tables = self.cursor.fetchall()
            # 将数据表添加到 ComboBox 中
            for table in self.tables:
                self.comboBox.addItem(table[0])
            self.cursor.close()
            self.conn.close()
            self.isconnect = False

    def PageSwitch(self):  # 页面切换
        sender = self.sender()
        if sender == self.pushButton_2:
            self.stackedWidget.setCurrentIndex(0)
        elif sender == self.pushButton_3:
            self.stackedWidget.setCurrentIndex(1)
        elif sender == self.pushButton_4:
            self.stackedWidget.setCurrentIndex(2)
        elif sender == self.pushButton_7:
            self.stackedWidget.setCurrentIndex(3)
    
    def ViewGrid(self): # 显示网格
        self.isChecked = self.checkBox.isChecked()
        if Qt.Checked:
            self.RB.isDrawGrid = not self.RB.isDrawGrid
            self.RB.updateGL()  # 更新GLWidget

    # 根据传入的关节索引和关节角度值更新机器人的姿态，然后重新计算机器人的位置并更新显示
    def valueChangeJVars(self, index, value):   # 更新关节角度
        self.objRB.JVars[index] = DegToRad(value)   # 将参数转化成弧度赋值并更新指定索引处的关节角度
        self.objRB.CalFwdPostion(self.objRB.JVars)  # 计算正运动学
        self.RB.updateGL()  # 重新绘制机器人的图形

    # 根据关节角度数据的数量和运动状态,通过循环调用timeEvent方法控制机器人的连续运动，
    # 并在运动结束后更新文本标签的显示内容
    def timeEvent(self):
        try:
            self.objRB.JVars = self.AllJVars[self.count]    # 将索引为self.count的关节角度数据赋值给self.objRB.JVars
            self.RB.listPoints = np.append(self.RB.listPoints, [self.AllPoints[self.count]], axis=0)    # 机器人关节角度
            if self.toolstatus[self.count] == 1:
                self.RB.color = np.append(self.RB.color, 1)
            else:
                self.RB.color = np.append(self.RB.color, 0)
            self.count += 1
            self.RB.updateGL()
        finally:
            if (self.count < len(self.AllJVars) - 1) and self.isRun:
                QTimer.singleShot(0, self.timeEvent)
            else:
                self.valueStatus.setText("Done")


# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)    # 创建一个QApplication对象
    window = MyWindow()   # 创建一个主窗口对象
    window.show()   # 显示窗口
    sys.exit(app.exec_())   # 进入主循环