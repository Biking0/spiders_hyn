# encoding=utf-8
# lionairthai SL
# by hyn
# 2018-12-08

import scrapy
import json, logging
from utils import dataUtil, pubUtil
import time
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime
from datetime import datetime, timedelta


class JtSpider(scrapy.Spider):
    name = 'sl'

    allowed_domains = ['lionair.co.id']
    task = []
    isOK = False
    ADT = '3'

    custom_settings = dict(

        DEFAULT_REQUEST_HEADERS={
            'Content-Type': 'application/json; charset=UTF-8'
        },
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.JTSpiderMiddlewareProxy': 300

        },
        POST_DATA={
            "sd": {
                "Adults": ADT,
                "AirlineCode": "",
                "ArrivalCity": '',
                "ArrivalCityName": None,
                "BookingClass": None,
                "CabinClass": 0,
                "ChildAge": [],
                "Children": 0,
                "CustomerId": 0,
                "CustomerType": 0,
                "CustomerUserId": 230,
                "DepartureCity": '',
                "DepartureCityName": None,
                "DepartureDate": '',
                "DepartureDateGap": 0,
                "DirectFlightsOnly": False,
                "Infants": 0,
                "IsPackageUpsell": False,
                "JourneyType": 1,
                "PreferredCurrency": "IDR",
                "ReturnDate": "/Date(-2208988800000)/",
                "ReturnDateGap": 0,
                "SearchOption": 1
            },
            "fsc": "0"
        },

        DOWNLOAD_TIMEOUT=40,
        # LOG_LEVEL = 'DEBUG',
        # DOWNLOAD_DELAY=1,
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
        self.start_urls = [
            'https://mobile.lionair.co.id/GQWCF_FlightEngine/GQDPMobileBookingService.svc/SearchAirlineFlights']

        self.version = 1.0

        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()

        self.proxy = True

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
                time.sleep(10)
                continue
            for data in result:

                logging.info("# input data: " + data)
                # 处理任务 CTU-HKT:20181209:1
                count = int(data.split(':')[-1])
                (date, dep, arr) = pubUtil.analysisData(data[:-2])
                _date = datetime.strptime(date, '%Y-%m-%d')

                # 跑多天
                for i in range(count):
                    _date = _date + timedelta(days=i)
                    dt_stamp = time.mktime(time.strptime(_date.strftime('%Y%m%d'), '%Y%m%d'))
                    # 日期末尾增加3个0
                    date = "/Date(%s)/" % int(dt_stamp * 1000)

                    # 设置无效
                    invalid = {
                        'date': date.replace('-', ''),
                        'depAirport': dep,
                        'arrAirport': arr,
                        'mins': self.custom_settings.get('INVALID_TIME')
                    }

                    # 更新目标地址参数字典
                    self.custom_settings['POST_DATA']['sd']['DepartureCity'] = dep
                    self.custom_settings['POST_DATA']['sd']['ArrivalCity'] = arr
                    self.custom_settings['POST_DATA']['sd']['DepartureDate'] = date

                    pay_load = json.dumps(self.custom_settings.get('POST_DATA'))

                    yield scrapy.Request(self.start_urls[0],
                                         body=pay_load,
                                         callback=self.parse,
                                         dont_filter=True,
                                         meta={'invalid': invalid, 'proxy': ''},
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

        try:
            json_dict = json.loads(response.text)
        except:
            logging.info('# no data')
            return
        # 当天无航班，设置无效
        data_list = json_dict.get('SearchAirlineFlightsResult')
        if data_list is None or len(data_list) == 0:
            logging.info("# no flight")
            self.task.append(response.meta.get('invalid'))
            return

        for data in data_list:

            # 中转
            if data.get('TotalNoStops') != 0:
                logging.info('is change')
                continue

            # 其他航司，设置无效,OD,ID,IW
            carrier = data.get('MACode')
            if carrier != 'SL':
                logging.info("### other airline" + carrier)
                self.task.append(response.meta.get('invalid'))
                # return

            flight_number = carrier + data.get('FlightNo')
            dep_time = dataUtil.str_to_stamp(data.get('DepDate') + data.get('DepTime'))
            arr_time = dataUtil.str_to_stamp(data.get('ArrDate') + data.get('ArrTime'))
            dep_airport = data.get('DepCity')
            arr_airport = data.get('ArrCity')

            currency = data.get('Currency')
            segment_info = data.get('SegmentInformation')[0]
            cabin = segment_info.get('SegBookingClass')

            # 寻找最低价
            price_list = []
            result_price = {}
            cabin_list = ['PromoFlight', 'EconomyFlight', 'BusinessFlight', 'BusinessFlexiFlight']
            for i in cabin_list:
                low_flight = data.get(i)
                if low_flight:
                    price_list.append(low_flight)

            # 防止取不到价格
            if len(price_list) is 0:
                logging.info('# no price')

            for j in range(len(price_list)):
                if j is 0:
                    result_price = price_list[j]
                    continue
                temp_price = jsonpath(price_list[j], '$..PricePerPax')[0]
                if jsonpath(result_price, '$..PricePerPax')[0] > temp_price:
                    result_price = price_list[j]

            adult_tax = jsonpath(result_price, '$..TaxPerPax')[0]
            net_fare = jsonpath(result_price, '$..PricePerPax')[0]
            is_change = 1
            segments = '[]'

            item = SpidersHynItem()
            item.update(dict(
                f=flight_number,
                d=dep_time,
                a=arr_time,
                fc=self.port_city.get(dep_airport, dep_airport),
                tc=self.port_city.get(arr_airport, arr_airport),
                c=currency,
                ap=net_fare + adult_tax,
                at=adult_tax,
                n=net_fare,
                m=self.ADT,
                cb=cabin,
                cr=carrier,
                i=is_change,
                s=segments,
                g=time.time(),
                da=dep_airport,
                aa=arr_airport
            ))

            # print item
            yield item
