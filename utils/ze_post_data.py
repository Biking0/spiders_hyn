# encoding=utf-8
# eastarjet,ZE
# by hyn
# 2018-11-16

import json


def get_data(dep, arr, date, ADT, city_code):
    data = {"viewType": "B", "fly_type": "2", "person1": str(ADT), "person2": "0", "person3": "0",
            "residentCountry": city_code,
            "currency": "", "promotion_cd": "", "flySection": [
            {"departure_cd": dep, "departure_txt": "", "arrival_cd": arr,
             "arrival_txt": "", "departure_date_cd": date,
             "departure_date_txt": ""}]}

    post_data = {
        "id": 10,
        "method": "DataService.service",
        "params": [{
            "javaClass": "com.jein.framework.connectivity.parameter.RequestParameter",
            "requestUniqueCode": "PGWHC00001",
            "requestExecuteType": "BIZ",
            "DBTransaction": 'false',
            "sourceName": 'null',
            "sourceExtension": 'null',
            "functionName": "DTWBA00022",
            "panelId": 'null',
            "methodType": 'null',
            "inParameters": {
                "javaClass": "java.util.List",
                "list": [{
                    "javaClass": "com.jein.framework.connectivity.parameter.InParameter",
                    "paramName": "flightSearch",
                    "ioType": "IN",
                    "structureType": "FIELD",
                    "data": {
                        "javaClass": "java.util.List",
                        "list": [{
                            "map": {
                                "flightSearch": json.dumps(data)
                            },
                            "javaClass": "java.util.Map"
                        }]
                    }
                }]
            },
            "filterParameter": {
                "javaClass": "java.util.Map",
                "map": {}
            }
        }]
    }
    return post_data


def get_tax(temp_info, ADT, flight_code):
    data = {"viewType": "B", "person1": str(ADT), "person2": "0",
            "inFlightSearchAuthKey": temp_info.get('flight_key'),
            "happySellKey": "",
            "happyInternational": flight_code, "cancelSellKeyList": [],
            "selectedInfo": [temp_info.get('fare_key')]}

    post_data = {
        "id": 0,
        "method": "DataService.service",
        "params": [{
            "javaClass": "com.jein.framework.connectivity.parameter.RequestParameter",
            "requestUniqueCode": "PGWHC00001",
            "requestExecuteType": "BIZ",
            "DBTransaction": 'false',
            "sourceName": 'null',
            "sourceExtension": 'null',
            "functionName": "DTWBA00027",
            "panelId": 'null',
            "methodType": 'null',
            "inParameters": {
                "javaClass": "java.util.List",
                "list": [{
                    "javaClass": "com.jein.framework.connectivity.parameter.InParameter",
                    "paramName": "flightPriceInfo",
                    "ioType": "IN",
                    "structureType": "FIELD",
                    "data": {
                        "javaClass": "java.util.List",
                        "list": [{
                            "map": {
                                "flightPriceInfo": json.dumps(data)
                            },
                            "javaClass": "java.util.Map"
                        }]
                    }
                }]
            },
            "filterParameter": {
                "javaClass": "java.util.Map",
                "map": {}
            }
        }]
    }

    return post_data
