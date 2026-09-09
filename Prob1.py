def func1(x):
    for i in range(3):
        x *= 2
    return x + x

def func2(y, z):
    A = func1(y+1) % 8
    z, A = A + z, y
    return z ** A

if __name__ == '__main__':
    print(func2(1, 5))
