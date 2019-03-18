# encoding=utf-8
# Lion Air
# by hyn
# 2018-11-01

import scrapy
import json, logging, jsonpath, random, os, csv
from utils import dataUtil,pubUtil
import time, datetime
from spiders_hyn.items import SpidersHynItem

from datetime import datetime as datetime_module


class JtSpider(scrapy.Spider):
    name = 'jt'

    allowed_domains = ['lionair.co.id']

    task = []

    isOK = False

    custom_settings = dict(

        DEFAULT_REQUEST_HEADERS={
            'Content-Type': 'application/json; charset=UTF-8'
        },
        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.JTSpiderMiddlewareProxy': 300

        },
        DOWNLOAD_TIMEOUT=30,
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
        self.ADT = '3'
        self.version = 1.0

        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()
        # self.currency = 'ZAR'

        # 模拟参数
        self.dep = 'HLP'
        self.arr = 'BPN'
        self.date = ''

        self.proxy = True

    # 开始请求
    def start_requests(self):

        # # 服务器任务获取
        # per_min = 0
        # logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, per_min, self.version))
        # while True:
        #     result = pubUtil.getUrl('je', 1)
        #     if not result:
        #         logging.info('get task error')
        #         time.sleep(10)
        #         continue
        #     for data in result:
        #         # logging.info("###input data: " + data)
        #         (dt, dep, to) = pubUtil.analysisData(data)
        #         self.dep=dep
        #         self.arr=to
        #         dt_stamp = time.mktime(time.strptime(to, '%Y-%m-%d'))
        #
        #         # 日期末尾增加3个0
        #         self.date = "/Date(%s)/" % int(dt_stamp * 1000)

        # 本地获取任务
        input_file = open(os.path.join('utils/src', 'JT.csv'), 'rU')
        reader = csv.reader(input_file)
        data_list = list(reader)
        input_file.close()

        this_day = datetime_module.now() + datetime.timedelta(days=5)
        # #倒序输出
        data_list = data_list[::-1]
        # 打乱顺序
        # random.shuffle(data_list)
        days = 1
        for i in range(8, 30, days):
            _date = this_day + datetime.timedelta(days=i)
            _dt = _date.strftime('%Y-%m-%d')
            for data in data_list:
                if not data or not len(data):
                    continue

                print 'input data: ', data[0], data[1], _dt
                self.dep = data[0]
                self.arr = data[1]
                # 年月日，2018-11-11
                # dt_stamp = time.mktime(time.strptime(_dt, '%Y-%m-%d')) + 8 * 60 * 60
                dt_stamp = time.mktime(time.strptime(_dt, '%Y-%m-%d'))
                # 日期末尾增加3个0
                self.date = "/Date(%s)/" % int(dt_stamp * 1000)

                # 目标地址参数字典
                post_data = {
                    "sd": {
                        "Adults": self.ADT,
                        "AirlineCode": "",
                        "ArrivalCity": self.arr,
                        "ArrivalCityName": None,
                        "BookingClass": None,
                        "CabinClass": 0,
                        "ChildAge": [],
                        "Children": 0,
                        "CustomerId": 0,
                        "CustomerType": 0,
                        "CustomerUserId": 230,
                        "DepartureCity": self.dep,
                        "DepartureCityName": None,
                        "DepartureDate": self.date,
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
                }

                # 设置无效
                invalid = {
                    'date': self.date.replace('-', ''),
                    'depAirport': self.dep,
                    'arrAirport': self.arr,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                PayLoad = json.dumps(post_data)

                yield scrapy.Request(self.start_urls[0],
                                     body=PayLoad,
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
            logging.info('###no data')
            return
        # 当天无航班，设置无效
        data_list = json_dict.get('SearchAirlineFlightsResult')
        if data_list is None or len(data_list) == 0:
            logging.info("no flight")
            self.task.append(response.meta.get('invalid'))
            return

        for data in data_list:

            # 是否中转
            # if len(data.get('SegmentInformation')) > 0:
            #     logging.info("is change")
            #     continue
            if data.get('TotalNoStops') != 0:
                logging.info('is change')
                continue

            # 其他航司，设置无效,OD,ID
            carrier = data.get('MACode')
            if carrier != 'JT':
                logging.info("### other airline" + carrier)
                self.task.append(response.meta.get('invalid'))
                # return

            depTime = dataUtil.str_to_stamp(data.get('DepDate') + data.get('DepTime'))
            
            arrTime = dataUtil.str_to_stamp(data.get('ArrDate') + data.get('ArrTime'))
            depAirport = data.get('DepCity')
            arrAirport = data.get('ArrCity')
            flightNumber = data.get('MACode') + data.get('FlightNo')
            currency = data.get('Currency')
            segmentInfo = data.get('SegmentInformation')[0]
            cabin = segmentInfo.get('SegBookingClass')

            lowFlight = data.get('PromoFlight')
            if not lowFlight:  # 找出最低价
                lowFlight = data.get('EconomyFlight')
                if not lowFlight:
                    lowFlight = data.get('BusinessFlight')
                    if not lowFlight:
                        lowFlight = data.get('BusinessFlexiFlight')

            # segment['depTerminal'] = jsonpath(lowFlight, '$..TerminalCode')
            # segment['depTerminal']=''

            tax = jsonpath.jsonpath(lowFlight, '$..TaxPerPax')[0]
            netFare = jsonpath.jsonpath(lowFlight, '$..PricePerPax')[0]
            seats = jsonpath.jsonpath(lowFlight, '$..StrikeoutInfo')[0]

            # maxseats = self.ADT
            # segment['seats'] = maxseats

            item = SpidersHynItem()
            item['m'] = int(self.ADT)
            item['f'] = flightNumber
            item['d'] = depTime
            item['a'] = arrTime
            item['da'] = depAirport
            item['aa'] = arrAirport
            item['c'] = currency
            item['cb'] = cabin
            item['cr'] = carrier
            item['s'] = '[]'
            item['i'] = 1
            item['g'] = time.time()
            item['ap'] = netFare + tax
            item['at'] = float(tax)
            item['n'] = float(netFare)
            item['fc'] = self.port_city.get(depAirport, depAirport)
            item['tc'] = self.port_city.get(arrAirport, arrAirport)

            # # 测试数据
            # print ('item', item)
            # # 测试税价
            # print '--------------'
            # print 'tax: ', tax
            # print type(tax), tax

            yield item

    def get_task(self):
        # 本地获取任务
        inputFile = open(os.path.join('utils/src', 'JT.csv'), 'rU')
        reader = csv.reader(inputFile)
        datas = list(reader)
        inputFile.close()
        # thisday = time.strftime('%Y%m%d',time.localtime(time.time())) + datetime.timedelta(days=3)
        # thisday = str(int(time.strftime('%Y%m%d',time.localtime(time.time()))) + 3)

        thisday = datetime_module.now() + datetime.timedelta(days=5)
        # #倒序输出
        # datas = datas[::-1]
        # 打乱顺序
        random.shuffle(datas)
        days = 1
        for i in range(9, 30, days):
            _date = thisday + datetime.timedelta(days=i)
            _dt = _date.strftime('%Y-%m-%d')
            for data in datas:
                if not data or not len(data):
                    continue

                # print  'data: ',data
                yield (data[0], data[1], _dt)
                # (data[0], data[1], _dt)
