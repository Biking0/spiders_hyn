# encoding=utf-8
# eastarjet,ZE
# by hyn
# 2018-11-16

import scrapy
import json, logging
from utils import dataUtil, pubUtil, ze_post_data
from utils.ze_utils import read_tax_json, ze_get_tax, get_net_tax, update_tax_json
import time
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime, timedelta


# 传入机场
class ZeSpider(scrapy.Spider):
    name = 'ze'
    allowed_domains = ['eastarjet.com']
    task = []
    isOK = True

    custom_settings = dict(

        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.ZeSpiderGetsession': 300
        },
        # 处理连接超时
        DOWNLOAD_TIMEOUT=40,
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
        self.start_urls = ['https://www.eastarjet.com/json/dataService']
        self.ADT = 4
        self.version = 1.8

        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()

        # 国家-城市，切换货币单位
        self.city_dict = {'HKG': 'CN', 'PVG': 'CN', 'SHE': 'CN', 'YNJ': 'CN', 'CTS': 'JP',
                          'FUK': 'JP', 'IBR': 'JP', 'KIX': 'JP', 'KMI': 'JP', 'KOJ': 'JP',
                          'NRT': 'JP', 'OKA': 'JP', 'CJJ': 'KR', 'CJU': 'KR', 'GMP': 'KR',
                          'ICN': 'KR', 'KUV': 'KR', 'PUS': 'KR', 'BKI': 'MY', 'VVO': 'RU',
                          'PPS': 'SE', 'BKK': 'TH', 'TPE': 'TW', 'TSA': 'TW', 'DAD': 'VN',
                          'HAN': 'VN',
                          }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Referer': 'https://www.eastarjet.com/newstar/PGWHC00001',
            'Cookie': ''
        }

        self.session_flag = True
        self.tax_dict = read_tax_json()

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
                    _date = _date + timedelta(days=i)
                    date = _date.strftime('%Y%m%d')
                    # dep = 'KIX'
                    # arr = 'ICN'
                    # logging.info('# input data: ' + dep + '-' + arr + '-' + date)
                    city_code = self.city_dict.get(dep)
                    if city_code is None:
                        logging.info('# not found city: ' + dep)
                    body = json.dumps(ze_post_data.get_data(dep, arr, date, self.ADT, city_code))

                    # 设置无效
                    invalid = {
                        'date': date.replace('-', ''),
                        'depAirport': dep,
                        'arrAirport': arr,
                        'mins': self.custom_settings.get('INVALID_TIME')
                    }
                    task_data = {
                        'dep': dep,
                        'arr': arr,
                        'date': date,
                        'city_code': city_code,
                        'body': body
                    }

                    yield scrapy.Request(self.start_urls[0],
                                         headers=self.headers,
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
        return failure.request

    # 解析数据
    def parse(self, response):
        data_dict = json.loads(response.body)

        flight_list = jsonpath(data_dict, '$..trips')[0][0]

        task_data = response.meta.get('task_data')
        # 无航班
        if len(flight_list) == 0:
            # logging.info('# no flight: ' + task_data.get('dep') + task_data.get('arr') + task_data.get('date'))
            self.task.append(response.meta.get('invalid'))
            return

        # 货币单位
        currency = jsonpath(data_dict, '$..bookingCurrencyCode')[0]
        flight_key = jsonpath(data_dict, '$..flightSearchAuthKey')[0]

        temp_info = {
            'flight_key': flight_key,
            'fare_key': '',
        }
        dep_airport = flight_list[0].get('legs')[0].get('departureStation')
        arr_airport = flight_list[0].get('legs')[0].get('arrivalStation')
        # 航线
        air_line = dep_airport + arr_airport
        is_local = hasattr(self, 'local')
        for data in flight_list:
            # 中转
            if int(data.get('stops')) > 0:
                # logging.info('# is change: ' + task_data.get('dep') + task_data.get('arr') + task_data.get('date'))
                continue
            # 税相关参数
            carrier = data.get('carrierCode')
            flight_number = carrier + data.get('flightNumber')
            dep_time = time.mktime(time.strptime(data.get('standardTimeOfDeparture'), '%Y%m%d%H%M%S'))
            arr_time = time.mktime(time.strptime(data.get('standardTimeOfArrival'), '%Y%m%d%H%M%S'))
            dep_city = self.port_city.get(dep_airport, dep_airport)
            arr_city = self.port_city.get(arr_airport, arr_airport)
            max_seats = self.ADT

            # 获取税参数
            sell_key = data.get('sellKey')
            cabin = 'X'
            # 获取最低价
            if 'e_amount' in data:
                net_fare = float(data.get('e_amount'))
                temp_info['fare_key'] = data.get('e_sellKey') + '|' + sell_key
                cabin = data.get('e_classOfService')
                # logging.info('# test bargain : ' + task_data.get('dep') + task_data.get('arr') + task_data.get(
                #     'date') + ' ' + str(net_fare))
            elif 'd_amount' in data:
                net_fare = float(data.get('d_amount'))
                temp_info['fare_key'] = data.get('d_sellKey') + '|' + sell_key
                cabin = data.get('d_classOfService')
            elif 'y_amount' in data:
                net_fare = float(data.get('y_amount'))
                temp_info['fare_key'] = data.get('y_sellKey') + '|' + sell_key
                cabin = data.get('y_classOfService')
            else:
                net_fare = 0

            # 获取税，初始化情况下，并且有票
            if net_fare is not 0:
                # 线上先从本地中获取，线下都从网络中获取
                if not is_local:
                    # 只有初始化从字典中获取，最后从本地字典变量中获取
                    adult_tax = ze_get_tax(air_line, self.tax_dict, currency)
                else:
                    adult_tax = -1

                if adult_tax == -1:
                    # 获取税后更新字典
                    flight_code = jsonpath(data_dict, '$..flightCodeShare')[0]
                    headers = response.request.headers
                    logging.info('# airline not in tax dict: ' + air_line + task_data.get('date'))

                    # 网络中获取税
                    adult_tax = get_net_tax(self.ADT, temp_info, headers, flight_code)

                    # 网络获取税出错，重新请求这个任务
                    if adult_tax is None:
                        self.session_flag = True
                        yield scrapy.Request(self.start_urls[0],
                                             headers=self.headers,
                                             body=response.meta.get('task_data').get('body'),
                                             callback=self.parse,
                                             dont_filter=True,
                                             meta=response.meta,
                                             errback=self.errback,
                                             method='POST')

                        return

                    # 当本地local运行时更新字典，该条航线的税不存在时直接添加，存在时对比更新
                    else:
                        # 航线取最高税价，对比功能
                        self.log('got new tax : %s' % adult_tax, 20)
                        tax, cur = self.tax_dict.get(air_line) or [-1, '']
                        if currency == cur or tax == -1:
                            self.tax_dict.update({air_line: [adult_tax, currency]})
                            if is_local:
                                self.log('%s -> %s' % (tax, adult_tax), 20)
                                update_tax_json(self.tax_dict)
                        elif currency != cur:
                            print '%s->%s in %s' % (cur, currency, air_line)
                            logging.info('# currency error, local update ')

            if net_fare == 0:
                adult_price = 0
                adult_tax = 0
                max_seats = 0
            else:
                adult_price = net_fare + adult_tax

            is_change = 1
            segments = '[]'

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
                info=json.dumps(temp_info)
            ))

            # print item
            yield item
