from OpenGL.GLUT import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import OpenGLControl as DrawRB
import numpy as np
from Robot import *
from Trajectory import *


class RobotSimulator(QMainWindow):
    def __init__(self, *args):
        super(RobotSimulator, self).__init__(*args)
        # 调用父类RobotSimulator的初始化方法
        loadUi('model_diaplay.ui', self) # 加载ui文件
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


# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)    # 创建一个QApplication对象
    window = RobotSimulator()   # 创建一个RobotSimulator对象
    window.setupUI()    # 设置UI
    window.show()   # 显示窗口
    sys.exit(app.exec_())   # 进入主循环
