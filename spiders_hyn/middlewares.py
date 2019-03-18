# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import time, json, requests
import logging, random, re
from spiders_hyn import settings
import urllib, requests
from jsonpath import jsonpath
from selenium import webdriver
from utils import ly_post_data
import traceback
from selenium import webdriver
from utils import pubUtil


class StatisticsItem(object):
    def __init__(self):
        self.interval = 0
        self.itemsprev = 0

    # 统计每分钟item
    def process_request(self, request, spider):
        run_time = time.time()
        if run_time - self.interval >= 60:
            self.interval = run_time
            items = spider.crawler.stats.get_value('item_scraped_count', 0)
            irate = items - self.itemsprev
            self.itemsprev = items
            spider.crawler.stats.set_value('permins', irate)

class Trmiddlewares(object):
    def __init__(self):
        self.proxy = ''
        self.proxyCount = 0
        self.backSelfCount = 0
        self.cooke_dict = {}
        self.cookies = ''

    def process_request(self, request, spider):

        try:
            self.get_proxy(spider)
            if hasattr(spider, 'proxy') and spider.proxy:
                self.get_proxy(spider)

            spider.isOK = False
            if spider.js_verify_flag:
                self.js_verify(spider)
            spider.js_verify_flag = False

            if spider.image_verify_flag:
                self.image_verify(spider)
            spider.image_verify_flag = False

            self.cookies = 'PDEP=PVG; PARR=TPE; PSEG=oneway; PDATE=2019%2F03%2F15; _EVAlang=3; _EVAcookieaccept=Y;' + ' D_IID=' + self.cooke_dict.get(
                'D_IID') + '; D_UID=' + self.cooke_dict.get('D_UID') + '; D_ZID=' + self.cooke_dict.get(
                'D_ZID') + '; D_SID=' + self.cooke_dict.get('D_SID') + '; D_ZUID=' + self.cooke_dict.get(
                'D_ZUID') + '; D_HID=' + self.cooke_dict.get('D_HID')

            request.headers['Cookie'] = self.cookies
            request.meta['proxy'] = 'https://' + self.proxy
        except:
            logging.info('# br middlewares error')
            # print traceback.print_exc()
            time.sleep(3)
            return

    def js_verify(self, spider):
        logging.info('# start js verify')
        try:
            chrome_options = webdriver.ChromeOptions()
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # chrome_options.add_experimental_option("prefs", prefs)
            # chrome_options.add_argument('--no-sandbox')
            # chrome_options.add_argument('--proxy-server=' + self.proxy)
            chrome_options.add_argument('--proxy-server=127.0.0.1:8080')
            # chrome_options.add_argument("--ignore-certificate-errors")
            # chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            # driver.set_window_position(0, 0)
            # driver.set_window_size(100, 100)
            # 70s超时处理
            # driver.set_page_load_timeout(100)
            # logging.info('try to get new cookie')
            # start_time = time.time()

            driver.delete_all_cookies()
            driver.get(spider.js_verify_url)

            time.sleep(5)

            # driver.find_elements_by_xpath('//a[contains(text(),\'手動加載\')]')[0].click()
            # time.sleep(5)
            # print driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore")
            # print type(driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore"))

            try:
                driver.find_elements_by_xpath('//a[contains(text(),\'do so manually\')]')[0].click()
                time.sleep(3)
            except:
                logging.info('# click en error')

            try:
                driver.find_elements_by_xpath('//a[contains(text(),\'手動加載\')]')[0].click()
                time.sleep(3)
            except:
                logging.info('# click cn error')

            # if not driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore").find(
            #         'do so manually'):
            #
            #     driver.find_elements_by_xpath('//a[contains(text(),\'do so manually\')]')[0].click()
            #     time.sleep(5)
            # else:
            #     driver.find_elements_by_xpath('//a[contains(text(),\'手動加載\')]')[0].click()
            #     time.sleep(5)

            cookies = driver.get_cookies()

            time.sleep(3)

            # 获取cookies
            for i in cookies:
                self.cooke_dict[i.get('name')] = i.get('value')

            driver.delete_all_cookies()
            driver.close()
            spider.js_verify_flag = False
        except Exception as e:
            print(traceback.print_exc())
            # print(e)
            logging.info('# js verify error')
            spider.js_verify_flag = False

    def image_verify(self, spider):
        logging.info('# start image verify')
        try:
            chrome_options = webdriver.ChromeOptions()
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # chrome_options.add_experimental_option("prefs", prefs)
            # chrome_options.add_argument('--no-sandbox')
            # chrome_options.add_argument('--proxy-server=' + self.proxy)
            chrome_options.add_argument('--proxy-server=127.0.0.1:8080')
            # chrome_options.add_argument("--ignore-certificate-errors")
            # chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            # driver.set_window_position(0, 0)
            # driver.set_window_size(100, 100)
            # 70s超时处理
            # driver.set_page_load_timeout(100)
            # logging.info('try to get new cookie')
            # start_time = time.time()

            driver.delete_all_cookies()

            # time.sleep(15)
            driver.get(spider.url)

            # to-do 检测到400已通过验证，关闭浏览器

            time.sleep(20)
            driver.find_elements_by_xpath('//div[@class=\'geetest_radar_tip\']')[0].click()
            time.sleep(5)
            driver.find_elements_by_xpath('//a[@class=\'geetest_voice\']')[0].click()

            time.sleep(5)
            # print '# 182: ', driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore")

            voice_url = re.compile(r"""<audio class="geetest_music" src="(.*)"></audio>""", flags=re.DOTALL).search(
                driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore")).group(1)

            res = requests.get(voice_url)
            f = open('utils/br_music/test.mp3', 'wb')
            f.write(res.content)
            time.sleep(10)
            f.close()
            input_data = pubUtil.voice_cover()
            time.sleep(10)
            driver.find_elements_by_xpath('//input[@class=\'geetest_input\']')[0].send_keys(input_data)
            time.sleep(5)
            driver.find_elements_by_xpath('//span[@class=\'geetest_submit\']')[0].click()

            time.sleep(5)
            driver.close()
            spider.image_verify_flag = False
        except:
            logging.info('# image verify error')
            print(traceback.print_exc())
            spider.image_verify_flag = False

    def get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        if spider.isOK:
            return self.proxy
        if self.proxyCount < num:
            self.proxyCount = self.proxyCount + 1
            # logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxyCount = 0
        if self.backSelfCount >= 10:
            # try 10 times and back to sel ip
            # logging.info('using self ip')
            self.backSelfCount = 0
            self.proxy = ''
            return self.proxy

        try:
            params = {'carrier': 'f3'}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text)
            # logging.info('Proxy Num: ' + str(len(li)))
            # logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.backSelfCount = self.backSelfCount + 1
        except:
            traceback.print_exc()
            # logging.info('get proxy error....')
        finally:
            return self.proxy


