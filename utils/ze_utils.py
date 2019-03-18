# encoding=utf-8
# eastarjet,ZE
# by hyn
# 2018-11-21

import json
import logging
import requests
import ze_post_data
from jsonpath import jsonpath

local_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Referer': 'https://www.eastarjet.com/newstar/PGWHC00001',
    'Cookie': ''
}
url = 'https://www.eastarjet.com/json/dataService'


def get_net_tax(ADT, temp_info, headers, flight_code):
    local_headers['Cookie'] = headers.get('Cookie')
    try:
        response = requests.post(url, headers=local_headers,
                                 data=json.dumps(ze_post_data.get_tax(temp_info, ADT, flight_code)))
    except Exception as e:
        print e
        logging.info('# network timeout')
        return
    try:
        adult_tax_list = jsonpath(json.loads(response.text), '$..serviceCharges')[0].get('items')
    except:
        logging.info('# get tax error, update session')
        return
    adult_tax = 0
    for tax_item in adult_tax_list[1:]:
        adult_tax = adult_tax + float(tax_item.get('amount'))

    return adult_tax


# ze从字典中获取税
def ze_get_tax(air_line, tax_dict, currency):
    # 字典中寻找该航线
    tax_cur = tax_dict.get(air_line)
    if tax_cur:
        # 并且货币对应
        if currency == tax_cur[1]:
            # logging.info('# find tax')
            return tax_cur[0]
        else:
            logging.info('# tax currency error' + air_line + currency)
            return -1
    else:
        return -1


def read_tax_json():
    f = open('utils/src/ze_tax_dict.json', 'r')
    tax_dict = json.load(f)
    f.close()
    return tax_dict


def update_tax_json(tax_dict):
    f = open('utils/src/ze_tax_dict.json', 'w')
    json.dump(tax_dict, f, indent=4, sort_keys=True)
    f.close()
    logging.info('# update tax dict')
