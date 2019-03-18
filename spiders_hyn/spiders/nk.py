# encoding=utf-8
# spirit,NK
# by hyn
# 2018-12-29

import scrapy
import json, logging
from utils import dataUtil, pubUtil
import time
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
from datetime import datetime, timedelta
import urllib
import requests
from lxml import etree
from bs4 import BeautifulSoup


# 传入机场
class TrSpider(scrapy.Spider):
    name = 'nk'
    allowed_domains = ['spirit.com']
    task = []
    isOK = True

    custom_settings = dict(

        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            # 'spiders_hyn.middlewares.NkSpiderGetsession': 300
        },
        DEFAULT_REQUEST_HEADERS={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': ''
        },
        POST_DATA={
            'bypassHC': 'False',
            'bookingType': 'F',
            'carPickUpTime': '16',
            'carDropOffTime': '16',
            'tripTypeoneWay': '',
            'vacationPackageType': 'on',
            'tripType': 'oneWay',
            # 'from': '',
            # 'to': '',
            # 'departDate': '',
            # 'departDateDisplay': '01/24/2019',
            # 'returnDate': '02/24/2019',
            # 'returnDateDisplay': '02/24/2019',
            # 'ADT': '1',
            'CHD': '0',
            'INF': '0',
            'redeemMiles': 'false'},
        DOWNLOAD_TIMEOUT=30,
        DOWNLOAD_DELAY=1,
        PROXY_TRY_NUM=0,
        COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=8,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }
    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = ['https://www.spirit.com/Default.aspx?action=search']
        self.ADT = 4
        self.version = 1.2
        # 通过机场获取城市
        self.port_city = dataUtil.get_port_city()
        self.get_session_url = "https://www.spirit.com/"
        self.proxy = ''
        self.proxy_flag = True
        self.cookies_flag = True
        self.cookies_str = ''
        # self.use_time = 500

    def start_requests(self):
        permins = 0
        logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        result_iter = None
        # IP使用时长计时器
        # start_time = time.time()
        while True:
            if hasattr(self, 'local'):
                if not result_iter:
                    result_iter = pubUtil.get_task(self.name, days=10)
                result = next(result_iter)
            else:
                result = pubUtil.getUrl(self.name, 1)
            if not result:
                logging.info('get task error')
                time.sleep(20)
                continue
            for data in result:
                # logging.info("## input data: " + data)
                # 处理任务 [u'TLN-CFE:20181110:1']
                count = int(data.split(':')[-1])
                (date, dep, arr) = pubUtil.analysisData(data[:-2])
                _date = datetime.strptime(date, '%Y-%m-%d')

                for i in range(count):
                    temp_date = _date + timedelta(days=i)
                    date = temp_date.strftime('%m/%d/%Y')
                    invalid_date = temp_date.strftime('%Y%m%d')

                    # logging.info('# input data: ' + dep + '-' + arr + '-' + date)
                    # dep, arr, date = 'FLL', 'LAS', '2019-01-13'

                    # IP超过使用时长，强制更换
                    # logging.info('ip used time: ' + str(time.time() - start_time))
                    # if time.time() - start_time > self.use_time:
                    #     self.proxy_flag = True
                    #     logging.info('### ip invalid:' + self.proxy)
                    if self.proxy_flag:
                        while True:
                            # 俄罗斯代理
                            # self.proxy = pubUtil.nk_get_ip()
                            # 小池子代理
                            self.proxy = pubUtil.get_proxy(self.name)
                            if self.proxy is None:
                                logging.info('# no get proxy, continue')
                                # time.sleep(60)
                                continue
                            logging.info('# get a new ip: ' + self.proxy)
                            ip_proxies = {"https": "https://" + self.proxy}
                            # 获取session
                            try:
                                response = requests.get(self.get_session_url, proxies=ip_proxies, timeout=15)
                                self.cookies_str = json.dumps(requests.utils.dict_from_cookiejar(response.cookies))[
                                                   1:-1].replace(
                                    '\"',
                                    '').replace(
                                    ':', '=').replace(' ', '').replace(',', '; ')

                            except Exception as e:
                                logging.info(e)
                                self.proxy_flag = True
                                logging.info('# get session error')
                                continue
                            # IP正常使用，开始计时
                            # start_time = time.time()
                            self.proxy_flag = False

                            break
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Cookie': self.cookies_str
                    }

                    post_data = {
                        'from': dep,
                        'to': arr,
                        # 'from': 'AXM',
                        # 'to': 'ATL',
                        'departDate': date,
                        'departDateDisplay': date,
                        'ADT': self.ADT
                    }

                    post_data.update(self.custom_settings.get('POST_DATA'))
                    post_data = urllib.urlencode(post_data)

                    # 设置无效
                    invalid = {
                        'date': invalid_date,
                        'depAirport': dep,
                        'arrAirport': arr,
                        'mins': self.custom_settings.get('INVALID_TIME')
                    }
                    yield scrapy.Request(url=self.start_urls[0],
                                         body=post_data,
                                         headers=headers,
                                         callback=self.parse,
                                         dont_filter=True,
                                         meta={'invalid': invalid, 'proxy': self.proxy},
                                         errback=self.errback,
                                         method='POST')

    def errback(self, failure):
        """
        异常捕获
        """
        self.log(failure.value, 40)
        self.proxy_flag = True
        logging.info('# time out')
        time.sleep(30)
        return failure.request

    # 解析数据
    def parse(self, response):
        soup = BeautifulSoup(response.body, "lxml")
        soup.find_all()
        # 航班DIV列表
        result = soup.find('div', class_="sortThisTable")
        task_data = response.meta.get('invalid')
        try:
            flight_list = result.find_all('div', class_="row rowsMarket1")
            # 隔天航班
            next_days = result.find_all('div', class_="rowsMarket1 row govNext ")
        except:
            logging.info("# access denied")
            self.proxy_flag = True
            # time.sleep(3)
            access_str = str(response.body)
            if not 'access' in access_str:
                logging.info('# server error')
                time.sleep(120)

            # 先return处理，后续需要考虑cookies失效情况
            return
        if len(next_days) != 0:
            # logging.info('## next day flight')
            for next_day in next_days:
                flight_list.append(next_day)
        for data in flight_list:

            flight_number = data.find_all('div', class_="fi-header-text text-uppercase text-right")
            flight = data.find_all('input', class_="bfsFlightInfo")
            if len(flight) == 0:
                logging.info(
                    '# no flight: ' + task_data.get('depAirport') + task_data.get('arrAirport') + task_data.get('date'))
                self.task.append(response.meta.get('invalid'))
                continue

            flight_info_number = flight[0]['value'].replace('\n', '').replace('\t', '').replace('\'', '\"')
            flight_info = data.find_all('div', class_="standardFare radio")[0]('input')
            flight_info = flight_info[0]['value'].replace('\n', '').replace('\t', '').replace('\'', '\"').split('~~')[
                -2].split('~')

            # 中转
            if len(flight_number) > 1:
                logging.info(
                    '# is change: ' + task_data.get('depAirport') + task_data.get('arrAirport') + task_data.get('date'))
                continue

            # {u'std': u'2019-01-27T14:30:00.0000000-05:00', u'asc': u'ACY', u'cc': u'NK', u'dsc': u'FLL', u'fn': u'262'}
            flight_info_number = json.loads(flight_info_number[1:-1].replace(' ', ''))

            carrier = flight_info_number.get('cc')
            flight_number = carrier + flight_info_number.get('fn')
            # print time.strptime(flight_info[1], '%m/%d/%Y %H:%M')
            dep_time = time.mktime(time.strptime(flight_info[1], '%m/%d/%Y %H:%M'))
            arr_time = time.mktime(time.strptime(flight_info[3], '%m/%d/%Y %H:%M'))
            dep_airport = flight_info[0]
            arr_airport = flight_info[2]

            price_str = data('em')[-1].text
            net_fare = float(price_str[1:])

            if price_str[0] == '$':
                currency = 'USD'
            else:
                logging.info('# other currency')
                continue

            adult_tax = 0
            adult_price = net_fare
            segments = '[]'
            max_seats = self.ADT
            is_change = 1
            cabin = 'X'

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

            # print item
            yield item
