from OpenGL.GLUT import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *
from PyQt5.QtGui import *
import OpenGLControl as DrawRB
import numpy as np
import pymysql
from Robot import *
from Trajectory import *
from Ui_datebase_link import Ui_Form

# 主窗口类
class RobotSimulator(QMainWindow):
    def __init__(self, *args):
        super(RobotSimulator, self).__init__(*args)
        # 调用父类RobotSimulator的初始化方法
        loadUi('model_diaplay.ui', self) # 加载ui文件
        # self.sub_window = Ui_Form() # 创建子窗口
        self.timer = QTimer()   # 创建定时器对象
        self.count = 0  # 计数器
        self.timer.timeout.connect(self.timeEvent)  # 将定时器的timeout信号连接到timeEvent方法上
        self.objRB = Robot()    # 创建机器人对象
        self.RB = DrawRB.GLWidget(self, self.objRB) # 创建一个GLWidget对象RB，该对象用于绘制机器人
        # self.objRB.cf = ConfigRobot()
        self.fileName = None    # 初始化文件名
        self.AllPoints = np.array([[None, None, None]]) # 初始化所有点
        self.AllJVars = np.array([[None, None, None, None]])    # 初始化所有关节角度
        self.toolstatus = np.array([None])  # 初始化工具状态
    
    def setupUI(self):  # 设置UI
        self.setCentralWidget(self.RB)  # 设置中心窗口
        self.horizontalSlider.sliderMoved.connect(lambda: self.valueChangeJVars(0, self.horizontalSlider.value()))
        self.horizontalSlider_2.sliderMoved.connect(lambda: self.valueChangeJVars(1, self.horizontalSlider_2.value()))
        self.horizontalSlider_3.sliderMoved.connect(lambda: self.valueChangeJVars(2, self.horizontalSlider_3.value()))
        self.checkBox.stateChanged.connect(self.ViewGrid)  # 将checkbox的stateChanged信号连接到ViewGrid方法上
        self.pushButton.clicked.connect(self.OpenDB)   # 将pushButton的clicked信号连接到OpenDB方法上

    def ViewGrid(self): # 显示网格
        self.isChecked = self.checkBox.isChecked()
        if Qt.Checked:
            self.RB.isDrawGrid = not self.RB.isDrawGrid # 设置是否显示网格
            self.RB.updateGL()  # 更新GLWidget

    # 根据传入的关节索引和关节角度值更新机器人的姿态，然后重新计算机器人的位置并更新显示
    def valueChangeJVars(self, index, value):   # 更新关节角度
        self.objRB.JVars[index] = DegToRad(value)   # 将参数转化成弧度赋值并更新指定索引处的关节角度
        self.objRB.CalFwdPostion(self.objRB.JVars)  # 计算正运动学 即根据更新后的关节角度计算机器人的位置
        self.RB.updateGL()  # 更新GLWidget即重新绘制机器人的图形

    # 根据关节角度数据的数量和运动状态，
    # 通过循环调用timeEvent方法控制机器人的连续运动，
    # 并在运动结束后更新文本标签的显示内容
    def timeEvent(self):
        try:
            self.objRB.JVars = self.AllJVars[self.count]    # 将索引为self.count的关节角度数据赋值给self.objRB.JVars
            self.RB.listPoints = np.append(self.RB.listPoints, [self.AllPoints[self.count]], axis=0)    # 机器人关节角度
            if self.toolstatus[self.count] == 1:
                self.RB.color = np.append(self.RB.color, 1) #
            else:
                self.RB.color = np.append(self.RB.color, 0)

            self.count += 1
            self.RB.updateGL()
        finally:
            if (self.count < len(self.AllJVars) - 1) and self.isRun:
                QTimer.singleShot(0, self.timeEvent)
            else:
                self.valueStatus.setText("Done")
    
    # 打开数据库界面
    def OpenDB(self):
        self.sub_window = DBWindow()    # 创建子窗口
        self.sub_window.show()  # 显示子窗口


