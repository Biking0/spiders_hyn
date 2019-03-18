# encoding=utf-8
# Israel Air,ly
# by hyn
# 2018-11-23

import scrapy
import json, logging, os, sys, csv, random
from utils import dataUtil, pubUtil, ly_post_data
from utils.ze_utils import read_tax_json, ze_get_tax
import time
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime, timedelta
import urllib


class LySpider(scrapy.Spider):
    name = 'ly'
    allowed_domains = ['elal.com']
    task = []

    custom_settings = dict(
        DEFAULT_REQUEST_HEADERS={
            'Origin': 'https://booking.elal.co.il',
            'User-Agent': 'ElalMobile/2.0(Android)Ewave/1.0(http://www.ewave.co.il)',
            'Referer': 'https://booking.elal.co.il/newBooking/urlDirector.do',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.LySpiderGetSession': 300,
        },
        # 处理连接超时
        DOWNLOAD_TIMEOUT=40,
        # 延迟1秒
        # DOWNLOAD_DELAY=1,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=8,
        COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=1,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }
    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = [
            'https://fly.elal.co.il/plnext/mobile4LY/MFlexPricerAvailabilityDispatcherPui.action;jsessionid=']
        self.ADT = 3
        self.version = 1.0

        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()

    def start_requests(self):
        permins = 0
        print(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        result_iter = None
        while True:
            if hasattr(self, 'local'):
                if not result_iter:
                    result_iter = pubUtil.get_task(self.name, days=30)
                result = next(result_iter)
            else:
                result = pubUtil.getUrl(self.name)
            if not result:
                time.sleep(6)
                continue

            for data in result:

                # 处理任务 [u'TLN-CFE:20181110:1']
                task_data_list = data.split(':')
                count = int(task_data_list[2])
                (dt, dep, arr) = pubUtil.analysisData(task_data_list[0] + ':' + task_data_list[1])
                _date = datetime.strptime(dt, '%Y-%m-%d')

                for i in range(count):
                    date = _date + timedelta(days=i)
                    date = date.strftime('%Y%m%d0000')

                    dep = self.port_city.get(dep, dep)
                    arr = self.port_city.get(arr, arr)

                    # logging.info('# input data: ' + dep + '' + arr + '' + date)

                    # 设置无效
                    invalid = {
                        'date': date.replace('-', ''),
                        'depAirport': dep,
                        'arrAirport': arr,
                        'mins': self.custom_settings.get('INVALID_TIME')
                    }

                    post_data = urllib.urlencode(ly_post_data.second_post_data(dep, arr, date, self.ADT))

                    yield scrapy.Request(self.start_urls[0],
                                         body=post_data,
                                         callback=self.parse,
                                         dont_filter=True,
                                         meta={'invalid': invalid},
                                         errback=self.errback,
                                         method='POST')

    def errback(self, failure):
        """
        异常捕获
        """
        self.log(failure.value, 40)
        return failure.request

    # 解析数据
    def parse(self, response):

        try:
            response_dict = json.loads(response.body)
        except:
            print response.text
            return

        no_flight = jsonpath(response_dict, '$..generatedJSonByPrice')
        if not no_flight:
            # logging.info('# no flight' + str(response.meta.get('invalid')))
            self.task.append(response.meta.get('invalid'))
            return

        flight_dict = json.loads(jsonpath(response_dict, '$..generatedJSonByPrice')[0])

        flight_list = jsonpath(flight_dict, '$..list_flight')

        for data in flight_list:
            # 中转
            flight_info_change = jsonpath(data, '$..list_segment')
            if len(flight_info_change) > 1:
                # logging.info('# is change ')
                continue

            flight_info = flight_info_change[0][0]

            carrier = flight_info.get('airline').get('code')
            flight_number = carrier + flight_info.get('flight_number')

            dep_time = time.mktime(
                time.strptime(flight_info.get('b_date_date') + flight_info.get('b_date_time'), '%Y%m%d%H%M'))
            arr_time = time.mktime(
                time.strptime(flight_info.get('e_date_date') + flight_info.get('e_date_time'), '%Y%m%d%H%M'))
            dep_airport = flight_info.get('b_location').get('location_code')
            arr_airport = flight_info.get('e_location').get('location_code')

            dep_city = self.port_city.get(dep_airport, dep_airport)
            arr_city = self.port_city.get(arr_airport, arr_airport)

            adult_tax = 0

            list_price = jsonpath(data, '$..list_price')[0][0]
            max_seats = int(list_price.get('lsaNbrSeat'))
            currency = list_price.get('currency_code')
            if max_seats < 1:
                adult_price = 0
                net_fare = 0

            else:
                adult_price = float(list_price.get('totalPrice')) / self.ADT
                net_fare = adult_price

            is_change = 1
            segments = '[]'
            cabin = list_price.get('rbdFlight')

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
                aa=arr_airport
            ))

            # print item
            # print flight_info.get('b_date_date') + flight_info.get('b_date_time')
            yield item

