# encoding=utf-8
# wizzair,w6
# by hyn
# 2018-11-28

import scrapy
import json, logging
from utils import dataUtil, pubUtil
import time, random
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime, timedelta


class W6Spider(scrapy.Spider):
    name = 'w6'
    start_urls = ['https://be.wizzair.com/9.1.0/Api/search/search']
    carrier = 'W6'
    task = []
    version = 1.9
    isOK = True
    ADT = 3
    session_flag = True

    custom_settings = dict(

        DEFAULT_REQUEST_HEADERS={
            'accept': "application/json, text/plain, */*",
            'origin': "https://wizzair.com",
            'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
            'content-type': "application/json;charset=UTF-8",
            'referer': "https://wizzair.com/en-gb",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9",
            'cookie': '',
            'cache-control': "no-cache",
            'postman-token': "55999a7b-9f88-8c8d-1a7a-6750c32175bd"
        },

        POST_DATA={
            "isFlightChange": False,
            "isSeniorOrStudent": False,
            "flightList": [{
                "departureStation": '',
                "arrivalStation": '',
                "departureDate": ''
            }],
            "adultCount": ADT,
            "childCount": 0,
            "infantCount": 0,
            "wdc": True
        },

        CONCURRENT_REQUESTS=1,
        DOWNLOAD_TIMEOUT=30,
        CLOSESPIDER_TIMEOUT=60 * 60 * 2,
        COOKIES_ENABLED=False,
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.W6SpiderGetSession': 300
        },
        ITEM_PIPELINES={
            'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        }
    )

    def __init__(self, *args, **kwargs):
        super(W6Spider, self).__init__(*args, **kwargs)

        # 通过机场获取城市
        # self.port_city = dataUtil.get_port_city()

    def start_requests(self):
        permins = 0
        # print(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        while True:
            # CRL-OTP:20181203:30
            # result = pubUtil.getUrl(self.name, 1)
            result = ["CRL-OTP:20181220:30"]
            if not result:
                logging.info('get task error')
                time.sleep(10)
                continue
            for data in result:
                (dt, dep, to) = pubUtil.analysisData(data)  # 把获取到的data格式化
                # (dt, dep, to, days) = ('20181026', 'LTN', 'IAS', 30)
                dt_datetime = datetime.strptime(dt, '%Y-%m-%d')
                # end_date = dt_datetime + timedelta(days=int(days))
                dt = dt_datetime.strftime('%Y-%m-%d')

                # dep = 'AES'
                # to = 'GDN'
                # dt = '2018-12-20'
                logging.info('# input data: ' + dep + '-' + to + '-' + dt)
                data_post = dict(
                    DepartureDate=dt,
                    DepartureStation=dep,
                    ArrivalStation=to,
                )

                # 设置无效
                invalid = {
                    'date': dt.replace('-', ''),
                    'depAirport': dep,
                    'arrAirport': to,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                self.custom_settings['POST_DATA']['flightList'] = [data_post]
                pay_load = json.dumps(self.custom_settings.get('POST_DATA'))
                yield scrapy.Request(method='POST',
                                     url=self.start_urls[0],
                                     body=pay_load,
                                     dont_filter=True,
                                     callback=self.parse,
                                     meta={'invalid': invalid, 'pay_load': pay_load},
                                     errback=self.errback,
                                     )

    def errback(self, failure):
        """
        异常捕获
        """
        print '6' * 66
        self.log(failure.value, 40)
        self.session_flag = True
        return failure.request

    def parse(self, response):
        print('parse', response.body)

        try:
            data_dict = json.loads(response.text)
        except:
            self.session_flag = True
            logging.info('parse request error')
            yield scrapy.Request(method='POST',
                                 url=self.start_urls[0],
                                 body=response.meta.get('pay_load'),
                                 meta=response.meta,
                                 dont_filter=True,
                                 callback=self.parse)
            return

        flight_list = data_dict.get('outboundFlights')
        currency = data_dict.get('currencyCode')
        for data in flight_list:

            dep_airport = data.get('departureStation')
            arr_airport = data.get('arrivalStation')
            carrier = data.get('carrierCode')
            flight_number = carrier + data.get('flightNumber')
            dep_time = time.mktime(time.strptime(data.get('departureDateTime'), '%Y-%m-%dT%H:%M:%S'))
            arr_time = time.mktime(time.strptime(data.get('arrivalDateTime'), '%Y-%m-%dT%H:%M:%S'))
            fares = jsonpath(data, '$..fares')[0]

            adult_price = 0.0
            adult_tax = 0.0
            net_fare = 0.0
            max_seats = 0.0
            for fare in fares:
                if fare.get('wdc') is True:  # 排除掉wizz club的价格，注释掉即是会员折扣价
                    continue

                if adult_price != 0 and adult_price < fare.get('fullBasePrice').get('amount'):
                    continue

                net_fare = fare.get('discountedFarePrice').get('amount')
                adult_tax = fare.get('administrationFeePrice').get('amount')
                adult_price = net_fare + adult_tax
                max_seats = fare.get('availableCount')

            cabin = 'X'
            is_change = 1
            segments = '[]'

            item = SpidersHynItem()
            item.update(dict(
                f=flight_number,
                d=dep_time,
                a=arr_time,
                # fc=self.port_city.get(dep_airport, dep_airport),
                # tc=self.port_city.get(arr_airport, arr_airport),
                fc='SHA',
                tc='BJK',
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

            print item
            yield item
