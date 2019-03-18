# -*- coding: utf-8 -*-

# Scrapy settings for spiders_hyn project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'spiders_hyn'

SPIDER_MODULES = ['spiders_hyn.spiders']
NEWSPIDER_MODULE = 'spiders_hyn.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'spiders_hyn (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

RETRY_ENABLED = False

# close debug
LOG_LEVEL = 'INFO'

DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
HEARTBEAT_DURATION = 60 * 10

HTTPERROR_ALLOW_ALL = True
DOWNLOADER_MIDDLEWARES = {
    'spiders_hyn.middlewares.SpidersHynSpiderMiddleware': 400,
}
CLOSESPIDER_TIMEOUT = 60 * 60 * 2
DOWNLOAD_TIMEOUT = 30
ITEM_PIPELINES = {
    'spiders_hyn.pipelines.SpidersHynPipeline': 300,
}
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}
INVALID_TIME = 45
GET_URL_TIMEOUT = 30
LOG_LEVEL = 'INFO'
GET_PORT_CITY_URL = 'http://116.196.117.196/br/portcity?carrier=VY'
GET_TASK_URL = 'http://task.jiaoan100.com/buddha/gettask?'
PUSH_TASK_URL = 'http://task.jiaoan100.com/buddha/pushtask?'
HEARTBEAT_URL = 'http://task.jiaoan100.com/buddha/heartbeat?'

PUSH_DATA_URL = {  # url和对应的概率， 概率为 k/sum(PUSH_DATA_URL.values())
   'http://task.jiaoan100.com/br/newairline?': 3,
   'http://stock.jiaoan100.com/br/newairline?': 7,
}
LOG_URL = 'http://dx.jiaoan100.com/br/log?'
PUSH_DATA_NUM = 10
PUSH_DATA_URL_TEST = 'http://test.jiaoan100.com/br_test/newairline?'  # 测试
GET_PROXY_URL = 'http://dx.proxy.jiaoan100.com/proxy/getproxy?'
GET_FRALS_TEST = 'http://test.jiaoan100.com/br_test/frals?carrier='  # 获取测试库中的线路图
GET_FRALS = 'http://116.196.117.196/br/frals?carrier='

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)

COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'spiders_hyn.middlewares.SpidersHynSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'spiders_hyn.middlewares.SpidersHynDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'spiders_hyn.pipelines.SpidersHynPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
