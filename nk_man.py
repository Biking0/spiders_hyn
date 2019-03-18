# encoding:utf-8

import sys, os, time
from utils.pubUtil import timezone_is_cst

timezone_is_cst()  # 判断时区

CARRIER = 'nk'

argv = sys.argv
if len(argv) < 2:
    print('pls input like this:')
    print('python be_spider.py lin 1 ')
    sys.exit()

num = 1 if len(argv) < 3 else argv[2]  # 爬虫序号

arg_set = set()  # 生成后面的参数
arg_big = set()
if len(argv) > 3:
    for arg in argv[3:]:
        if arg == '1':  # 兼容以前的proxy版本的
            arg_set.add('proxy=1')
        else:
            k, v = arg.split('=')
            if k == 'local':
                arg_big.add('CLOSESPIDER_TIMEOUT=0')

            if k.isupper():
                arg_big.add(arg.replace(' ', ''))
            else:
                arg_set.add(arg.replace(' ', ''))

arg_str = ''
if len(arg_set):
    arg_str = ' -a ' + ' -a '.join(arg_set)
if len(arg_big):
    arg_str += ' -s ' + ' -s '.join(arg_big)
    if not os.path.exists('logs'):
        os.mkdir('logs')

cmd = 'scrapy crawl %s -a host_name=%s -a num=%s' % (CARRIER, argv[1], num) + arg_str

while True:
    os.system(cmd)
    time.sleep(8)
