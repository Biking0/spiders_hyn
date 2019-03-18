# encoding=utf-8
# Hop Air
# by hyn
# 2018-11-05

import scrapy
import json, logging, urllib
from utils import dataUtil, pubUtil, a5_post_data
import time, datetime
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime as datetime_module
import os, csv, random


# 传入机场
class A5Spider(scrapy.Spider):
    name = 'a5'
    allowed_domains = ['hop.com']
    task = []
    isOK = True

    custom_settings = dict(

        DEFAULT_REQUEST_HEADERS={
            'Host': 'book.hop.com',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.2; SM-G955N Build/NRD90M)',
            'Accept-Language': 'zh-Hans-CN;q=1.0, en-CN;q=0.9, en-US;q=0.8',
            'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5'

        },
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.A5SpiderMiddlewareProxy': 300
        },
        DOWNLOAD_TIMEOUT=30,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=8,
        COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=8,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }

    )

    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.get_session_url = ['https://book.hop.com/plnext/HOPmobileNG/Override.action?']
        self.start_url = [
            'https://book.hop.com/plnext/HOPmobileNG/MFlexPricerAvailabilityDispatcherPui.action;jsessionid=']
        self.start_url_data = '?SITE=H01QH01Q&LANGUAGE=GB&COUNTRY_SITE=GB&UIFWK=ANGULAR'
        self.ADT = 3
        self.version = 1.3

        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()

    def get_session(self, response):

        task_data = response.meta.get('task_data')
        count = task_data.get('count')
        dep = task_data.get('dep')
        arr = task_data.get('arr')
        _date = datetime_module.strptime(task_data.get('date')[:-4], '%Y%m%d')
        session_id = response.headers.getlist('Set-Cookie')[1].split(';')[0].split('=')[1]

        # 循环30天
        for i in range(count):
            date = (_date + datetime.timedelta(days=i)).strftime('%Y%m%d0000')
            # 目标地址参数字典
            post_data = a5_post_data.second_post_data(dep, arr, date, self.ADT)
            start_url = self.start_url[0] + session_id + self.start_url_data

            # 设置无效
            invalid = {
                'date': date[:-4],
                'depAirport': dep,
                'arrAirport': arr,
                'mins': self.custom_settings.get('INVALID_TIME')
            }

            # 封装post_data
            post_data = urllib.urlencode(post_data)
            parse_task_data = {
                'dep': dep,
                'arr': arr,
                'date': date[:-4],
                'start_url': start_url
            }

            # print  'first parse_task_data',parse_task_data
            yield scrapy.Request(start_url,
                                 body=post_data,
                                 callback=self.parse,
                                 dont_filter=True,
                                 meta={'invalid': invalid, 'parse_task_data': parse_task_data, 'post_data': post_data},
                                 method='POST',
                                 errback=self.errback,
                                 )

    # 开始请求
    def start_requests(self):

        permins = 0
        logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        result_iter = None
        while True:
            if hasattr(self, 'local'):
                if not result_iter:
                    result_iter = pubUtil.get_task(self.name, step=7)
                result = next(result_iter)
            else:
                result = pubUtil.getUrl(self.name, 1)
            if not result:
                logging.info('get task error')
                time.sleep(10)
                continue

            # 循环多个任务，现在默认一个
            for data in result:
                # 处理任务 BVE-LYS-201812030000-15
                count = int(data.split(':')[-1])
                (date, dep, arr) = pubUtil.analysisData(data[:-2])
                date = date.replace('-', '') + '0000'

                # logging.info('# input data: ' + dep + '-' + arr + '-' + date + '-' + str(count))

                task_data = {
                    'dep': dep,
                    'arr': arr,
                    'date': date,
                    'count': count
                }

                post_data = urllib.urlencode(a5_post_data.first_post_data(dep, arr, date, self.ADT))
                # 获取session
                yield scrapy.Request(self.get_session_url[0],
                                     body=post_data,
                                     callback=self.get_session,
                                     dont_filter=True,
                                     meta={'post_data': post_data, 'task_data': task_data},
                                     method='POST',
                                     errback=self.errback,
                                     )

    def errback(self, failure):
        """
        异常捕获
        """
        self.log(failure.value, 40)
        self.log(failure.request.meta.get('proxy'), 40)
        self.isOK = False
        return failure.request

    # 解析数据，遍历
    def parse(self, response):
        response_dict = json.loads(response.text)

        data_dict = response_dict.get('data').get('booking').get('mouta')
        # 返回json，ip被封
        request_error_code = jsonpath(response_dict, '$..errorid')
        if request_error_code:
            if request_error_code[0] != 73003:

                fligth_list = jsonpath(data_dict, '$..list_flight')
                # 无航班
                if fligth_list or request_error_code[0] == 2130258:
                    self.task.append(response.meta.get('invalid'))
                    # logging.info('# no flight 2130258')
                    return

                # logging.info('# second ip denied json')
                time.sleep(2)
                meta = response.meta
                parse_task_data = meta.get('parse_task_data')
                # 设置无效
                invalid = {
                    'date': parse_task_data.get('date'),
                    'depAirport': parse_task_data.get('dep'),
                    'arrAirport': parse_task_data.get('arr'),
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                yield scrapy.Request(
                    parse_task_data.get('start_url'),
                    body=meta.get('post_data'),
                    callback=self.parse,
                    dont_filter=True,
                    meta={'invalid': invalid, 'parse_task_data': parse_task_data, 'post_data': meta.get('post_data')},
                    method='POST',
                    errback=self.errback,
                )

                return

        # 当天无航班
        number_code = jsonpath(response_dict, '$..SUBERROR_ITEMS')
        if number_code:
            if number_code[0][0].get('NUMBER') == 931 or number_code[0][0].get('NUMBER') == 977:
                self.task.append(response.meta.get('invalid'))
                # logging.info('# no flight')
                return
            if number_code[0][0].get('NUMBER') == 979 or number_code[0][0].get('NUMBER') == 866:
                print response.text
                return

        # 航班列表
        try:
            fligth_list = jsonpath(data_dict, '$..list_flight')[0]
        except:
            print response.text

        # 解析数据
        for data in fligth_list:

            # 判断中转
            if data.get('availabilityInfo').get('stops') != 0:
                # logging.info('# is change')
                continue

            # 航班数据字典
            segments = data.get('segments')[0]
            # 判断航司
            carrier = segments.get('airline').get('code')
            if carrier != 'A5':
                # logging.info("# other airline" + carrier)
                self.task.append(response.meta.get('invalid'))

            flight_number = carrier + segments.get('flight_number')
            dep_time = time.mktime(
                time.strptime(segments.get('b_date_date') + segments.get('b_date_time'), '%Y%m%d%H%M'))
            arr_time = time.mktime(
                time.strptime(segments.get('e_date_date') + segments.get('e_date_time'), '%Y%m%d%H%M'))
            dep_airport = segments.get('b_location').get('location_code')
            arr_airport = segments.get('e_location').get('location_code')
            dep_city = self.port_city.get(dep_airport, dep_airport)
            arr_city = self.port_city.get(arr_airport, arr_airport)

            price_dict = data.get('fares')[0]

            currency = price_dict.get('currency_code')
            adult_tax = 0
            max_seats = int(price_dict.get('lsaNbrSeat'))

            # 判断座位数
            if max_seats < 1:
                adult_price = 0
                net_fare = 0
            else:
                adult_price = float(price_dict.get('totalAmount')) / self.ADT
                net_fare = adult_price

            is_change = 1
            segments = '[]'
            cabin = 'X'

            item = SpidersHynItem()
            item.update(dict(
                f=flight_number,
                d=dep_time,
                a=arr_time,
                fc=dep_city,
                tc=arr_city,
                c=currency,
                ap=adult_price,
                at=adult_tax,
                n=net_fare,
                m=max_seats,
                cb=cabin,
                cr=carrier,
                i=is_change,
                s=segments,
                g=time.time(),
                da=dep_airport,
                aa=arr_airport,
            ))

            # print item

            yield item

    # 本地获取任务
    def get_task(self):
        input_file = open(os.path.join('utils/src', 'A5.csv'), 'rU')
        reader = csv.reader(input_file)
        data_list = list(reader)
        input_file.close()

        this_day = datetime_module.now() + datetime.timedelta(days=5)
        # 倒序输出
        # data_list = data_list[::-1]
        # 打乱顺序
        random.shuffle(data_list)
        days = 1
        for i in range(8, 30, days):
            _date = this_day + datetime.timedelta(days=i)
            _dt = _date.strftime('%Y-%m-%d')
            for data in data_list:
                if not data or not len(data):
                    continue

                dep = data[0]
                arr = data[1]
                date = _dt.replace('-', '') + '0000'

                logging.info('### input data: ' + dep + '-' + arr + '-' + date)
