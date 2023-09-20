import numpy as np


class Trajectory(object):
    def __init__(self, startPoint=None, endPoint=None):
        # startPoint and endPoint are numpy arrays
        # 初始化方法，接收起点和终点作为参数，并设置默认的运动速度和采样时间
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.sp_time = 0.1
        self.velocity = 5

    def SetPoint(self, startPoint, endPoint, velocity=5):
        # 设置起点、终点和速度的方法。可以通过调用这个方法来更新轨迹的参数
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.velocity = velocity

    def SetSpTime(self, time):
        # 设置采样时间的方法。可以通过调用这个方法来更新轨迹的参数
        self.sp_time = time

    def Calculate(self):
        # 计算轨迹的方法。这个方法会根据起点、终点和速度来计算轨迹，并返回轨迹上的点、速度和加速度
        distance = np.linalg.norm(self.endPoint - self.startPoint)
        if abs(distance - 0) < 0.01:
            return False,
        T = distance / self.velocity
        if T == 0:
            return False,
        numT = int(round(T / self.sp_time, 2))
        s0 = 0;
        sn = distance
        h = sn - s0
        a0 = s0
        a1 = 0
        a2 = 0
        a3 = 1.0 / (2 * T ** 3) * 20 * h
        a4 = 1.0 / (2 * T ** 4) * (-30) * h
        a5 = 1.0 / (2 * T ** 5) * 12 * h
        point = np.array([[None, None, None]])
        vel = np.array([[None, None, None]])
        acc = np.array([[None, None, None]])
        for i in range(numT + 1):
            t = i * self.sp_time
            s = a0 + a1 * t + a2 * t ** 2 + a3 * t ** 3 + a4 * t ** 4 + a5 * t ** 5
            s_dot = a1 + 2 * a2 * t + 3 * a3 * t ** 2 + 4 * a4 * t ** 3 + 5 * a5 * t ** 4
            s_dot_dot = 2 * a2 + 6 * a3 * t + 12 * a4 * t ** 2 + 20 * a5 * t ** 3
            point = np.append(point, [self.startPoint + ((self.endPoint - self.startPoint) / distance) * s], axis=0)
            vel = np.append(vel, [((self.endPoint - self.startPoint) / distance) * s_dot], axis=0)
            acc = np.append(acc, [((self.endPoint - self.startPoint) / distance) * s_dot_dot], axis=0)

        point = np.delete(point, 0, axis=0)
        vel = np.delete(vel, 0, axis=0)
        acc = np.delete(acc, 0, axis=0)
        return True, point, vel, acc