class Brmiddlewares(object):
    def __init__(self):
        self.proxy = ''
        self.proxyCount = 0
        self.backSelfCount = 0
        self.cooke_dict = {}
        self.cookies = ''

    def process_request(self, request, spider):

        try:
            self.get_proxy(spider)
            if hasattr(spider, 'proxy') and spider.proxy:
                self.get_proxy(spider)

            spider.isOK = False
            if spider.js_verify_flag:
                self.js_verify(spider)
            spider.js_verify_flag = False

            if spider.image_verify_flag:
                self.image_verify(spider)
            spider.image_verify_flag = False

            self.cookies = 'PDEP=PVG; PARR=TPE; PSEG=oneway; PDATE=2019%2F03%2F15; _EVAlang=3; _EVAcookieaccept=Y;' + ' D_IID=' + self.cooke_dict.get(
                'D_IID') + '; D_UID=' + self.cooke_dict.get('D_UID') + '; D_ZID=' + self.cooke_dict.get(
                'D_ZID') + '; D_SID=' + self.cooke_dict.get('D_SID') + '; D_ZUID=' + self.cooke_dict.get(
                'D_ZUID') + '; D_HID=' + self.cooke_dict.get('D_HID')

            request.headers['Cookie'] = self.cookies
            request.meta['proxy'] = 'https://' + self.proxy
        except:
            logging.info('# br middlewares error')
            # print traceback.print_exc()
            time.sleep(3)
            return

    def js_verify(self, spider):
        logging.info('# start js verify')
        try:
            chrome_options = webdriver.ChromeOptions()
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # chrome_options.add_experimental_option("prefs", prefs)
            # chrome_options.add_argument('--no-sandbox')
            # chrome_options.add_argument('--proxy-server=' + self.proxy)
            chrome_options.add_argument('--proxy-server=127.0.0.1:8080')
            # chrome_options.add_argument("--ignore-certificate-errors")
            # chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            # driver.set_window_position(0, 0)
            # driver.set_window_size(100, 100)
            # 70s超时处理
            # driver.set_page_load_timeout(100)
            # logging.info('try to get new cookie')
            # start_time = time.time()

            driver.delete_all_cookies()
            driver.get(spider.js_verify_url)

            time.sleep(5)

            # driver.find_elements_by_xpath('//a[contains(text(),\'手動加載\')]')[0].click()
            # time.sleep(5)
            # print driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore")
            # print type(driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore"))

            try:
                driver.find_elements_by_xpath('//a[contains(text(),\'do so manually\')]')[0].click()
                time.sleep(3)
            except:
                logging.info('# click en error')

            try:
                driver.find_elements_by_xpath('//a[contains(text(),\'手動加載\')]')[0].click()
                time.sleep(3)
            except:
                logging.info('# click cn error')

            # if not driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore").find(
            #         'do so manually'):
            #
            #     driver.find_elements_by_xpath('//a[contains(text(),\'do so manually\')]')[0].click()
            #     time.sleep(5)
            # else:
            #     driver.find_elements_by_xpath('//a[contains(text(),\'手動加載\')]')[0].click()
            #     time.sleep(5)

            cookies = driver.get_cookies()

            time.sleep(3)

            # 获取cookies
            for i in cookies:
                self.cooke_dict[i.get('name')] = i.get('value')

            driver.delete_all_cookies()
            driver.close()
            spider.js_verify_flag = False
        except Exception as e:
            print(traceback.print_exc())
            # print(e)
            logging.info('# js verify error')
            spider.js_verify_flag = False

    def image_verify(self, spider):
        logging.info('# start image verify')
        try:
            chrome_options = webdriver.ChromeOptions()
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # chrome_options.add_experimental_option("prefs", prefs)
            # chrome_options.add_argument('--no-sandbox')
            # chrome_options.add_argument('--proxy-server=' + self.proxy)
            chrome_options.add_argument('--proxy-server=127.0.0.1:8080')
            # chrome_options.add_argument("--ignore-certificate-errors")
            # chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            # driver.set_window_position(0, 0)
            # driver.set_window_size(100, 100)
            # 70s超时处理
            # driver.set_page_load_timeout(100)
            # logging.info('try to get new cookie')
            # start_time = time.time()

            driver.delete_all_cookies()

            # time.sleep(15)
            driver.get(spider.url)

            # to-do 检测到400已通过验证，关闭浏览器

            time.sleep(20)
            driver.find_elements_by_xpath('//div[@class=\'geetest_radar_tip\']')[0].click()
            time.sleep(5)
            driver.find_elements_by_xpath('//a[@class=\'geetest_voice\']')[0].click()

            time.sleep(5)
            # print '# 182: ', driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore")

            voice_url = re.compile(r"""<audio class="geetest_music" src="(.*)"></audio>""", flags=re.DOTALL).search(
                driver.page_source.encode('ascii', 'ignore').decode('ascii').decode("utf8", "ignore")).group(1)

            res = requests.get(voice_url)
            f = open('utils/br_music/test.mp3', 'wb')
            f.write(res.content)
            time.sleep(10)
            f.close()
            input_data = pubUtil.voice_cover()
            time.sleep(10)
            driver.find_elements_by_xpath('//input[@class=\'geetest_input\']')[0].send_keys(input_data)
            time.sleep(5)
            driver.find_elements_by_xpath('//span[@class=\'geetest_submit\']')[0].click()

            time.sleep(5)
            driver.close()
            spider.image_verify_flag = False
        except:
            logging.info('# image verify error')
            print(traceback.print_exc())
            spider.image_verify_flag = False

    def get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        if spider.isOK:
            return self.proxy
        if self.proxyCount < num:
            self.proxyCount = self.proxyCount + 1
            # logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxyCount = 0
        if self.backSelfCount >= 10:
            # try 10 times and back to sel ip
            # logging.info('using self ip')
            self.backSelfCount = 0
            self.proxy = ''
            return self.proxy

        try:
            params = {'carrier': 'f3'}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text)
            # logging.info('Proxy Num: ' + str(len(li)))
            # logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.backSelfCount = self.backSelfCount + 1
        except:
            traceback.print_exc()
            # logging.info('get proxy error....')
        finally:
            return self.proxy