# 子窗口类
class DBWindow(QWidget, Ui_Form):
    def __init__(self, *args): # 初始化
        super(DBWindow, self).__init__(*args)   # 调用父类DBWindow的初始化方法
        self.setupUi(self)  # 设置UI
        self.isconnect = False  # 初始化数据库连接状态
        self.autoupdate = False # 初始化自动刷新状态

        # 设置默认提示文本
        self.lineEdit.setPlaceholderText("database host")   # 设置数据库地址
        self.lineEdit_2.setEchoMode(QLineEdit.Password) # 设置密码输入框
        self.lineEdit_2.setPlaceholderText("database password") # 设置密码
        self.lineEdit_3.setPlaceholderText("database name") # 设置数据库名
        self.lineEdit_4.setPlaceholderText("table name")    # 设置数据表名

        # 按键事件绑定
        self.pushButton.clicked.connect(self.connectDB)    # 将pushButton的clicked信号连接到connectDB方法上
        self.pushButton_2.clicked.connect(self.disconnectDB)    # 将pushButton_2的clicked信号连接到disconnectDB方法上
        self.pushButton_3.clicked.connect(self.readDB)  # 将pushButton_3的clicked信号连接到readDB方法上
        self.pushButton_4.clicked.connect(self.clearDB) # 将pushButton_4的clicked信号连接到clearDB方法上
        self.radioButton.toggled.connect(self.refreshDB)    # 将radioButton的toggled信号连接到refreshDB方法上
        self.radioButton_2.toggled.connect(self.refreshDB)  # 将radioButton_2的toggled信号连接到refreshDB方法上

        # 创建 QTimer 定时器，每隔一定时间执行 update_data 函数
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)  # 设置时间间隔为10秒（单位：毫秒）

    def connectDB(self):    # 连接数据库
        if self.isconnect:
            self.plainTextEdit.appendPlainText("Database has connected!")
            return
        else:
            self.isconnect = True
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.table = self.lineEdit_4.text()  # 获取数据表名
            self.password = self.lineEdit_2.text()  # 获取密码
            self.database = self.lineEdit_3.text()  # 获取数据库名
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
            # 查询数据库版本
            self.cursor.execute("select version()") # 返回值是查询到的数据数量
            # 通过 fetchall方法获得数据
            self.data = self.cursor.fetchone()
            self.plainTextEdit.appendPlainText("Database Version:%s" % self.data) # 打印数据库版本
            # print("Database Version:%s" % self.data) # 打印数据库版本
            
    def disconnectDB(self): # 断开数据库连接
        if self.isconnect:
            self.isconnect = False
            self.conn.close()
            self.cursor.close()
            self.plainTextEdit.appendPlainText("Database has disconnected!")
        else:
            self.plainTextEdit.appendPlainText("Database has disconnected!")
            return

    def readDB(self):   # 读取数据库
        if self.isconnect:
            self.table = self.lineEdit_4.text()  # 获取数据表名
            # 数据库查询数据
            self.sql = "SELECT * FROM " + self.table + "" # 查询数据表中的所有数据
            self.cursor.execute(self.sql) # 返回值是查询到的数据数量
            self.data = self.cursor.fetchall() # 查询全部数据
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
            # print(self.data)    # 打印查询到的数据
            self.plainTextEdit.appendPlainText(str(self.data)) # 显示查询到的数据
        else:
            self.plainTextEdit.appendPlainText("Database has disconnected!")
            return
    
    #  定时器调用的函数，用于更新数据
    def update_data(self):
        if self.isconnect & self.autoupdate:
            self.table = self.lineEdit_4.text()  # 获取数据表名
            # 数据库查询数据
            self.sql = "SELECT * FROM " + self.table + "" # 查询数据表中的所有数据
            self.cursor.execute(self.sql) # 返回值是查询到的数据数量
            self.data = self.cursor.fetchall() # 查询全部数据
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
    
    # 清除tablevview中的数据
    def clearDB(self):
        self.reply = QMessageBox.question(self, "确认清除", "确定要清除所有内容吗？", QMessageBox.Yes | QMessageBox.No)
        if self.reply == QMessageBox.Yes:
            # 清除模型数据
            self.model.clear()
            # 刷新视图
            self.tableView.reset()
            self.plainTextEdit.appendPlainText("Database has cleared!")
    
    # 刷新tableview中的数据
    def refreshDB(self):
        if self.radioButton.isChecked():
            self.readDB()
            self.plainTextEdit.appendPlainText("Database has refreshed!")
        elif self.radioButton_2.isChecked():
            self.autoupdate = True # 设置自动刷新状态
            self.plainTextEdit.appendPlainText("Enable Auto Refresh!")

# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)    # 创建一个QApplication对象
    window = RobotSimulator()   # 创建一个RobotSimulator对象
    window.setupUI()    # 设置UI
    window.show()   # 显示窗口
    sys.exit(app.exec_())   # 进入主循环
