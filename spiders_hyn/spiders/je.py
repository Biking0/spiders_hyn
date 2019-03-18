# encoding=utf-8
# Mango Air
# by hyn
# 2018-10-23

import scrapy
import json, logging
from utils import dataUtil, pubUtil
import time, datetime
from spiders_hyn.items import SpidersHynItem
from spiders_hyn import middlewares


# 传入机场
class Je_Spider(scrapy.Spider):
    name = 'je'

    allowed_domains = ['flymango.com']

    task = []

    isOK = True

    custom_settings = dict(

        DEFAULT_REQUEST_HEADERS={
            'Content-Type': 'application/json; charset=UTF-8'
        },
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
        },
        DOWNLOAD_TIMEOUT=20,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=8,
        COOKIES_ENABLED=False,
        INVALID_TIME=45,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }

    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = ['https://www.flymango.com/api/availability/search']
        self.ADT = '3'
        self.version = 1.6

        # 通过机场获取城市
        self.portCitys = dataUtil.get_port_city()
        self.currency = 'ZAR'

    # 开始请求
    def start_requests(self):
        permins = 0
        logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        while True:
            result = pubUtil.getUrl('je', 1)
            if not result:
                logging.info('get task error')
                time.sleep(10)
                continue
            for data in result:
                # logging.info("###input data: " + data)
                (dt, dep, to) = pubUtil.analysisData(data)

                # 目标地址参数字典
                post_data = {
                    "AgencyCode": "",
                    "AirportFrom": dep,
                    "AirportTo": to,
                    "BoardDate": dt,
                    "CarPackage": 'false',
                    "ReturnDate": "",
                    "SearchType": "Normal",
                    "AvailType": "",
                    "IsReturnFlight": 'false',
                    "IsBusiness": 'false',
                    "Adults": self.ADT,
                    "Children": "0",
                    "Infants": "0",
                    "FareDesignator": "",
                    "EdgarsClubCard": "",
                    "VoyagerState": '0',
                    "HaveErrors": 'false',
                    "IsChangeBooking": 'false',
                    "MomentumClientNumber": "",
                    "OutSegmentKeyFromRedirect": "",
                    "InSegmentKeyFromRedirect": "",
                    "isMobile": 'false',
                    "CriteriaSearchType": "Day"
                }

                # 设置无效
                invalid = {
                    'date': dt.replace('-', ''),
                    'depAirport': dep,
                    'arrAirport': to,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                PayLoad = json.dumps(post_data)

                yield scrapy.Request(self.start_urls[0],
                                     body=PayLoad,
                                     callback=self.parse,
                                     dont_filter=True,
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
        json_dict = json.loads(response.text)

        # 当天无航班
        oa = json_dict.get('OutAvailability')
        if not oa or not len(oa):
            logging.info("no flight")
            self.task.append(response.meta.get('invalid'))
            return

        for data in oa:

            # 是否中转
            if len(data.get('Stops')) > 0:
                # logging.info("is change")
                continue

            dep_port = data.get('DepartureAirport')
            arr_port = data.get('ArrivalAirport')
            flight_number = data.get('FlightNumber')
            from_city = self.portCitys.get(dep_port, dep_port)
            to_city = self.portCitys.get(arr_port, arr_port)
            carrier = flight_number[:2]
            cabin = data.get('ClassCode')

            dt_time = data.get('DepartureTime')
            dt_date = data.get('DepartureDateText').split(' ')[0]
            dt_stamp = time.mktime(time.strptime('%s %s' % (dt_date, dt_time), '%m/%d/%Y %H:%M'))
            at_time = data.get('ArrivalTime')
            at_date = data.get('ArrivalDateText').split(' ')[0]
            at_stamp = time.mktime(time.strptime('%s %s' % (at_date, at_time), '%m/%d/%Y %H:%M'))

            seat = int(data.get('SeatCount'))
            if seat < int(self.ADT):
                seat = 0
                price = 0
                tax = 0
                net_fare = 0
                currency = ''
            else:
                price_str = data.get('Price')
                price = float(price_str[1:])
                tax = float(data.get('TaxValue')[1:])
                net_fare = float(data.get('FareValue')[1:])
                # 货币单位处理
                if price_str[0] != 'R':
                    self.log("currency error: %s->%s at %s Price: %s" % (dep_port, arr_port, dt_date, price_str), 30)
                    continue
                currency = self.currency

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

            yield item