class KnGetProxy(object):
    def __init__(self):
        self.proxy = ''
        self.proxyCount = 0
        self.backSelfCount = 0

    def process_request(self, request, spider):

        if hasattr(spider, 'proxy') and spider.proxy:
            self.get_proxy(spider)

        # self.proxy='110.74.209.202:34632'
        # print '#' * 46, self.proxy

        request.meta['proxy'] = 'http://' + self.proxy

    def get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        if spider.isOK:
            return self.proxy
        if self.proxyCount < num:
            self.proxyCount = self.proxyCount + 1
            # logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxyCount = 0
        if self.backSelfCount >= 10:
            # try 10 times and back to sel ip
            # logging.info('using self ip')
            self.backSelfCount = 0
            self.proxy = ''
            return self.proxy

        try:
            params = {'carrier': spider.name}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text)
            # logging.info('Proxy Num: ' + str(len(li)))
            # logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.backSelfCount = self.backSelfCount + 1
        except:
            traceback.print_exc()
            # logging.info('get proxy error....')
        finally:
            return self.proxy


class AqGetProxy(object):
    def __init__(self):
        self.proxy = ''
        self.proxyCount = 0
        self.backSelfCount = 0

    def process_request(self, request, spider):

        if hasattr(spider, 'proxy') and spider.proxy:
            self.get_proxy(spider)

        # self.proxy='110.74.209.202:34632'
        # print '#' * 46, self.proxy

        if spider.session_flag:
            self.get_sesison(spider)

        request.meta['proxy'] = 'http://' + self.proxy

    def get_sesison(self, spider):
        while True:
            try:
                # proxy = {'http': 'http://127.0.0.1:8888'}
                proxy = {'http': 'http://' + self.proxy}
                logging.info('# get session')
                response = requests.post(spider.session_url, proxies=proxy, headers=spider.headers,
                                         data=spider.session_data,
                                         timeout=spider.timeout)
                spider.session_id = requests.utils.dict_from_cookiejar(response.cookies).get('JSESSIONID')
                if spider.session_id is not None:
                    spider.isOK = True
                    spider.headers['Cookie'] = 'JSESSIONID=' + spider.session_id
                    print spider.session_id
                    spider.session_flag = False
                    break
                time.sleep(3)
                logging.info('# session is none')
                spider.isOK = False
                self.get_proxy(spider)
            except Exception as e:
                # print e
                # print traceback.print_exc()
                logging.info('# get session error')
                spider.isOK = False
                self.get_proxy(spider)
                time.sleep(2)
                continue

    def get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        if spider.isOK:
            return self.proxy
        if self.proxyCount < num:
            self.proxyCount = self.proxyCount + 1
            # logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxyCount = 0
        if self.backSelfCount >= 10:
            # try 10 times and back to sel ip
            # logging.info('using self ip')
            self.backSelfCount = 0
            self.proxy = ''
            return self.proxy

        try:
            params = {'carrier': spider.name}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text)
            # logging.info('Proxy Num: ' + str(len(li)))
            # logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.backSelfCount = self.backSelfCount + 1
        except:
            traceback.print_exc()
            # logging.info('get proxy error....')
        finally:
            return self.proxy


