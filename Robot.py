from Kinematics import *


class Robot(object):  # 机器人类
    """docstring for Robot"""

    def __init__(self):
        super(Robot, self).__init__()
        self.cf = ConfigRobot() # 机器人配置
        self.q = self.cf.q_init # 机器人关节角度
        self.d = self.cf.d  # 机器人关节长度
        self.a = self.cf.a  # 机器人关节长度
        self.alpha = self.cf.alpha  # 机器人关节角度
        self.fwd = FwdKinematics()  # 正运动学
        self.inv = InvKinematics()  # 逆运动学
        self.JVars = self.cf.q_init[1:] # 机器人关节角度
        self.q1P = self.JVars   # 机器人关节角度
        self.q2P = self.JVars   # 机器人关节角度
        self.EVars = np.array([])   # 机器人末端位姿
        self.EVars = self.fwd.Cal_Fwd_Position(self.JVars)  # 机器人末端位姿

    def CalFwdPostion(self, JVars): # 计算正运动学
        self.JVars = JVars  # 机器人关节角度
        self.q1P = self.q2P = JVars # 机器人关节角度
        self.EVars = self.fwd.Cal_Fwd_Position(JVars)   # 机器人末端位姿

    def CalInvPostion(self, EVars): # 计算逆运动学
        sol = self.inv.FindTheBestSolution(EVars, self.q1P, self.q2P)   # 机器人关节角度
        if sol is not None: # 机器人关节角度
            result = self.inv.Cal_Inv_Position(EVars, sol)  # 机器人关节角度
            if result[0]:   # 机器人关节角度
                self.EVars = EVars  # 机器人末端位姿
                self.JVars = result[1]  # 机器人关节角度
                self.q2P = self.q1P # 机器人关节角度
                self.q1P = self.JVars   # 机器人关节角度
            else:
                print("error while calculate")

    def CalInvPositionEx(self, EVars, q1p=None, q2p=None, sol=-1):  # 计算逆运动学
        if sol == -1:  
            sol = self.inv.FindTheBestSolution(EVars, q1p, q2p) # 机器人关节角度
        if sol is not None:
            result = self.inv.Cal_Inv_Position(EVars, sol)  # 机器人关节角度
            if result[0]:
                JVars = result[1]
                return True, JVars
            else:
                print("error while calculate")
                return False,
        else:
            return False,

    def GetCurrentStatus(self):
        return self.EVars
