# -*- coding: utf-8 -*-

import time

import requests

from .. import db


def get_price(item):
    if 'startingFromPrice' not in item:
        return 0
    return int(float(item['startingFromPrice']['price']['summary']['total']))


def build_row(sailing, cruise_sailings):
    row = {}
    sailing_id = sailing['sailingId']

    if sailing_id not in cruise_sailings['sailings']:
        return False
    cruise_sailing = cruise_sailings['sailings'][sailing_id]

    row['project'] = 'disneycruise'
    row['departure_time'] = int(time.mktime(time.strptime(cruise_sailing['name'], "%B %d, %Y")))
    row['duration'] = cruise_sailing['numberOfNights']
    row['itinerary_id'] = cruise_sailing['product'].split(';').pop(0)

    if cruise_sailing['product'] not in cruise_sailings['products']:
        return False
    cruise_product = cruise_sailings['products'][cruise_sailing['product']]
    cruise_ship = cruise_sailings['ships'][cruise_sailing['ship']]
    cruise_port = cruise_sailings['ports'][cruise_sailing['portFrom']]

    row['title'] = cruise_product['name']
    row['ship_name'] = cruise_ship['name']
    row['departure_port'] = cruise_port['name'].split(",").pop(0)

    inside = sailing['startingFromPriceByPartyMix'][0]['stateroomTypes'][0]
    ocean_view = sailing['startingFromPriceByPartyMix'][0]['stateroomTypes'][1]
    balcony = sailing['startingFromPriceByPartyMix'][0]['stateroomTypes'][2]
    suite = sailing['startingFromPriceByPartyMix'][0]['stateroomTypes'][3]

    row['inside'] = get_price(inside)
    row['oceanview'] = get_price(ocean_view)
    row['balcony'] = get_price(balcony)
    row['suite'] = get_price(suite)

    return row


class Crawler:
    def __init__(self):
        self.host = "https://disneycruise.disney.go.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36',
            'Accept': 'text/html;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'utf-8,gbk;q=0.7,*;q=0.3',
            'Connection': 'close',
            'Content-Type': 'application/json',
            'Authorization': 'BEARER ugH_oCuHbY1JlXTEiQAWYA',
            'Referer': self.host
        }
        self.payload = {
            "currency": "USD",
            "affiliations": [],
            "partyMix": [
                {"accessible": False,
                 "adultCount": 2,
                 "childCount": 0,
                 "orderBuilderId": None,
                 "nonAdultAges": [],
                 "partyMixId": "0"}
            ]
        }

    def get_token(self):
        url = self.host + 'wam/authentication/get-client-token/'
        res = requests.get(url).json()
        return res['access_token']

    def run(self, page):
        token = self.get_token()
        self.headers['Authorization'] = 'BEARER ' + token
        url = self.host + 'wam/cruise-sales-service/cruise-listing/?region=INTL&storeId=DCL&view=cruise-listing'
        res = requests.post(url, json=self.payload, headers=self.headers).json()

        cruise_sailings = res['cruise-sailings']
        sailings = res['sailings-availability']['sailings']

        data = []
        for sailing_id in sailings:
            row = build_row(sailings[sailing_id], cruise_sailings)
            if not row:
                continue
            data.append("('disneycruise', '" + \
                        row['itinerary_id'] + \
                        "', '" + row['title'] + \
                        "', '" + row['ship_name'] + \
                        "', '" + str(row['duration']) + \
                        "', '" + row['departure_port'] + \
                        "', FROM_UNIXTIME(" + str(row['departure_time']) + \
                        "), '" + str(row['inside']) + \
                        "', '" + str(row['oceanview']) + \
                        "', '" + str(row['balcony']) + \
                        "', '" + str(row['suite']) + \
                        "', '" + str(0) + \
                        "')")
            print row['title'].encode('utf-8') + ' Done! '

        db.save(data)
        return False


if __name__ == "__main__":
    c = Crawler()
    c.run(1)
