#!/usr/bin/python
# encoding: utf-8
import re

import requests
from bs4 import BeautifulSoup

from med.yyk import db


class DoctorListParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
        }

    def get_list(self, page):
        url = 'http://yyk.39.net/doctors/c_p' + str(page) + '/'

        if db.get_url(url) is not None:
            print 'list ' + url + ' exists'
            return True

        res = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(res.text, 'lxml')

        doctor_list = soup.select('.serach-left-list li')

        if len(doctor_list) == 0:
            if res.status_code == 200:
                print 'list page is empty'
                return False
            else:
                print 'status code : ' + str(res.status_code) + '. list page error!'
                return True

        sql = 'INSERT INTO doctors(`user_id`, `name`, `title`, `hospital`, `section`, `photo`) VALUES (%s, %s, %s, %s, %s, %s)'

        for doctor in doctor_list:
            a = doctor.find('a')
            user_id = re.compile(r'(\d+)\.html').findall(a.attrs['href'])[0]
            name = a.attrs['title']
            photo = a.find('img').attrs['src']

            p_list = doctor.find_all('p')
            title = ','.join(re.compile(r'\S+').findall(p_list[0].get_text()))
            hospital = ','.join(map((lambda x: x.get_text()), p_list[1].find_all('a')))
            section = ','.join(map((lambda x: x.get_text()), p_list[2].find_all('a')))

            try:
                db.execute(sql, [user_id, name, title, hospital, section, photo])
            except Exception:
                continue

        db.save_url(url)
        return True

    def get_detail(self, user_id):

        url = 'http://yyk.39.net/doctor/' + user_id + '.html'

        if db.get_url(url) is not None:
            print 'detail ' + url + ' exists'
            return True

        try:
            res = requests.get(url, headers=self.headers)
        except Exception:
            return False

        soup = BeautifulSoup(res.text, 'lxml')

        detail = soup.find('div', class_='doc-detail')

        if detail is None:
            print 'status code : ' + str(res.status_code) + '. detail page error!'
            return True

        intro_more = soup.select_one('.intro_more')

        if intro_more is not None and re.compile(ur'擅长领域：(.*)').findall(intro_more.get_text()):
            skills = re.compile(ur'擅长领域：(.*)').findall(intro_more.get_text())[0]
        elif intro_more is not None and re.compile(ur'擅长领域：(\S+)').findall(detail.get_text()):
            skills = re.compile(ur'擅长领域：(\S+)').findall(detail.get_text())[0]
        else:
            skills = ''

        experience = ''
        if soup.find(class_='hos-guide-box1'):
            experience = soup.find(class_='hos-guide-box1').get_text().strip()

        print user_id

        sql = 'UPDATE doctors SET `skills`=%s, `experience`=%s WHERE `user_id`=%s'

        db.execute(sql, [skills, experience, user_id])
        db.save_url(url)

# DoctorListParser().get_list(1)
