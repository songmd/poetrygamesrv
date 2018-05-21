import threading
import time


def hello(name):
    print("hello %s\n" % name)


class TestCls:
    def __init__(self, name):
        self.name = name

    def hello(self, name):
        print("%s say hello %s\n" % (self.name, name))


class Testcoroutine:

    async def do(self):
        print('do')
        print(await 1)
        return 1




if __name__ == "__main__":
    import os
    import random

    # cls = TestCls('bob')
    # timer = threading.Timer(2.0, cls.hello, ["Hawk"])
    # timer.start()
    # # timer.cancel()
    #
    # timer = threading.Timer(3.0, hello, ["Hawk"])
    # # timer.start()
    #
    # r = Testcoroutine()
    # r.do()
    # print('end')
    import os
    import random

    files = [f for f in os.listdir('wxtx') if not os.path.isdir(f)]
    names = []
    with open('name2.txt') as nf:
        while True:
            name = nf.readline()
            if name:
                names.append(name.strip())
            else:
                break

    random.shuffle(names)
    random.shuffle(files)

    for i in range(min(len(files), len(names))):
        print(files[i], names[i])

    # fs = os.listdir('wxtx')
    # for f1 in fs:
    #     # tmp_path = os.path.join(f,f1)
    #     if not os.path.isdir(f1):
    #         print('文件: %s' % f1)
    #     else:
    #         print('文件夹：%s' % f1)
