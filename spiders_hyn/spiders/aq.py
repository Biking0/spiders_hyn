# encoding=utf-8
# 9air,aq
# by hyn
# 2019-02-11

import scrapy
import json, logging, random
from utils import dataUtil, pubUtil
import time, datetime, urllib, requests, traceback
from spiders_hyn.items import SpidersHynItem
from spiders_hyn import middlewares


class AqSpider(scrapy.Spider):
    name = 'aq'
    allowed_domains = ['9air.com']
    task = []
    isOK = True

    custom_settings = dict(

        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.AqGetProxy': 300
        },
        DOWNLOAD_TIMEOUT=5,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=3,
        # COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=5,

        # ITEM_PIPELINES={
        #     'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        # }

    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = ['http://www.9air.com/app/GetFlight']
        self.ADT = 3
        self.version = 2.0

        # 通过机场获取城市
        self.portCitys = dataUtil.get_port_city()
        self.session_id = ''
        self.session_flag = True
        self.session_url = 'http://www.9air.com/app/Login'
        self.info_url = "http://www.9air.com/app/ChangeFlt"
        self.seat_url = 'http://www.9air.com/app/GetOrder?orderid='
        self.session_data = {
            'op': 'lg',
            # 设备ID，重新登陆安卓端可获取
            'tck': ''
        }
        self.headers = {
            'android_version': '1.44',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Apache-HttpClient/UNAVAILABLE (java 1.4)',
            'Host': 'www.9air.com'
        }
        self.timeout = 5

        self.id_pool = [
            'A4FD4D17F0B6513BA4FD4D17F0B6513B0F01AC9B07E4EA18CCD0D90BAEF4076EC16A4AFE5B5FFD0C545F48C19EFEFD54A67C38DFC7165F61',
            'A4FD4D17F0B6513BA4FD4D17F0B6513B0F01AC9B07E4EA18CCD0D90BAEF4076EC7170EB068F5A7DDFEFBFF044B3C77B410C50AD1FDC6EC69',
            'A4FD4D17F0B6513BA4FD4D17F0B6513B0F01AC9B07E4EA18CCD0D90BAEF4076EC7170EB068F5A7DDF2BF7BD5087F7E44FA7BB8676BEFE96D',
            'A4FD4D17F0B6513BA4FD4D17F0B6513B0F01AC9B07E4EA18CCD0D90BAEF4076EC7170EB068F5A7DD72FD095C54E93C2105B8245E0DE6C37A',
            'A4FD4D17F0B6513BA4FD4D17F0B6513B0F01AC9B07E4EA18CCD0D90BAEF4076EC7170EB068F5A7DD5DE024C3ED7EDCC4ADE8F13194EF3C80',

        ]

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

            self.session_data['tck'] = random.choice(self.id_pool)
            for data in result:
                # logging.info("###input data: " + data)
                (dt, dep, to) = pubUtil.analysisData(data)

                # dt,dep,to='2019-02-28','CAN','RGN'
                post_data = {
                    'traveldate': dt,
                    'ori': dep,
                    'currency': 'CNY',
                    'dest': to
                }

                # 设置无效
                invalid = {
                    'date': dt.replace('-', ''),
                    'depAirport': dep,
                    'arrAirport': to,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }

                post_data = urllib.urlencode(post_data)

                yield scrapy.Request(self.start_urls[0],
                                     headers=self.headers,
                                     body=post_data,
                                     callback=self.parse,
                                     dont_filter=True,
                                     meta={'invalid': invalid},
                                     method='POST',
                                     errback=self.errback)

    def errback(self, failure):
        """
        异常捕获
        """
        # self.log(failure.value, 40)
        self.isOK = False
        return failure.request

    # 解析数据，遍历
    def parse(self, response):
        json_dict = json.loads(response.text)
        # IP被封
        if json_dict.get('errorcode') == '9990':
            logging.info('# ip deny')
            self.isOK = False
            time.sleep(2)
            return
        flight_list = json_dict.get('goflight')

        # 无航班
        if not flight_list:
            # logging.info("no flight" + json.dumps(response.meta.get('invalid')))
            # print response.meta.get('invalid')
            self.task.append(response.meta.get('invalid'))

            return

        currency = json_dict.get('cur')
        order_id = json_dict.get('orderid')
        # logging.info('# seat info: ' + self.session_id + '-' + order_id)
        ip_proxies = {"http": response.meta.get('proxy')}
        self.isOK = True
        for flights in flight_list:

            flight = flights.get('flight')[0]
            # 中转
            is_change = flight.get('stops')
            if not is_change == '0':
                logging.info('# is change')
                continue

            flight_number = flight.get('fltno')

            dep_port = flight.get('ori')
            arr_port = flight.get('dest')

            from_city = self.portCitys.get(dep_port, dep_port)
            to_city = self.portCitys.get(arr_port, arr_port)
            carrier = flight_number[:2]
            dt_time = flight.get('oritime')
            dt_date = flight.get('fltdate')
            dt_stamp = time.mktime(time.strptime('%s%s' % (dt_date, dt_time), '%Y%m%d%H:%M'))
            at_time = flight.get('desttime')
            at_stamp = time.mktime(time.strptime('%s%s' % (dt_date, at_time), '%Y%m%d%H:%M'))

            # 隔天
            if at_stamp < dt_stamp:
                at_stamp += + 24 * 3600

            net_fare = 0
            cabin_list = ['SAVER', 'SMART', 'PLUS']
            cabin_count = 0

            # 处理三种套餐价格
            for i in range(1, 4):
                price_str = flights.get('fare0' + str(i))
                if price_str != '0':
                    cabin_count = str(i)
                    net_fare = int(price_str)
                    break

            if net_fare == 0:
                logging.info('# price is 0')
                continue
            tax = int(flights.get('fare0' + cabin_count + 'cn')) + int(flights.get('fare0' + cabin_count + 'yq')) + int(
                flights.get('fare0' + cabin_count + 'tax'))

            querystring = {"gocode": "0" + cabin_count, "goflightno": flight_number, "orderid": order_id}

            # 获取座位数
            try:
                requests.get(self.info_url, proxies=ip_proxies, params=querystring, headers=self.headers,
                             timeout=self.timeout)
                res = requests.get(self.seat_url + order_id, proxies=ip_proxies, headers=self.headers,
                                   timeout=self.timeout)
                seat = int(json.loads(res.text).get('flights')[0].get('num'))

                # session失效
                if seat is None:
                    self.session_flag = True
                    return

            except:
                # print traceback.print_exc()
                logging.info('# get seat error')
                self.isOK = False
                return

            cabin = cabin_list[int(cabin_count) - 1]
            if tax == 0:
                print '## tax error', flights
            price = net_fare + tax

            info = {
                'session_id': self.session_id,
                'order_id': order_id,
                'go_code': '0' + cabin_count
            }

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
                info=json.dumps(info)
            ))

            # print item
            yield item
