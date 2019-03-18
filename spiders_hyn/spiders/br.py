# encoding=utf-8
# evaair,br
# by hyn
# 2019-02-28

import scrapy
import json, logging, random, re
from utils import dataUtil, pubUtil
import time, datetime, urllib, requests, traceback
from spiders_hyn.items import SpidersHynItem
from jsonpath import jsonpath
# from fake_useragent import UserAgent


class AqSpider(scrapy.Spider):
    name = 'br'
    allowed_domains = ['evaair.com']
    task = []
    isOK = True

    custom_settings = dict(

        DOWNLOADER_MIDDLEWARES={
            'spiders_hyn.middlewares.StatisticsItem': 400,
            'spiders_hyn.middlewares.Brmiddlewares': 300
        },
        DOWNLOAD_TIMEOUT=20,
        # LOG_LEVEL = 'DEBUG',
        PROXY_TRY_NUM=0,
        # COOKIES_ENABLED=False,
        INVALID_TIME=45,
        CONCURRENT_REQUESTS=1,

        ITEM_PIPELINES={
            'spiders_hyn.pipelines.SpidersHynPipelineTest': 300,
        }

    )

    # 初始化
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        super(cls, self).__init__(*args, **kwargs)
        self.start_urls = ['https://book.evaair.com/plnext/EVAOnlineDX/Override.action']
        self.ADT = 3
        self.version = 1.0

        # 通过机场获取城市
        self.portCitys = dataUtil.get_port_city()
        self.session_id = ''
        self.session_flag = True

        self.headers = {
            'host': "book.evaair.com",
            'origin': "https://booking.evaair.com",
            'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            # 'cookie': "_EVAlang=3; _EVAcookieaccept=Y; D_IID=7198D30D-7BBD-3DF6-825F-B9A8A2E33EE0; D_UID=23C10191-61C4-3CA8-9BC5-C5D35052983E; D_ZID=CE20E1D1-B040-39C1-ABA8-A02CD4FF539C; D_ZUID=586B31F7-C8CD-3A85-B4DA-B344F51A8200; D_HID=0C5A5C86-CDDE-3364-BA5F-C5D7DDEB0DF6; D_SID=104.233.233.98:HydOGsyu5q3U0qPWwvSWYahCS9zxyt4ScbSDCVW4MSI; PDEP=PVG; PARR=TPE; PSEG=oneway; PDATE=2019%2F03%2F28",
            'content-type': "application/x-www-form-urlencoded",
        }
        self.timeout = 5
        self.js_verify_flag = True
        self.image_verify_flag = False
        self.js_verify_url = 'https://book.evaair.com/iframe.html'
        self.url = ''

    # 开始请求
    def start_requests(self):
        permins = 0
        logging.info(pubUtil.heartbeat(self.host_name, self.name, self.num, permins, self.version))
        result_iter = None
        while True:
            if hasattr(self, 'local'):
                if not result_iter:
                    result_iter = pubUtil.get_task(self.name, days=1)
                result = next(result_iter)
            else:
                result = pubUtil.getUrl('aq', 1)
            if not result:
                logging.info('get task error')
                time.sleep(20)
                continue
            for data in result:
                # logging.info("###input data: " + data)
                (dt, dep, to) = pubUtil.analysisData(data)

                # dt,dep,to='2019-03-28','PVG','TPE'

                # ua = UserAgent()
                # self.headers['user-agent'] = ua.random
                post_data = 'B_LOCATION_1=' + dep + '&E_LOCATION_1=' + to + '&B_DATE_1=' + dt.replace('-',
                                                                                                      '') + '0000&B_ANY_TIME_1=True&EMBEDDED_TRANSACTION=FlexPricerAvailability&ARRANGE_BY=D&DISPLAY_TYPE=2&PRICING_TYPE=O&SO_SITE_MATRIX_CALENDAR=FALSE&SO_SITE_RUI_CAL_AVAI_NO_RECO=TRUE&SO_SITE_RUI_FP_AVAI_PRESEL=FALSE&COMMERCIAL_FARE_FAMILY_1=NEWECOOW&COMMERCIAL_FARE_FAMILY_2=NEWDELOW&COMMERCIAL_FARE_FAMILY_3=NEWBIZOW&SO_SITE_RUI_AX_CAL_ENABLED=TRUE&SO_SITE_CAL_CHANGE_WEEK=TRUE&SO_SITE_RUI_HIDE_MDF_SRC=FALSE&EXTERNAL_ID%236=OW&TRAVELLER_TYPE_1=ADT&TRIP_TYPE=O&TRIP_FLOW=YES&SO_SITE_EXPORT_CONFIRM=TRUE&SO_SITE_EXPORT_CONF_URL=https%3A%2F%2Fbooking.evaair.com%2Fexporttripplan%2Fwebservice.aspx&SO_SITE_THREEDS_USE=N&SO_SITE_BILLING_NOT_REQUIRED=Y&SO_SITE_BILL_ADD_OPTIONS=BILL_ADD_HIDDEN&SO_SITE_PREBOOK_CANCELLATION=TRUE&SO_GL=%3C%3Fxml+version%3D%221.0%22+encoding%3D%22iso-8859-1%22%3F%3E%0D%0A%3CSO_GL%3E%0D%0A%3CGLOBAL_LIST+mode%3D%22partial%22%3E%0D%0A%3CNAME%3ESL_AIR_MOP%3C%2FNAME%3E%0D%0A%3CLIST_ELEMENT%3E%0D%0A%3CCODE%3ECC%3C%2FCODE%3E%0D%0A%3CLIST_VALUE%3ECredit+Card%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EY%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3ECC%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3ECryptic%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3ECC%25T%25I%2F%25E%2F%25C%25F%2FN%25A%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%2F%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3ECC%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3CLIST_VALUE%3EN%3C%2FLIST_VALUE%3E%0D%0A%3C%2FLIST_ELEMENT%3E%0D%0A%3C%2FGLOBAL_LIST%3E%0D%0A%3C%2FSO_GL%3E&SO_SITE_FD_DISPLAY_MODE=1&SO_SITE_CURRENCY_FORMAT_JAVA=0&SO_SITE_ENABLE_SRV_POLICY=BAG%2CCOA&SO_SITE_ALLOW_SPEC_REQ_SERV=FALSE&SO_SITE_SD_TRUE_OP_CARRIER=TRUE&SO_SITE_BARCODE_ENABLE=TRUE&SO_SITE_ALLOW_CS_CODE_SHARE=FALSE&SO_SITE_USE_PAYMENT_ACTION=TRUE&EXTERNAL_ID=AIBS&EXTERNAL_ID%232=&EXTERNAL_ID%233=&EXTERNAL_ID%234=NEWECOOW&EXTERNAL_ID%235=&EXTERNAL_ID%2314=N&EXTERNAL_ID%2312=&EXTERNAL_ID%2313=zh_CN&EXTERNAL_ID%2399=C5WBKT102%23%23flyeva&DIRECT_LOGIN=NO&SO_SITE_RUI_MULTIDEV_ENABLED=TRUE&SO_SITE_RUI_TABLET_PG_LIST=ALL&SO_SITE_RUI_MOBILE_PG_LIST=ALL&SO_SITE_RUI_DISP_FF_TABLE=TRUE&SO_SITE_RUI_UPSLL_T_MDL=TRUE&SO_SITE_RUI_UPSLL_T_MDL_ATC=TRUE&SO_SITE_RUI_DPICKER_NATIVE=TABLET%2CMOBILE&MC_FORCE_DEVICE_TYPE=MOBILE&SO_SITE_RUI_MOBILE_FLOW=ALL&SO_SITE_RUI_TABLET_FLOW=ALL&SO_SITE_RUI_COLLAPSE_BOUND_T=TWO_STEPS&SO_SITE_RUI_UPSLL_HIDE_BTNS=FALSE&SO_SITE_OFFICE_ID=SHABR08AA&LANGUAGE=CN&SITE=CAWXCNEW'
                url_data = {"ENCT": "1",
                            "ENC": "990572D723A7BC83F77B4C6C03C696340674137066140FF11D721B8765E55FF8DC0562E080CE4BD1CD01272028CBBA89",
                            # 传入当前查询时间
                            "ENC_TIME": time.strftime("%Y%m%d%H%M%S", time.localtime())}

                # 设置无效
                invalid = {
                    'date': dt.replace('-', ''),
                    'depAirport': dep,
                    'arrAirport': to,
                    'mins': self.custom_settings.get('INVALID_TIME')
                }
                url_data = urllib.urlencode(url_data)
                self.url = self.start_urls[0] + '?' + url_data
                # print '# url: ', url
                # print '# url_data: ', url_data

                # ip = '127.0.0.1:8888'
                # ip = '127.0.0.1:1080'
                yield scrapy.Request(self.url,
                                     headers=self.headers,
                                     body=post_data,
                                     callback=self.parse,
                                     dont_filter=True,
                                     # meta={'invalid': invalid, 'proxy': ip},
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

        # 图形验证
        if response.status == 405:
            logging.info('# need image verify')
            self.image_verify_flag = True
            self.isOK = False
            return
        self.isOK = True
        # js验证
        if not response.body.find('automatically'):
            logging.info('# line:145 need js verify')
            self.js_verify_flag = True
            return

        response_data = response.body

        try:

            response_data = re.compile(r"""config : (.*), pageEngine""", flags=re.DOTALL).search(response_data).group(1)
        except:
            logging.info('# line:156 response data error')
            logging.info('# line:156 need js verify')
            self.js_verify_flag = True
            self.isOK = False
            return

        json_dict = json.loads(response_data.decode("utf8", "ignore"))

        try:
            valid_airline = jsonpath(json_dict, '$..siteConfiguration')[0]

            # js验证
            if not valid_airline:
                logging.info('# need js verify')
                self.js_verify_flag = True
                return

            json_dict = jsonpath(json_dict, '$..Availability')

            # 航线无效
            if not json_dict:
                # logging.info("no flight" + json.dumps(response.meta.get('invalid')))
                # print response.meta.get('invalid')
                self.task.append(response.meta.get('invalid'))
                return

            json_dict = json_dict[0]

        except:
            logging.info('# response data error')
            print traceback.print_exc()
            # self.js_verify_flag = True
            self.isOK = False
            return

        currency = json_dict.get('currencyBean').get('code')
        self.isOK = True
        flight_list = json_dict.get('proposedBounds')[0].get('proposedFlightsGroup')

        price_list = json_dict.get('recommendationList')

        for flights in flight_list:

            # 中转
            is_change = len(flights.get('segments'))
            if is_change > 1:
                logging.info('# is change' + json.dumps(response.meta.get('invalid')))
                continue

            flight = flights.get('segments')[0]
            carrier = flight.get('airline').get('code')
            flight_number = carrier + flight.get('flightNumber')

            dep_port = flight.get('beginLocation').get('locationCode')
            arr_port = flight.get('endLocation').get('locationCode')

            from_city = self.portCitys.get(dep_port, dep_port)
            to_city = self.portCitys.get(arr_port, arr_port)

            # "beginDate": "Mar 20, 2019 12:05:00 PM",
            dt_time = flight.get('beginDate')
            dt_stamp = time.mktime(time.strptime(dt_time, '%b %d, %Y %I:%M:%S %p'))
            at_time = flight.get('endDate')
            at_stamp = time.mktime(time.strptime(at_time, '%b %d, %Y %I:%M:%S %p'))

            flight_id = flight.get('id')

            price_info_list = []

            for price_json in price_list:

                seat_info = price_json.get('bounds')[0].get('flightGroupList')[0]

                # 寻找与价格对应的价格信息
                if flight_id == seat_info.get('flightId'):
                    price_info = price_json.get('recoAmount')
                    net_fare = price_info.get('amountWithoutTax')
                    tax = price_info.get('tax')
                    adult_price = net_fare + tax
                    seat = seat_info.get('numberOfSeatsLeft')
                    cabin = seat_info.get('rbd')

                    price_info_list.append([adult_price, net_fare, tax, seat, cabin])

                    # 找到对应元素移除，避免下次遍历
                    price_list.remove(price_json)

            # 寻找最低价
            # print '# 213 price info: ', price_info_list

            try:
                net_fare = price_info_list[0][1]
                tax = price_info_list[0][2]
                adult_price = net_fare + tax
                seat = price_info_list[0][3]
                cabin = price_info_list[0][4]
            except:
                print response.meta.get('invalid')
                logging.info('# price error')
                return

            item = SpidersHynItem()
            item.update(dict(
                f=flight_number,
                d=dt_stamp,
                a=at_stamp,
                fc=from_city,
                tc=to_city,
                c=currency,
                ap=adult_price,
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
            yield item
