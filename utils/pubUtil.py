# encoding:utf-8
import os
import csv
import sys
import re
import json
import time
import base64
import random
import logging
import traceback
from datetime import datetime, timedelta
from jsonpath import jsonpath

import requests
from dateutil.tz import tzlocal

sys.path.append('..')  # 测试专用
from spiders_hyn import settings
import subprocess

BASIC_TIME = 0


# mp3 to wav
def mp3_to_wav():
    subprocess.call(
        ['sox', 'utils/br_music/test.mp3', '-e', 'mu-law', '-r', '16k', 'utils/br_music/test_cover.wav', 'remix',
         '1,2'])
    time.sleep(10)

    # subprocess.call(['ffmpeg', '-i', 'test.mp3',
    #                  'test_co1ver.wav'])


# google speech-text voice cover
def voice_cover():
    mp3_to_wav()

    time.sleep(10)

    api_url = "https://speech.googleapis.com/v1beta1/speech:syncrecognize?key=AIzaSyDRSsiT07QM5mbKyEPEitArlT6By8vnaeg"
    audio_file = open('utils/br_music/test_cover.wav', 'rb')
    audio_b64 = base64.b64encode(audio_file.read())
    audio_b64str = audio_b64.decode()  # ②
    # print(type(audio_b64))
    # print(type(audio_b64str))
    audio_file.close()

    # ③
    voice = {
        "config":
            {
                # "encoding": "wav",
                "languageCode": "cmn-Hans-CN"
            },

        "audio":
            {
                "content": audio_b64str
            }
    }
    # 将字典格式的voice编码为utf8
    voice = json.dumps(voice).encode('utf8')

    # 翻墙，获取wn国际代理
    ip = get_proxy('wn')
    proxy = {'https': 'https://' + ip}

    # res = requests.post(api_url, data=voice, headers={'content-type': 'application/json'})
    res = requests.post(api_url, data=voice, proxies=proxy, headers={'content-type': 'application/json'})
    text_data = re.findall(r"\d+\.?\d*", jsonpath(json.loads(res.text), '$..transcript')[0].replace(' ', ''))[0]
    print '# verify number:', text_data

    return text_data


# 从俄罗斯IP获取IP
def nk_get_ip():
    while True:
        try:
            get_proxy_url = 'http://dx.proxy.jiaoan100.com/proxy/nk'
            res = json.loads(requests.get(get_proxy_url).text)
            if len(res) != 0:
                return res[0]
            logging.info('# No IP available ')
            # 俄罗斯IP为空，从小池子中获取
            return get_proxy()
        except Exception as e:
            # print e
            logging.info('# get proxy error, continue')
            time.sleep(2)


# 从小池子中获取IP
def get_proxy(carrier):
    # num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
    # if spider.isOK:
    #     return self.proxy
    # if self.proxy_count < num and self.proxy != '':
    #     self.proxy_count = self.proxy_count + 1
    #     logging.info('using old proxy:' + self.proxy)
    #     return self.proxy
    #
    # self.proxy_count = 0
    # if self.token_count >= 5:

    #     logging.info('# update token')
    #     self.token_count = 0
    #     self.get_token(spider)
    #     return
    proxy = ''
    try:
        params = {'carrier': carrier}
        li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT,
                                     verify=False).text)
        logging.info('Proxy Num: ' + str(len(li)))
        logging.info(str(li))
        proxy = random.choice(li).decode('ascii') or ''
        # self.token_count = self.token_count + 1
    except:
        traceback.print_exc()
        logging.info('get proxy error....')
        return
    finally:
        # spider.proxy_flag = False
        return proxy


# 本地IP备用
def ip_pool(ip_pools):
    # 每个IP休息时长，10分钟，600s，现模拟：间隔时长20分钟，实际使用5分钟，休息15分钟
    rest_time = 100
    for i in range(len(ip_pools)):
        if time.time() - ip_pools[i][1] > rest_time:
            print ('get ip: ', ip_pools[i][0], ip_pools[i][1], time.time(), 'IP rest time(s):', time.time() - \
                   ip_pools[i][1])
            # 更新该IP的获取时间
            ip_pools[i][1] = time.time()
            result_ip = ip_pools[i][0]
            # 将用过的IP放到队尾
            ip_pools.append(ip_pools[i])
            del ip_pools[i]
            return result_ip
    return


# 获取本任务
def get_task(carrier, step=1, days=7):
    input_file = open(os.path.join('utils/src', '%s.csv' % carrier.upper()), 'rU')
    reader = csv.reader(input_file)
    data_list = list(reader)
    input_file.close()

    this_day = datetime.now() + timedelta(days=15)
    # 打乱顺序
    random.shuffle(data_list)

    for i in range(0, days, step):
        _date = this_day + timedelta(days=i)
        _dt = _date.strftime('%Y%m%d')
        for data in data_list:
            if not data or not len(data):
                continue
            print(['%s-%s:%s:%s' % (data[0], data[1], _dt, step)])
            yield ['%s-%s:%s:%s' % (data[0], data[1], _dt, step)]


