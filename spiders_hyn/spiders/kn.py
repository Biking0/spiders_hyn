# encoding=utf-8
# 中国联航,kn
# by hyn
# 2019-02-18

import scrapy
import json, logging, random
from utils import dataUtil, pubUtil
import time, datetime, urllib, requests, traceback
from spiders_hyn.items import SpidersHynItem
from spiders_hyn import middlewares
from fake_useragent import UserAgent


class AqSpider(scrapy.Spider):
    name = 'kn'
    allowed_domains = ['wx.flycua.com']
    task = []
    isOK = True

    custom_settings = dict(

        # DEFAULT_REQUEST_HEADERS={
        #     'android_version': '1.44',
        #     'Content-Type': 'application/x-www-form-urlencoded',
        #     'User-Agent': 'Apache-HttpClient/UNAVAILABLE (java 1.4)',
        #     'Cookie': 'JSESSIONID=owgnt2x88n93ntitf4w0xhtx',
        #     'Host': 'www.9air.com'
        # },

        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.KnGetProxy': 300
        },
        DOWNLOAD_TIMEOUT=10,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=10,
        # COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=10,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }

    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = ['http://wx.flycua.com/wechat/pip/book/flightSearch.json']
        self.ADT = 3
        self.version = 1

        # 通过机场获取城市
        self.portCitys = dataUtil.get_port_city()
        self.session_id = ''
        self.session_flag = True
        self.headers = {
            'Host': "wx.flycua.com",
            # 'content-length': "95",
            'Origin': "http://wx.flycua.com",
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
            'isWechat': "H5",
            'Content-Type': "application/json",
            'Accept': "application/json, text/plain, */*",
            'Cookie': "JSESSIONID=7DB644CF0C5608A8198719E96B1AF8B9",
            # 'referer': "http://wx.flycua.com/wechat/?code=021QpAK41iotwS1ed5L41EJxK41QpAKu&state=1",
            # 'cache-control': "no-cache",
            # 'postman-token': "ee1a68b8-780c-3243-f7fb-e4b552929ee4"
        }
        self.timeout = 5

    # 开始请求
    def start_requests(self):
        permins = 0
        logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        result_iter = None
        while True:
            if hasattr(self, 'local'):
                if not result_iter:
                    result_iter = pubUtil.get_task(self.name, days=30)
                result = next(result_iter)
            else:
                result = pubUtil.getUrl(self.name, 1)
            if not result:
                logging.info('get task error')
                time.sleep(20)
                continue
            for data in result:
                (dt, dep, to) = pubUtil.analysisData(data)

                # dep, to, dt = 'FUK', 'YNT', '2019-03-27'
                post_data = {
                    "tripType": "OW",
                    "orgCode": dep,
                    "dstCode": to,
                    "takeoffdate1": dt,
                }

                # 随机UA
                ua = UserAgent()
                self.headers['User-Agent'] = ua.random
                # post_data = urllib.urlencode(post_data)
                # logging.info("###input data: " + dep + to + dt)
                # 设置无效
                invalid = {
                    'date': dt.replace('-', ''),
                    'depAirport': dep,
                    'arrAirport': to,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                yield scrapy.Request(self.start_urls[0],
                                     headers=self.headers,
                                     body=json.dumps(post_data),
                                     # body=post_data,
                                     callback=self.parse,
                                     dont_filter=True,
                                     # meta={'invalid': invalid, 'proxy': 'http://127.0.0.1:8888'},
                                     meta={'invalid': invalid},
                                     method='POST',
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
        # print 'response', response.text.encode('utf-8')
        try:
            json_dict = json.loads(response.text.encode('utf-8'))
        except:
            logging.info('# ip deny')
            self.isOK = False
            return

        # print json_dict
        # 登陆
        if not json_dict.get('commonRes').get('isOk'):
            error_code = json_dict.get('commonRes').get('code')

            if error_code == 'PipSHP0001':
                logging.info('# no flight' + json.dumps(response.meta.get('invalid')))
                self.task.append(response.meta.get('invalid'))
                return
            if error_code == 'PREVENT0001':
                logging.info('# need login')
                self.isOK = False
                # print r' ' + response.text.encode('utf-8')
                return

        flight_list = json_dict.get('goFlightInfo').get('flightInfo')
        self.isOK = True
        for flight in flight_list:

            # flight = flights.get('flight')[0]
            flight_info = flight.get('flightSegs')[0]
            # 中转
            is_change = flight_info.get('stopAirportsSize')
            if not is_change == 0:
                logging.info('# is change')
                continue

            flight_number = flight_info.get('flightNo')

            dep_port = flight.get('orgAirport').get('airportCode')
            arr_port = flight.get('dstAirport').get('airportCode')

            from_city = self.portCitys.get(dep_port, dep_port)
            to_city = self.portCitys.get(arr_port, arr_port)
            carrier = flight_number[:2]
            dt_stamp = time.mktime(time.strptime(flight.get('departTime'), '%Y-%m-%d %H:%M'))
            at_stamp = time.mktime(time.strptime(flight.get('arrivalTime'), '%Y-%m-%d %H:%M'))

            price_list = flight_info.get('brandSeg')[0].get('price')
            price_info = ''
            for price_str in price_list:
                price_type = price_str.get('psgType')
                if price_type == 'ADT':
                    price_info = price_str
                    break

            if price_info == '':
                logging.info('###### price error')

            net_fare = price_info.get('price')
            currency = price_info.get('currency')
            tax = 0
            cabin = flight_info.get('brandSeg')[0].get('cabinCode')
            price = net_fare

            seat_str = flight_info.get('brandSeg')[0].get('remaindNum')

            if seat_str == u'>10\u5f20':
                seat = 10
            else:
                seat = int(seat_str[2])

            item = SpidersHynItem()
            item.update(dict(
                f=flight_number,
                d=dt_stamp,
                a=at_stamp,
                fc=from_city,
                tc=to_city,
                c=currency,
                ap=price,
                at=tax,
                n=net_fare,
                m=seat,
                cb=cabin,
                cr=carrier,
                i=1,
                s='[]',
                g=time.time(),
                da=dep_port,
                aa=arr_port,
            ))

            # print item
            # print flight_info.get('brandSeg')[0].get('brandInfo').get('text')
            yield item
