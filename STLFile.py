import struct
from OpenGL.GL import *


# class for a 3d point
class createpoint:  # 表示一个三维点，包含了点的坐标（x、y、z）和颜色（默认为红色） 
    def __init__(self, p, c=(1, 0, 0)):
        self.point_size = 0.5
        self.color = c
        self.x = p[0]
        self.y = p[1]
        self.z = p[2]

    def glvertex(self): # 用于在OpenGL中绘制该点
        glVertex3f(self.x, self.y, self.z)


# class for a 3d face on a model
class createtriangle:   # 表示一个三角面片，包含了三个点（p1、p2、p3）和法向量（normal）
    points = None   # 三角面片的三个点
    normal = None   # 三角面片的法向量

    def __init__(self, p1, p2, p3, n=None): 
        # 3 points of the triangle
        self.points = createpoint(p1), createpoint(p2), createpoint(p3) # 三角面片的三个点

        # triangles normal
        self.normal = createpoint(self.calculate_normal(self.points[0], self.points[1], self.points[2]))  # (0,1,0) 三角面片的法向量

    # calculate vector / edge
    def calculate_vector(self, p1, p2): # 计算两个点之间的向量
        return -p1.x + p2.x, -p1.y + p2.y, -p1.z + p2.z # 返回一个向量

    def calculate_normal(self, p1, p2, p3): # 计算三角面片的法向量
        a = self.calculate_vector(p3, p2)   # 计算向量a
        b = self.calculate_vector(p3, p1)   # 计算向量b
        # calculate the cross product returns a vector
        return self.cross_product(a, b) # 返回向量a和向量b的叉积

    def cross_product(self, p1, p2):    # 计算两个向量的叉积
        return (p1[1] * p2[2] - p2[1] * p1[2]), (p1[2] * p2[0]) - (p2[2] * p1[0]), (p1[0] * p2[1]) - (p2[0] * p1[1])    # 返回两个向量的叉积


class loader:
    def __init__(self, filename):   # 读取stl文件
        self.model = []
        self.load_stl(filename)

    # return the faces of the triangles
    def get_triangles(self):    # 返回三角面片的法向量
        if self.model:
            for face in self.model:
                yield face

    # draw the models faces
    def draw(self): # 绘制三角面片
        glBegin(GL_TRIANGLES)
        for tri in self.get_triangles():    # 遍历三角面片
            glNormal3f(tri.normal.x, tri.normal.y, tri.normal.z)
            glVertex3f(tri.points[0].x, tri.points[0].y, tri.points[0].z)
            glVertex3f(tri.points[1].x, tri.points[1].y, tri.points[1].z)
            glVertex3f(tri.points[2].x, tri.points[2].y, tri.points[2].z)
        glEnd()

    # load stl file detects if the file is a text file or binary file
    def load_stl(self, filename):   # 读取stl文件
        # read start of file to determine if it's a binay stl file or an ascii stl file
        fp = open(filename, 'rb')
        h = fp.read(80)
        type = h[0:5]
        fp.close()
        if type == b'solid':
            # print ("reading stl file "+str(filename))
            self.load_text_stl(filename)
        else:
            # print ("reading binary stl file "+str(filename))
            self.load_binary_stl(filename)

    # read text stl match keywords to grab the points to build the model
    def load_text_stl(self, filename):  # 读取文本stl文件
        fp = open(filename, 'r')

        for line in fp.readlines():   # 遍历文件的每一行
            words = line.split()
            if len(words) > 0:
                if words[0] == 'solid': # 读取solid后面的名字
                    self.name = words[1]

                if words[0] == 'facet': # 读取facet后面的法向量
                    center = [0.0, 0.0, 0.0]
                    triangle = []
                    normal = (eval(words[2]), eval(words[3]), eval(words[4]))

                if words[0] == 'vertex':    # 读取vertex后面的点
                    triangle.append((eval(words[1]), eval(words[2]), eval(words[3])))

                if words[0] == 'endloop':   # 读取endloop后面的点
                    # make sure we got the correct number of values before storing
                    if len(triangle) == 3:
                        self.model.append(createtriangle(triangle[0], triangle[1], triangle[2], normal))
        fp.close()  # 关闭文件

    # load binary stl file check wikipedia for the binary layout of the file
    # 翻译上一句 读取二进制stl文件，检查维基百科的文件二进制布局
    # we use the struct library to read in and convert binary data into a format we can use
    # 翻译上一句 我们使用struct库来读取和转换二进制数据为我们可以使用的格式
    def load_binary_stl(self, filename):    # 读取二进制stl文件
        fp = open(filename, 'rb')
        h = fp.read(80)

        l = struct.unpack('I', fp.read(4))[0]   # 读取三角面片的个数
        count = 0
        while True:
            try:
                p = fp.read(12) # 读取三角面片的法向量
                if len(p) == 12:
                    n = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                p = fp.read(12) # 读取三角面片的三个点
                if len(p) == 12:
                    p1 = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                p = fp.read(12) # 读取三角面片的三个点
                if len(p) == 12:
                    p2 = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                p = fp.read(12) # 读取三角面片的三个点
                if len(p) == 12:
                    p3 = struct.unpack('f', p[0:4])[0], struct.unpack('f', p[4:8])[0], struct.unpack('f', p[8:12])[0]

                new_tri = (n, p1, p2, p3)   # 三角面片的法向量和三个点

                if len(new_tri) == 4:   # 三角面片的法向量和三个点
                    tri = createtriangle(p1, p2, p3, n)
                    self.model.append(tri)
                count += 1
                fp.read(2)

                if len(p) == 0:
                    break
            except EOFError:
                break
        fp.close()


