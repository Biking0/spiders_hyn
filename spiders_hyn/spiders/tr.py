# encoding=utf-8
# flyscoot,TR
# by hyn
# 2018-12-22

import scrapy
import json, logging
from utils import dataUtil, pubUtil, ze_post_data
from utils.ze_utils import read_tax_json, ze_get_tax, get_net_tax, update_tax_json
import time
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime, timedelta


# 传入机场
class TrSpider(scrapy.Spider):
    name = 'tr'
    allowed_domains = ['flyscoot.com']
    task = []
    isOK = True

    custom_settings = dict(

        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.TrSpiderGetsession': 300
        },
        DEFAULT_REQUEST_HEADERS={
            'User-Agent': 'OS=Android;OSVersion=6.0.1;AppVersion=2.0.2;DeviceModel=XiaomiMI4LTE;',
            'Accept-Language': 'zh_CN',
            'Authorization': '',
            'Content-Type': 'application/json;charset=UTF-8',
            'Host': 'prod.open.flyscoot.com',
            'Accept-Encoding': 'gzip',
            'Connection': 'keep-alive'
        },
        DOWNLOAD_TIMEOUT=30,
        PROXY_TRY_NUM=2,
        COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=2,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }
    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = ['https://prod.open.flyscoot.com/v1/experience/query/search']
        self.ADT = 1
        self.version = 1.5
        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()
        self.token_flag = True
        self.proxy_flag = False

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
                time.sleep(5)
                continue
            for data in result:

                # logging.info("## input data: " + data)
                # 处理任务 [u'TLN-CFE:20181110:1']
                count = int(data.split(':')[-1])
                (date, dep, arr) = pubUtil.analysisData(data[:-2])
                _date = datetime.strptime(date, '%Y-%m-%d')
                for i in range(count):
                    temp_date = _date + timedelta(days=i)
                    date = temp_date.strftime('%Y-%m-%d')

                    # logging.info('# input data: ' + dep + '-' + arr + '-' + date)
                    # dep, arr, date = 'MNL', 'SIN', '2019-01-04'
                    post_data = {
                        "originIata": dep,
                        "destinationIata": arr,
                        "departureDate": date + "T00:00:00+08:00",
                        "passengerComposition": {
                            "adult": self.ADT,
                            "children": 0,
                            "infant": 0
                        }
                    }
                    body = json.dumps(post_data)

                    # 设置无效
                    invalid = {
                        'date': date[:10].replace('-', ''),
                        'depAirport': dep,
                        'arrAirport': arr,
                        'mins': self.custom_settings.get('INVALID_TIME')
                    }
                    task_data = {
                        'dep': dep,
                        'arr': arr,
                        'date': date,
                        'body': body
                    }
                    yield scrapy.Request(url=self.start_urls[0],
                                         body=body,
                                         callback=self.parse,
                                         dont_filter=True,
                                         meta={'invalid': invalid, 'task_data': task_data},
                                         errback=self.errback,
                                         method='POST')

    def errback(self, failure):
        """
        异常捕获
        """
        self.log(failure.value, 40)
        # print '# errback'
        # self.token_flag = True
        self.proxy_flag = True
        return failure.request

    # 解析数据
    def parse(self, response):

        data_dict = json.loads(response.body)
        try:
            flight_list = jsonpath(data_dict, '$..departures')[0]
        except:
            # self.token_flag = True
            logging.info('# invalid airport')
            print '# flight_list ', response.text
            return

        self.proxy_flag = False
        datas = response.meta.get('invalid')
        if len(flight_list) == 0:
            datas = response.meta.get('invalid')
            logging.info('# no flight: ' + datas.get('depAirport') + datas.get('arrAirport') + datas.get('date'))
            self.task.append(response.meta.get('invalid'))

        for data in flight_list:

            # 中转
            if len(data.get('legs')) > 1:
                logging.info('is change')
                continue
            flight_info = data.get('legs')[0]
            flight_number = str(flight_info.get('flightNumber')).replace(' ', '')
            carrier = flight_number[0:2]

            if carrier != 'TR':
                print '# other airline'
                continue

            # 2018-12-31T00: 55: 00
            dep_time = time.mktime(time.strptime(flight_info.get('departureDateTime'), '%Y-%m-%dT%H:%M:%S'))
            arr_time = time.mktime(time.strptime(flight_info.get('arrivalDateTime'), '%Y-%m-%dT%H:%M:%S'))
            dep_airport = flight_info.get('departure')
            arr_airport = flight_info.get('arrival')

            price_info_list = data.get('fareClasses')
            price_info = price_info_list[0]

            try:
                adult_price = float(price_info.get('price').get('amount'))
            except:
                print '### price error: ' + datas.get('depAirport') + datas.get('arrAirport') + datas.get('date')
                continue

            currency = price_info.get('price').get('currency')
            net_fare = adult_price
            cabin = price_info.get('productCode')
            max_seats = int(data.get('journeyInfo').get('seatLeft'))
            adult_tax = 0
            is_change = 1

            segments_data = ''
            for i in price_info_list:
                if i.get('name') == 'FlyBag':
                    segments_data = i
                    break
            segments = []
            try:
                if segments_data != '':
                    segments.append([segments_data.get('price').get('amount'), max_seats])
                else:
                    segments = [[0, 0]]
            except:
                print '### segments price error: ' + datas.get('depAirport') + datas.get('arrAirport') + datas.get(
                    'date')
                continue

            item = SpidersHynItem()
            item.update(dict(
                f=flight_number,
                d=dep_time,
                a=arr_time,
                fc=self.port_city.get(dep_airport, dep_airport),
                tc=self.port_city.get(arr_airport, arr_airport),
                c=currency,
                ap=adult_price,
                at=adult_tax,
                n=net_fare,
                m=max_seats,
                cb=cabin,
                cr=carrier,
                i=is_change,
                s=json.dumps(segments),
                g=time.time(),
                da=dep_airport,
                aa=arr_airport
            ))

            yield item
