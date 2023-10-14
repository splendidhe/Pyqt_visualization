# 求所有的水仙花数
# 要求三位整数且各个位上的立方和等于该数本身
import math
for i in range(100, 1000):
    a = i // 100
    b = i // 10 % 10
    c = i % 10
    if i == math.pow(a, 3) + math.pow(b, 3) + math.pow(c, 3):
        print(i)
