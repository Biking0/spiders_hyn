# encoding=utf-8
# BY,TOM
# by hyn
# 2018-10-29

import scrapy
import requests, urllib
import json, logging
from utils import dataUtil, pubUtil

import time, datetime

from spiders_hyn.items import SpidersHynItem
from spiders_hyn import middlewares


# 传入机场
class by_Spider(scrapy.Spider):
    name = 'by'

    allowed_domains = ['tui.co.uk']

    task = []

    isOK = True

    custom_settings = dict(

        DEFAULT_REQUEST_HEADERS={
            'Content-Type': 'application/json; charset=UTF-8'
        },
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.BYSpidersHynSpiderMiddlewareGetCookies': 300
        },

        # 处理连接超时
        # DOWNLOAD_TIMEOUT=20,
        # DOWNLOAD_TIMEOUT=30,
        DOWNLOAD_TIMEOUT=40,
        # 延迟1秒
        # DOWNLOAD_DELAY=1,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=8,
        COOKIES_ENABLED=True,
        INVALID_TIME=45,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }

    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.first_url = "https://www.tui.co.uk/flight/search?"
        self.second_url = ['https://www.tui.co.uk/flight/ws/selectedflights?']
        self.ADT = '3'
        self.version = 1.2

        # 通过机场获取城市
        self.portCitys = dataUtil.get_port_city()
        self.currency = 'GBP'
        self.carrier = "BY"
        self.cabin = 'X'
        self.isChange = 1
        self.flag = True

        # 参数传递
        self.dep = ''
        self.arr = ''
        self.date = ''

    # 开始请求，重写该方法
    def start_requests(self):
        permins = 0
        logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        while True:
            result = pubUtil.getUrl('by', 1)
            if not result:
                logging.info('get task error')
                time.sleep(10)
                continue
            for data in result:
                logging.info("###input data: " + data)
                (dt, dep, to) = pubUtil.analysisData(data)

                self.dep = dep
                self.arr = to
                self.date = dt

                second_data = {
                    'flyingFrom[]': self.dep,
                    'flyingTo[]': self.arr,
                    'depDate': self.date,
                    'returnDate': '',
                    'adults': self.ADT,
                    'children': '0',
                    'infants': '0',
                    'infantAge': '',
                    'isOneWay': 'true',
                    'childAge': '',
                    'searchType': 'selected',
                    'tabId': dep,
                    'cycleDates': dt,
                    'duration': '0'
                }

                second_url = '%s%s' % (self.second_url[0], urllib.urlencode(second_data))

                # 设置无效
                invalid = {
                    'date': self.date.replace('-', ''),
                    'depAirport': self.dep,
                    'arrAirport': self.arr,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                yield scrapy.Request(second_url,
                                     callback=self.parse,
                                     dont_filter=True,
                                     meta={'invalid': invalid},
                                     errback=self.errback)

    def errback(self, failure):
        """
        异常捕获
        """
        self.log(failure.value, 40)
        self.isOK = False
        return failure.request

    # 解析数据，遍历
    def parse(self, response):
        try:
            json_dict = json.loads(response.body)
        except:
            print(' except second request error')
            self.flag = True
            return

        # 当天无航班
        if len(json_dict.get('itinerary')) == 0:
            logging.info("no flight")
            self.task.append(response.meta.get('invalid'))
            return

        for data in json_dict.get('itinerary'):
            item = SpidersHynItem()
            outbound = data.get('outbound')

            # TOM 4238
            item["f"] = self.carrier + outbound.get('flightno').split(' ')[1]
            item['d'] = time.mktime(time.strptime(
                outbound['schedule']['departureDate'] + outbound['schedule'][
                    'departureTime'], '%Y/%m/%d%H:%M'))
            item['a'] = time.mktime(time.strptime(
                outbound.get('schedule').get('arrivalDate') + outbound.get('schedule').get(
                    'arrivalTime'), '%Y/%m/%d%H:%M'))

            item['da'] = outbound.get('departureAirportData').get('id')
            item['aa'] = outbound.get('arrivalAirportData').get('id')

            item['fc'] = self.portCitys.get(item['da'], item['da'])
            item['tc'] = self.portCitys.get(item['aa'], item['aa'])
            item['m'] = int(data.get('minAvail'))

            # # 测试税费
            # if data.get('pricePP') != data.get('price'):
            #     print '#####################TaX test: ' + item['depAirport'] + '-' + item['arrAirport'] + '-' + item[
            #         'depTime']

            if item['m'] < int(self.ADT):
                item['m'] = 0
                item['ap'] = 0
                item['at'] = 0
                item['n'] = 0
            else:
                item['c'] = self.currency
                item['ap'] = float(data.get('price')) / int(self.ADT)
                item['n'] = float(data.get('pricePP'))
                item['at'] = 0

            item['cb'] = self.cabin
            item['cr'] = self.carrier
            item['i'] = self.isChange
            item['s'] = '[]'
            item['g'] = time.time()

            # 测试数据
            # print ('item', item)

            yield item