class NkSpiderGetsession(object):
    def __init__(self):
        self.get_session_url = "https://www.spirit.com/"
        self.cookies = ''
        self.token_str = ''
        self.proxy = ''
        self.proxy_count = 0

    def process_request(self, request, spider):

        # 是否更新cookies

        # if spider.proxy_flag:
        self.proxy = self.get_proxy(spider)
        self.proxy = 'ZLy5cF:XkzCmz@181.177.84.107:9852'
        # if spider.cookies_flag:
        self.cookies = self.get_cookies(spider)

        # if spider.token_flag:
        #     self.get_token(spider)
        #
        # if spider.proxy_flag:
        #     self.get_proxy(spider)
        print
        request.headers
        spider.proxy_flag = False

        print
        'cookies:', self.cookies
        request.headers['Cookie'] = self.cookies
        print
        self.proxy
        request.meta['proxy'] = self.proxy

        print
        'header: ', request.headers

    def get_cookies(self, spider):
        while True:

            # proxy = '195.235.200.147:3128'
            proxy = self.get_proxy(spider)
            ip_proxies = {"https": "https://" + proxy}
            # 获取session
            response = requests.get(self.get_session_url, proxies=ip_proxies, verify=False)
            if response.status_code == 403:
                continue
            self.cookies = json.dumps(requests.utils.dict_from_cookiejar(response.cookies))[1:-1].replace('\"',
                                                                                                          '').replace(
                ':', '=').replace(' ', '').replace(',', '; ')
            print
            'get cookies:', self.cookies
            spider.cookies_flag = False
            break

    def get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        # if spider.isOK:
        #     return self.proxy
        if self.proxy_count < num and self.proxy != '':
            self.proxy_count = self.proxy_count + 1
            logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxy_count = 0
        # if self.token_count >= 5:
        #     # try 10 times and back to sel ip
        #     logging.info('# update token')
        #     self.token_count = 0
        #     self.get_token(spider)
        #     return

        try:
            params = {'carrier': 'nk'}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT,
                                         verify=False).text)
            logging.info('Proxy Num: ' + str(len(li)))
            logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            # self.token_count = self.token_count + 1
        except:
            traceback.print_exc()
            logging.info('get proxy error....')
        finally:
            spider.proxy_flag = False
            return self.proxy or ''


