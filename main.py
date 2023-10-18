from OpenGL.GLUT import *
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
from Ui_datebase_link import Ui_Form

# 主窗口类
class DBWindow(QWidget, Ui_Form):
    def __init__(self, *args): # 初始化
        super(DBWindow, self).__init__(*args)   # 调用父类DBWindow的初始化方法
        self.setupUi(self)  # 设置UI
        self.isconnect = False  # 初始化数据库连接状态
        self.autoupdate = False # 初始化自动刷新状态
        self.graphics_scene = QGraphicsScene()
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
        self.layout = QVBoxLayout(self.openGLWidget)
        self.layout.addWidget(self.RB)

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
        self.pushButton_5.clicked.connect(self.manual_refreshDB) # 将pushButton_5的clicked信号连接到mutual_refreshDB方法上
        self.pushButton_6.clicked.connect(self.cleartext) # 将pushButton_6的clicked信号连接到data_visual方法上
        self.pushButton_7.clicked.connect(self.queryDB) # 将pushButton_7的clicked信号连接到queryDB方法上
        self.radioButton.toggled.connect(self.refreshDB)    # 将radioButton的toggled信号连接到refreshDB方法上
        self.radioButton_2.toggled.connect(self.refreshDB)  # 将radioButton_2的toggled信号连接到refreshDB方法上
        self.treeView.clicked.connect(self.selectTB)    # 将treeView的clicked信号连接到selectTB方法上
        self.graphicsView.setBackgroundBrush(QBrush(Qt.white)) # 设置graphicsView的背景颜色
        self.checkBox.stateChanged.connect(self.ViewGrid)  # 将checkbox的stateChanged信号连接到ViewGrid方法上
        self.pushButton_8.clicked.connect(self.clearImage)   # 将pushButton_8的clicked信号连接到saveData方法上
        
        # 创建 QTimer 定时器，每隔一定时间执行 update_data 函数
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)  # 设置时间间隔为5秒（单位：毫秒）
        self.timer = QTimer(self)   # 创建定时器对象
        self.timer.timeout.connect(self.gesture)
        self.timer.start(5000)  # 设置时间间隔为5秒（单位：毫秒）
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
            self.cursor.close()
            self.conn.close()
            self.isconnect = False
            
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
        if not self.isconnect:
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
            self.table = self.lineEdit_4.text()  # 获取数据表名
            # 数据库查询数据
            self.sql = "SELECT * FROM " + self.table + "" # 查询数据表中的所有数据
            self.cursor.execute(self.sql) # 返回值是查询到的数据数量
            self.data = self.cursor.fetchall() # 查询全部数据
            self.cursor.close() # 关闭游标
            self.conn.close()  # 关闭数据库连接
            self.isconnect = False # 设置数据库连接状态
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
            self.plainTextEdit.appendPlainText("Database has connected!")
            return
    
    #  定时器调用的函数，用于更新数据
    def update_data(self):
        if (self.isconnect == False) & self.autoupdate:
            self.isconnect = True  # 设置数据库连接状态
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.table = self.lineEdit_4.text()  # 获取数据表名
            self.password = self.lineEdit_2.text()  # 获取密码
            self.database = self.lineEdit_3.text()  # 获取数据库名
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
            self.table = self.lineEdit_4.text()  # 获取数据表名
            # 数据库查询数据
            self.sql = "SELECT * FROM " + self.table + "" # 查询数据表中的所有数据
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
    def gesture(self):
        if (self.isconnect == False) & self.autoupdate:
            self.isconnect = True  # 设置数据库连接状态
            # 获取文本框中的内容
            self.host = self.lineEdit.text()    # 获取数据库地址
            self.table = self.lineEdit_4.text()  # 获取数据表名
            self.password = self.lineEdit_2.text()  # 获取密码
            self.database = self.lineEdit_3.text()  # 获取数据库名
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
            self.valueChangeJVars(0, self.roll)
            self.valueChangeJVars(1, self.pitch)
            self.valueChangeJVars(2, self.yaw)

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
    
    # 手动刷新tableview中的数据
    def manual_refreshDB(self):
        self.readDB()
        self.plainTextEdit.appendPlainText("Database has refreshed!")
    
    # 清除文本框中的数据
    def cleartext(self):
        self.plainTextEdit.clear()

    # 查询数据库
    def queryDB(self):
        if not self.isconnect:
            self.isconnect = True  # 设置数据库连接状态
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
            self.cursor = self.conn.cursor() # 生成游标对象 cursor
            self.cursor.execute("SHOW TABLES") # 查询数据库中的所有数据表
            self.tables = self.cursor.fetchall() # 查询全部数据
            self.treemodel = QStandardItemModel()   # 创建数据模型
            self.treeView.setModel(self.treemodel)  # 设置数据模型到 QTreeView
            # 创建根节点
            self.root_item = self.treemodel.invisibleRootItem()
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
            
            self.cursor.close() # 关闭数据库连接释放资源
            self.conn.close()
            self.isconnect = False

    def getSelectedPath(self, index):
        # 获取选中项的文本
        text = self.treeView.model().data(index)

        # 如果选中项没有父项，则返回该项的文本
        if not index.parent().isValid():
            return [text]

        # 递归地向上遍历，获取每一级目录的名称
        parent_texts = self.getSelectedPath(index.parent())
        parent_texts.append(text)
        return parent_texts

    # 绘制数据图
    def selectTB(self, index):
        self.max_rows = 100  # 返回最多记录数
        # 获取treeview中选中的表名和列名
        # 获取选中项的文本
        text = self.treeView.model().data(index)
        # 如果选中项没有父项，则返回该项的文本
        if not index.parent().isValid():
            return [text]
        # 递归地向上遍历，获取每一级目录的名称
        parent_texts = self.getSelectedPath(index.parent())
        parent_texts.append(text)
        self.table_name = parent_texts[0]
        self.column_name = parent_texts[1]
        if not self.isconnect:
            self.isconnect = True  # 设置数据库连接状态
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
            self.cursor = self.conn.cursor() # 生成游标对象 cursor
            # 查询数据库中对应列的数据
            self.query = f"SELECT {self.column_name} FROM {self.table_name} LIMIT {self.max_rows}"
            self.cursor.execute(self.query)
            self.graph_data = self.cursor.fetchall()

            # 将数据转换为列表
            data_list = [row[0] for row in self.graph_data]

            # 清空视图内容
            self.graphics_scene.clear()

            # 绘制曲线图
            self.plot_widget = pg.PlotWidget()
            self.plot_widget.plot(data_list)
            self.plot_widget.setBackground('#ffffff') # 设置背景颜色
            self.graphics_scene.addWidget(self.plot_widget)
            self.graphicsView.setScene(self.graphics_scene)
            self.isconnect = False
            self.cursor.close() # 关闭数据库连接释放资源
            self.conn.close()

    # 清除绘制的图像
    def clearImage(self):
        self.graphics_scene.clear()

# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)    # 创建一个QApplication对象
    window = DBWindow()   # 创建一个主窗口对象
    window.show()   # 显示窗口
    sys.exit(app.exec_())   # 进入主循环
