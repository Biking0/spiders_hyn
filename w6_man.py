from utils import pubUtil
import sys, os, time

pubUtil.timezone_is_cst()

argv = sys.argv
host_name = argv[1]
num = argv[2] if len(argv) > 2 else 1
proxy = argv[3] if len(argv) > 3 else ''

# host_name = 'hyn-test'
# num = '1'
# proxy=''
while True:
    os.system('scrapy crawl w6 -a host_name=%s -a num=%s' % (host_name, num))
    time.sleep(8)