class TrSpiderGetsession(object):
    def __init__(self):
        self.get_token_url = "https://prod.open.flyscoot.com/v1/identity/token"
        self.token_str = ''
        self.proxy = ''
        self.token_count = 0
        self.proxy_count = 0

    def process_request(self, request, spider):

        if spider.token_flag:
            self.get_token(spider)

        if spider.proxy_flag:
            self.get_proxy(spider)
        spider.token_flag = False
        request.headers['Authorization'] = 'Bearer ' + self.token_str
        request.meta['proxy'] = self.proxy

    def process_response(self, request, response, spider):
        try:
            json.loads(response.body)
        except Exception as e:
            # spider.log('ip was denied: %s' % e, 30)
            # spider.log(request.meta.get('proxy'), 30)
            # spider.token_flag = True
            print
            e
            spider.proxy_flag = True
            return request
        return response

    def get_token(self, spider):
        headers = {
            'User-Agent': 'OS=Android;OSVersion=6.0.1;AppVersion=2.0.2;DeviceModel=XiaomiMI4LTE;',
            'Accept-Language': 'zh_CN',
            'Host': 'prod.open.flyscoot.com',
            'Accept-Encoding': 'gzip',
            'Connection': 'keep-alive',
            'Accept': 'application/json'
        }
        while True:
            try:
                # if spider.proxy_flag:
                #     self.get_proxy(spider)
                self.get_proxy(spider)
                proxies = {
                    'http': 'http://%s' % self.proxy,
                    'https': 'https://%s' % self.proxy
                }

                response = requests.post(self.get_token_url, proxies=proxies, headers=headers, timeout=30)

                self.token_str = json.loads(response.text).get('content').get('accessToken')
                if self.token_str is None:
                    logging.info('# token is none,continue get')
                    time.sleep(3)
                    continue

                logging.info('# got a new token')
                break
            except Exception as e:
                logging.info('# get token error')
                logging.info(e)
                time.sleep(3)

    def get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        # if spider.isOK:
        #     return self.proxy
        if self.proxy_count < num and self.proxy != '':
            self.proxy_count = self.proxy_count + 1
            logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxy_count = 0
        if self.token_count >= 5:
            # try 10 times and back to sel ip
            logging.info('# update token')
            self.token_count = 0
            self.get_token(spider)
            return

        try:
            params = {'carrier': 'tr'}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT,
                                         verify=False).text)
            logging.info('Proxy Num: ' + str(len(li)))
            logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.token_count = self.token_count + 1
        except:
            traceback.print_exc()
            logging.info('get proxy error....')
        finally:
            spider.proxy_flag = False
            return self.proxy or ''


