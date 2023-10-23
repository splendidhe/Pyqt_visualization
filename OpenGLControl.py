from OpenGL import GLU
from PyQt5 import QtCore
from PyQt5 import QtOpenGL
from numpy import arange

# from ConfigRobot import *
from GlobalFunc import *
from STLFile import *


class GLWidget(QtOpenGL.QGLWidget):
    xRotationChanged = QtCore.pyqtSignal(int)   # 信号
    yRotationChanged = QtCore.pyqtSignal(int)   # 信号
    zRotationChanged = QtCore.pyqtSignal(int)   # 信号

    def __init__(self, parent=None, objRobot=None):
        super(GLWidget, self).__init__(parent)
        self.objRobot = objRobot    # 机器人对象
        self.xRot = -2584   # x轴旋转角度
        self.yRot = 1376    # y轴旋转角度
        self.zRot = 0   # z轴旋转角度
        self.z_zoom = -200  # 缩放
        self.xTran = 0  # x轴平移
        self.yTran = 0  # y轴平移
        self.isDrawGrid = True  # 是否绘制网格
        print("Loading stl files...")
        self.model = loader('E:\Python_Environment\PyCharm\pycharm_code\Pyqt\model\little_ship.STL') # 加载stl文件
        print("All done.")

        self.listPoints = np.array([[0, 0, 0]]) 
        self.AllList = np.array([self.listPoints])  
        self.stt = np.array([]) 
        self.color = np.array([0])  

    def setXRotation(self, angle):  # 设置x轴旋转角度
        self.normalizeAngle(angle)  # 角度归一化
        if angle != self.xRot:
            self.xRot = angle
            self.xRotationChanged.emit(angle)   # 角度改变信号
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除颜色缓存和深度缓存
            self.updateGL() # 更新opengl

    def setYRotation(self, angle):  # 设置y轴旋转角度
        self.normalizeAngle(angle)  # 角度归一化
        if angle != self.yRot:
            self.yRot = angle
            self.yRotationChanged.emit(angle)   # 角度改变信号
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除颜色缓存和深度缓存
        # self.updateGL() # 更新opengl

    def setZRotation(self, angle):  # 设置z轴旋转角度
        self.normalizeAngle(angle)  # 角度归一化
        if angle != self.zRot:
            self.zRot = angle
            self.zRotationChanged.emit(angle)   # 角度改变信号
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除颜色缓存和深度缓存
            self.updateGL() # 更新opengl
    
    def setXYTranslate(self, dx, dy):
        self.xTran += 3.0 * dx
        self.yTran -= 3.0 * dy
        self.updateGL()

    def setZoom(self, zoom):    # 设置缩放
        self.z_zoom = zoom  
        self.updateGL() # 更新opengl

    def updateJoint(self):  # 更新关节角度
        self.updateGL() # 更新opengl

    def initializeGL(self): # 初始化opengl
        lightPos = (5.0, 5.0, 10.0, 1.0)    # 光源位置以四元组变量表示
        reflectance1 = (0.8, 0.1, 0.0, 1.0) # 反射系数
        reflectance2 = (0.0, 0.8, 0.2, 1.0) # 反射系数
        reflectance3 = (0.2, 0.2, 1.0, 1.0) # 反射系数

        ambientLight = [0.7, 0.7, 0.7, 1.0] # 环境光
        diffuseLight = [0.7, 0.8, 0.8, 1.0] # 漫反射光
        specularLight = [0.4, 0.4, 0.4, 1.0]    # 镜面反射光
        positionLight = [20.0, 20.0, 20.0, 0.0] # 光源位置

        glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLight)  # 设置环境光
        glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuseLight)  # 设置漫反射光
        glLightfv(GL_LIGHT0, GL_SPECULAR, specularLight)    # 设置镜面反射光
        glLightModelf(GL_LIGHT_MODEL_TWO_SIDE, 1.0) # 设置光照模型
        glLightfv(GL_LIGHT0, GL_POSITION, positionLight)    # 设置光源位置

        glEnable(GL_LIGHTING)   # 启用光照
        glEnable(GL_LIGHT0) # 启用光源0
        glEnable(GL_DEPTH_TEST) # 启用深度测试
        glEnable(GL_NORMALIZE)  # 启用法向量归一化
        # glEnable(GL_BLEND);   # 启用混合
        glClearColor(228, 228, 228, 1.0)    # 设置清除颜色缓存时的颜色

    def drawGL(self):
        glPushMatrix()  # 压栈 调用glPushMatrix函数保存当前矩阵状态
        if self.isDrawGrid:
            self.drawGrid() # 绘制网格
        self.setupColor([96.0 / 255, 96 / 255.0, 192.0 / 255])  # 设置颜色
        glRotatef(RadToDeg(self.objRobot.JVars[0]), 1.0, 0.0, 0.0)  # 旋转
        glRotatef(RadToDeg(self.objRobot.JVars[1]), 0.0, 1.0, 0.0)  # 旋转
        glRotatef(RadToDeg(self.objRobot.JVars[2]), 0.0, 0.0, 1.0)  # 旋转
        self.model.draw()  # 绘制模型
        glPopMatrix()   # 出栈 调用glPopMatrix函数恢复矩阵状态

    def paintGL(self):  # 绘制opengl
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清除颜色缓存和深度缓存
        glPushMatrix()  # 压栈 调用glPushMatrix函数保存当前矩阵状态
        glTranslate(0, 0, self.z_zoom)  # 将当前绘制的对象沿着Z轴方向平移一定距离
        glTranslate(self.xTran, self.yTran, 0)  # 将当前绘制的对象沿着X轴和Y轴方向平移一定距离
        glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)  # 旋转
        glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)  # 旋转
        glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)  # 旋转
        glRotated(+90.0, 1.0, 0.0, 0.0) # 旋转
        self.drawGL()   # 绘制opengl
        self.DrawPoint([255.0 / 255, 255.0 / 255, 255.0 / 255.0], 1.5)  # 绘制点
        glPopMatrix()   # 出栈 调用glPopMatrix函数恢复矩阵状态

    def DrawPoint(self, color, size):   # OpenGL中绘制点和线段
        glPushMatrix()  # 压栈 调用glPushMatrix函数保存当前矩阵状态
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, self.color) # 设置颜色
        glPointSize(size)  # 设置点的大小
        for i in np.arange(len(self.listPoints) - 1):
            if self.color[i] == 1:
                glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0]) # 设置颜色
                glBegin(GL_LINES)   # 绘制线段
                glVertex3f(self.listPoints[i][0], self.listPoints[i][1], self.listPoints[i][2]) # 设置线段的起点
                glVertex3f(self.listPoints[i + 1][0], self.listPoints[i + 1][1], self.listPoints[i + 1][2]) # 设置线段的终点
                glEnd() # 结束绘制线段
        glPopMatrix()   # 出栈 调用glPopMatrix函数恢复矩阵状态

    def resizeGL(self, width, height):  # 用于在OpenGL中调整视口大小
        side = min(width, height)   # 获取宽度和高度的最小值
        if side < 0:
            return
        glViewport(0, 0, width, height) # 设置视口的位置和大小
        glMatrixMode(GL_PROJECTION)   # 设置矩阵模式为投影模式
        glLoadIdentity()    # 重置当前指定的矩阵为单位矩阵
        GLU.gluPerspective(35.0, width / float(height), 1.0, 20000.0)   # 设置透视投影
        glMatrixMode(GL_MODELVIEW)  # 设置矩阵模式为模型视图模式
        glLoadIdentity()    # 重置当前指定的矩阵为单位矩阵
        glTranslated(0.0, 0.0, -40.0)   # 将当前绘制的对象沿着Z轴方向平移一定距离
    
    # 在鼠标按下事件发生时，会获取当前鼠标的位置信息，并将其保存在self.lastPos变量中
    def mousePressEvent(self, event):   
        self.lastPos = event.pos()

    def drawGrid(self): # 用于在OpenGL中绘制一个网格
        glPushMatrix()  # 压栈 调用glPushMatrix函数保存当前矩阵状态
        color = [8.0 / 255, 108.0 / 255, 162.0 / 255]   # 设置颜色
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, color)   # 设置颜色
        step = 50   # 设置步长
        num = 15    # 设置数量
        # 通过循环遍历-num到num+1之间的值
        # 使用glBegin和glEnd函数分别表示开始和结束绘制
        for i in arange(-num, num + 1):
            glBegin(GL_LINES)   # 绘制线段
            glVertex3f(i * step, -num * step, 0)
            glVertex3f(i * step, num * step, 0)
            glVertex3f(-num * step, i * step, 0)
            glVertex3f(num * step, i * step, 0)
            glEnd() # 结束绘制线段
        glPopMatrix()   # 出栈 调用glPopMatrix函数恢复矩阵状态

    # 在鼠标移动事件发生时，会获取当前鼠标的位置信息，
    # 并计算出其相对于上一次鼠标位置的偏移量。
    # 根据不同的鼠标按钮状态，执行不同的操作
    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & QtCore.Qt.LeftButton:
            # 若鼠标左键被按下，调用setXRotation和setYRotation函数分别更新X轴和Y轴旋转变换参数，从而实现场景的旋转
            self.setXRotation(self.xRot + 4 * dy)
            self.setYRotation(self.yRot - 4 * dx)
        elif event.buttons() & QtCore.Qt.RightButton:
            # 若鼠标右键被按下，调用setZoom函数更新视角缩放变换参数，与Y轴偏移量成正比，从而实现场景的缩放
            self.setZoom(self.z_zoom + 2.0 * dy)
        elif event.buttons() & QtCore.Qt.MidButton:
            # 若鼠标中键被按下，调用setXYTranslate函数更新X轴和Y轴平移变换参数，从而实现场景的平移
            self.setXYTranslate(dx, dy)
        self.lastPos = event.pos() # 将当前鼠标位置信息保存在self.lastPos变量中
    
    # 用于设置材质的环境光和散射光颜色
    def setupColor(self, color): 
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, color)   # 设置颜色

    def xRotation(self):    # 获取x轴旋转角度
        return self.xRot

    def yRotation(self):    # 获取y轴旋转角度
        return self.yRot

    def zRotation(self):    # 获取z轴旋转角度
        return self.zRot

    def normalizeAngle(self, angle):    # 角度归一化
        while angle < 0:
            angle += 360 * 16   # 角度增加360*16
        while angle > 360 * 16:
            angle -= 360 * 16   # 角度减少360*16