def timezone_is_cst():
    '''
    判断时区是否是中国上海
    '''
    try:
        if datetime.now(tzlocal()).tzname() != 'CST':
            print('the timezone is not cst. please config it by this command:')
            print('1. sudo tzselect # Asia -> China -> yes')
            print('2. sudo cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime')
            print('3. date # check it again !')
            sys.exit()
    except:
        print('Use Windows will report error, do not close temporarily!!!')


def change_to_int(hms):
    h, m, s = hms.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def adjustDate(fromDate):  # 调整日期为今天之后
    from_datetime = datetime.strptime(fromDate, '%Y-%m-%d')
    from_time = from_datetime.timetuple()
    from_stamp = time.mktime(from_time)
    diff = 0
    right_datetime = from_datetime
    while from_stamp < time.time():
        diff += 1
        right_datetime = from_datetime + timedelta(days=diff)
        right_time = right_datetime.timetuple()
        from_stamp = time.mktime(right_time)
    final = right_datetime.strftime('%Y-%m-%d')
    return final


def dateIsInvalid(dt):  # 是过去的日期
    dt_time = time.strptime(dt + " 23:59:59", '%Y-%m-%d %H:%M:%S')
    dt_stamp = time.mktime(dt_time)
    if dt_stamp < time.time():
        return True
    return False


def analysisData(data):
    p = data.split(':')
    fromTo = p[0].split('-')
    dep = fromTo[0]
    to = fromTo[1]
    dt = datetime.strptime(p[1], '%Y%m%d').strftime('%Y-%m-%d')
    return (dt, dep, to)


def getUrl(carrier, num=1, url=None):
    params = {
        'carrier': carrier,
        'num': num,
    }
    headers = {
        'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'accept-encoding': "gzip, deflate",
        'accept-language': "zh-CN,zh;q=0.9",
        'cache-control': "no-cache",
        'connection': "keep-alive",
        'host': "116.196.116.117",
        'upgrade-insecure-requests': "1",
        'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    }
    try:
        if not url:
            url = settings.GET_TASK_URL
        content = requests.get(url, headers=headers, params=params, timeout=settings.GET_URL_TIMEOUT).text
    except:
        # traceback.print_exc()
        return None
    data = json.loads(content)
    if 'status' not in data or data['status'] != 0:
        return None
    dt = data.get('data')
    return dt


def pushUrl(data):
    datas = {
        'carrier': data['carrier'],
        'als': data['als'],
        'dts': data['dts'],
    }
    try:
        res = requests.post(settings.PUSH_TASK_URL, data=json.dumps(datas), timeout=settings.GET_URL_TIMEOUT)
        s = requests.session()
        s.keep_alive = False
    except:
        logging.info('pushUrl Error...')


def invalidData(action, infos, push_data_url, host_name):
    if not len(infos):
        return True
    data = {
        'action': action,
        'data': infos,
        'name': host_name
    }
    requests.adapters.DEFAULT_RETRIES = 5
    try:
        res = requests.post(push_data_url, data=json.dumps(data), headers={'Connection': 'close'},
                            timeout=settings.GET_URL_TIMEOUT)
        print('invalidData: ' + res.text + ' num: ' + str(len(infos)))
        return True
    except:
        return False


def addData(action, infos, push_data_url, host_name, carrier=None):
    if not len(infos):
        return True
    data = {
        'action': action,
        'data': infos,
        'name': host_name
    }
    if not carrier:
        carrier = infos[0].get('cr')
    params = {'carrier': carrier}
    requests.adapters.DEFAULT_RETRIES = 5
    try:
        res = requests.post(push_data_url, params=params, data=json.dumps(data), headers={'Connection': 'close'},
                            timeout=settings.GET_URL_TIMEOUT)
        print('pushData: ' + res.text + ' num: ' + str(len(infos)))
        return True
    except:
        # traceback.print_exc()
        return False


def insertLog(carrier, dt, dep, to, name, log_content):
    data = {}
    data['fromDate'] = time.mktime(time.strptime(dt, '%Y-%m-%d'))
    data['fromCity'] = dep
    data['toCity'] = to
    data['carrier'] = carrier
    data['content'] = log_content
    data['nodename'] = name
    datas = {
        'action': 'add',
        'data': [data],
    }
    param = {'carrier': carrier}
    requests.adapters.DEFAULT_RETRIES = 5
    try:
        res = requests.post(settings.LOG_URL, params=param, data=json.dumps(datas), timeout=settings.GET_URL_TIMEOUT)
    except:
        return


def heartbeat(name, carrier, num, permins, version=1):
    params = {
        'carrier': carrier,
        'num': num,
        'name': name,
        'permins': permins or 0,
        'version': version,
    }
    try:
        return requests.get(settings.HEARTBEAT_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text
    except:
        return 'heartbeat error'


if __name__ == '__main__':
    # task = {
    #     'arrAirport': 'BHX',
    #     'date': '20180615',
    #     'depAirport': 'VIE',
    # }
    # print(invalidData('invalid', [task], 'http://dx.spider2.jiaoan100.com/br/newairline?carrier=ew', 'lin'))
    # num = 0
    # while True:
    #     print(num)
    #     getUrl('TW')
    #     time.sleep(2)
    #     num += 1
    # nk_get_ip()
    voice_cover()