class W6SpiderGetSession(object):
    session_flag = True
    get_session_url = 'https://wizzair.com/'
    # 请求数据关键字段
    get_abck_url = 'https://wizzair.com/_bm/_data'
    get_cookies_url = 'https://wizzair.com/en-gb#/booking/select-flight/TIA/DTM/2018-12-20/null/1/0/0/0/null'

    def __init__(self):
        self.abck_list = []

    def process_request(self, request, spider):

        if spider.session_flag:
            self.get_session()
        spider.session_flag = False
        # spider.custom_settings['DEFAULT_REQUEST_HEADERS']['cookie'] = '_abck=' + self.abck_list[0]
        request.headers[
            'cookie'] = '_abck=' + self.abck_list[0]

    def get_session(self):

        driver1 = webdriver.Chrome(executable_path='D:\softInstall\chromedriver.exe')
        driver1.get(self.get_cookies_url)
        self.abck_list = []
        for i in range(9):
            driver1.find_element_by_tag_name('main').click()

            self.abck = driver1.get_cookie('_abck').get('value')

            if i != 0 and self.abck == self.abck_list[i - 1]:
                return
            print
            i, self.abck
            self.abck_list.append(self.abck)
        driver1.close()


class LySpiderGetSession(object):
    session_flag = True

    def __init__(self):
        self.get_session_url = "https://fly.elal.co.il/plnext/mobile4LY/Override.action"
        self.session_id = ''

    def process_request(self, request, spider):

        if self.session_flag:
            self.get_session(spider)
        self.session_flag = False

        url = request.url
        request.url.replace(request.url, url + self.session_id)
        request._set_url(request.url + self.session_id)

    def get_session(self, spider):

        while True:
            try:
                response = requests.post(self.get_session_url,
                                         data=ly_post_data.first_post_data('123', '123', '123', 3),
                                         headers=spider.custom_settings.get('DEFAULT_REQUEST_HEADERS'), timeout=30,
                                         verify=False
                                         )
                self.session_id = requests.utils.dict_from_cookiejar(
                    response.cookies).get('JSESSIONID')
                logging.info('# got a new session')
                break
            except Exception as e:
                logging.info('# get session error')
                logging.info(e)
                time.sleep(2)


class ZeSpiderGetsession(object):
    def __init__(self):
        self.get_session_url = "https://www.eastarjet.com/newstar/PGWHC00001"
        self.session_id = ''

    def process_request(self, request, spider):

        if spider.session_flag:
            self.get_session()

        request.headers[
            'Cookie'] = 'selected_country_code=CN; JSESSIONID=' + self.session_id
        spider.session_flag = False

    def get_session(self):
        while True:
            try:
                response = requests.get(self.get_session_url, timeout=30)
                self.session_id = requests.utils.dict_from_cookiejar(
                    response.cookies).get('JSESSIONID')
                logging.info('# got a new session')
                break
            except Exception as e:
                logging.info('# get session error')
                logging.info(e)
                time.sleep(2)


