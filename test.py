import numpy as np

def f(x):
    return x**2

max = 2
min = 0

x = np.linspace(min, max, 10001)

y1 = f(x)
y2 = f(x+1/10000)

print(np.add(y1, y2))


