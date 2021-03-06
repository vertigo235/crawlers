# -*- coding: utf-8 -*-

import re
import time

import requests

from .. import db


class Crawler:
    def __init__(self):
        self.host = "http://www.carnival.com/BookingEngine/SailingSearch/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36',
            'Accept': 'text/html;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'utf-8,gbk;q=0.7,*;q=0.3',
            'Connection': 'close',
            'Referer': self.host
        }

    def run(self, page):
        url = self.host + 'Get?datFrom=012016&datTo=012020&pageSize=100&pageNumber=' + str(page)
        res = requests.get(url, headers=self.headers).json()

        if len(res['Itineraries']) == 0:
            return False

        for itinerary in res['Itineraries']:
            self.save_itinerary(itinerary)

        return True

    @staticmethod
    def save_itinerary(itinerary):
        data = []
        price_pattern = re.compile(r'^\$(\d+)')
        for sailing in itinerary['Sailings']:
            departure_time = int(time.mktime(time.strptime(sailing['SailDateMMddyyyyInv'], "%m%d%Y")))
            inside = 0 if len(price_pattern.findall(sailing['INPriceText'])) == 0 else \
                price_pattern.findall(sailing['INPriceText'].replace(',', ''))[0]
            ocean_view = 0 if len(price_pattern.findall(sailing['OVPriceText'])) == 0 else \
                price_pattern.findall(sailing['OVPriceText'].replace(',', ''))[0]
            balcony = 0 if len(price_pattern.findall(sailing['BAPriceText'])) == 0 else \
                price_pattern.findall(sailing['BAPriceText'].replace(',', ''))[0]
            suite = 0 if len(price_pattern.findall(sailing['STPriceText'])) == 0 else \
                price_pattern.findall(sailing['STPriceText'].replace(',', ''))[0]

            data.append("('carnival', '" + \
                        str(itinerary['ItineraryCode']) + \
                        "', '" + itinerary['ItnDescriptionText'] + \
                        "', '" + itinerary['ShipText'] + \
                        "', '" + str(itinerary['DurationDays']) + \
                        "', '" + itinerary['PortList'][0] + \
                        "', FROM_UNIXTIME(" + str(departure_time) + \
                        "), '" + str(inside) + \
                        "', '" + str(ocean_view) + \
                        "', '" + str(balcony) + \
                        "', '" + str(suite) + \
                        "', '" + str(int(sailing['LowestPrice'])) + \
                        "')")

        db.save(data)
        print itinerary['ItnDescriptionText'].encode('utf-8') + ' Done! '