class JTSpiderMiddlewareProxy(object):
    def __init__(self):
        self.proxy = ''
        self.proxyCount = 0
        self.backSelfCount = 0

    def process_request(self, request, spider):
        if spider.proxy:
            request.meta['proxy'] = self._get_proxy(spider)

    def _get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        if spider.isOK:
            return self.proxy
        if self.proxyCount < num:
            self.proxyCount = self.proxyCount + 1
            logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxyCount = 0
        if self.backSelfCount >= 10:
            # try 10 times and back to sel ip
            logging.info('using self ip')
            self.backSelfCount = 0
            self.proxy = ''
            return self.proxy

        try:
            params = {'carrier': spider.name}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text)
            logging.info('Proxy Num: ' + str(len(li)))
            logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.backSelfCount = self.backSelfCount + 1
        except:
            # traceback.print_exc()
            logging.info('get proxy error....')
        finally:
            return self.proxy or ''


class A5SpiderMiddlewareProxy(object):
    def __init__(self):
        self.proxy = ''
        self.proxyCount = 0
        self.backSelfCount = 0

    def process_request(self, request, spider):
        if spider.proxy:
            request.meta['proxy'] = self._get_proxy(spider)

    def process_response(self, request, response, spider):
        try:
            json.loads(response.body)
        except Exception as e:
            # spider.log('ip was denied: %s' % e, 30)
            # spider.log(request.meta.get('proxy'), 30)
            spider.isOK = False
            return request
        spider.isOK = True
        return response

    def _get_proxy(self, spider):
        num = spider.custom_settings.get('PROXY_TRY_NUM', 10)
        if spider.isOK:
            self.proxyCount = 0
            return self.proxy
        if self.proxyCount < num:
            self.proxyCount = self.proxyCount + 1
            logging.info('using old proxy:' + self.proxy)
            return self.proxy

        self.proxyCount = 0
        if self.backSelfCount >= 100:
            # try 10 times and back to sel ip
            logging.info('using self ip')
            self.backSelfCount = 0
            self.proxy = ''
            return self.proxy

        try:
            params = {'carrier': spider.name}
            li = json.loads(requests.get(settings.GET_PROXY_URL, params=params, timeout=settings.GET_URL_TIMEOUT).text)
            logging.info('Proxy Num: ' + str(len(li)))
            logging.info(str(li))
            self.proxy = random.choice(li).decode('ascii') or ''
            self.backSelfCount = self.backSelfCount + 1
        except:
            # traceback.print_exc()
            logging.info('get proxy error....')
        finally:
            return self.proxy or ''


class BYSpidersHynSpiderMiddlewareGetCookies(object):

    def __init__(self):
        self.first_url = "https://www.tui.co.uk/flight/search?"

        # 模拟参数
        self.dep = ''
        self.arr = ''
        self.date = ''

        # self.cookies = self.getCookies()

    def process_request(self, request, spider):

        self.dep = spider.dep
        self.arr = spider.arr
        self.date = spider.date
        self.ADT = spider.ADT
        # print ('process_request', request)

        if spider.flag:
            cookies = self.getCookies()
            # print type(cookies)
            request.cookies = requests.utils.dict_from_cookiejar(cookies)
            spider.flag = False

    def getCookies(self):

        first_data = {
            'flyingFrom[]': self.dep,
            'flyingTo[]': self.arr,
            'depDate': self.date,
            'returnDate': '',
            'adults': self.ADT,
            'children': '0',
            'infants': '0',
            'infantAge': '',
            'isOneWay': 'true',
            'childAge': '',
            'searchType': 'pricegrid',
            'isFlexible': 'Y'
        }

        first_url = '%s%s' % (self.first_url, urllib.urlencode(first_data))
        # print ('first_url',first_url)
        # second_url = '%s%s' % (self.second_url[0], urllib.urlencode(second_data))

        index_url = 'https://www.tui.co.uk/flight/'

        try:
            cookies = requests.get(first_url).cookies
            # print ('type cookies',cookies)
            logging.info("###update cookies")
        except:
            logging.info("###first request error")

        return cookies


class SpidersHynSpiderMiddleware(object):

    def __init__(self):
        self.interval = 0
        self.itemsprev = 0

    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SpidersHynDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    # 统计每分钟item
    def process_request(self, request, spider):
        run_time = time.time()
        if run_time - self.interval >= 60:
            self.interval = run_time
            items = spider.crawler.stats.get_value('item_scraped_count', 0)
            irate = items - self.itemsprev
            self.itemsprev = items
            spider.crawler.stats.set_value('permins', irate)
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
