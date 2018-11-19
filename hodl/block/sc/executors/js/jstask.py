from cryptogr import h
from block.sc.executors.js.jstools import CTX
import json
import time
from threading import Thread
import logging as log


BENCHMARK = None


def benchmark():
    ctx = CTX()
    ts = time.time()
    ctx.run_script('for (var i =0;i<200000000;i++){Math.pow(5,1000)}')
    global BENCHMARK
    BENCHMARK = time.time() - ts


Thread(target=benchmark).start()


class JSTask:
    def __init__(self, code):
        self.code = code
        self.done = False
        self.ans = None
        self.difficulty = 1
        self.context = str(CTX())

    def run(self, ctx=None):
        if not ctx:
            ctx = CTX.from_json(self.context)
        if not BENCHMARK:
            print('benchmark not finished')
            while not BENCHMARK:
                time.sleep(0.1)
        t1 = time.time()
        ctx.run_script(self.code)
        self.difficulty = (time.time() - t1) / BENCHMARK
        self.ans = ctx.run_script('__answer__')
        ctx.run_script('__answer__=""')
        self.context = str(ctx)
        self.done = True

    def __str__(self):
        return json.dumps([self.code, self.done, self.ans, self.difficulty, self.context])

    @classmethod
    def from_json(cls, s):
        s = json.loads(s)
        self = cls(s[0])
        self.done = s[1]
        self.ans = s[2]
        self.difficulty = s[3]
        self.context = s[4]
        return self

    def result_hash(self):
        return h(json.dumps([str(self.context), str(self.ans)]))

    def result_dump(self):
        return json.dumps([str(self.context), str(self.ans)])


def code_to_tasks(code):
    tasks = []
    code = code.split('\n')
    l = 0
    for i in range(len(code)+1):
        if i - l >= 10:
            if '\n'.join(code[:i]).count('{') == '\n'.join(code[:i]).count('}'):
                tasks.append(JSTask('\n'.join(code[l:i])))
                l = i
    if l != len(code):
        task = JSTask('\n'.join(code[l:]))
        tasks.append(task)
    return tasks


def msg_task(author, msg):
    return JSTask('''__msg__("{}")'''.format(json.dumps([author, msg])))


def net_task(author, msg):
    return JSTask('''__net__("{}")'''.format(json.dumps([author, msg])))


js = [JSTask, code_to_tasks, msg_task, net_task]
