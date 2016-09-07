# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import threading
import ConfigParser
import MySQLdb
import time
import util

class topic:
    def __init__(self,session):
        self.session=session
        cf=ConfigParser.ConfigParser()
        cf.read("config.ini")

        host=cf.get("db","host")
        port = int(cf.get("db", "port"))
        user=cf.get("db","user")
        password=cf.get("db","passwd")
        db_name=cf.get("db","db")
        charset =cf.get("db","charset")
        use_unicode =cf.get("db","use_unicode")

        self.db=MySQLdb.connect(host=host,port=port,user=user,passwd=password,db=db_name,charset=charset,use_unicode=use_unicode)
        self.cursor=self.db.cursor()

    def getTopics(self, token):
        topics_url = "http://www.zhihu.com/people/" + token + "/topics"
        content = self.session.get(topics_url).content
        try:
            pattern = re.compile(
                '<div.*?zm-profile-section-main">.*?<a.*?</a>.*?<a.*?href="/topic/(.*?)".*?<strong>(.*?)</strong>',
                re.S)
            topics = re.findall(pattern, content)
        except:
            print "没有匹配到话题"

        return topics

    def updateTopics(self,topics):

        for topic in topics:

            is_exist="SELECT LINK_ID FROM TOPIC WHERE LINK_ID = %s"
            self.cursor.execute(is_exist,topic[0])
            result=self.cursor.fetchone()
            #如果结果为空则插入新数据
            if result==None:
                insert_stmt = ("INSERT INTO TOPIC (NAME,LAST_VISIT,LINK_ID) VALUES (%s, %s, %s )")
                link_id=int(topic[0])
                name=topic[1]
                visit_time = int(time.time())
                data=(name,visit_time,link_id)
                n=self.cursor.execute(insert_stmt, data)
                print n

        self.db.close()

