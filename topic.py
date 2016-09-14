# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import threading
import ConfigParser
import MySQLdb
import time
import util
import os

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

    '''
    包含同步请求 和 异步请求
    '''
    def getTopics(self, token):
        topics_url = "http://www.zhihu.com/people/" + token + "/topics"
        content = self.session.get(topics_url).content
        off_set=0

        pattern_xtoken = r'name="_xsrf" value="(.*?)"'
        _xsrf = re.findall(pattern_xtoken, content)
        xToken = _xsrf[0]

        pattern = re.compile(
            '<div.*?zm-profile-section-main">.*?<a.*?</a>.*?<a.*?href="/topic/(.*?)".*?<strong>(.*?)</strong>',
            re.S)
        topics = re.findall(pattern, content)

        #topic_count=len(topics)
        #当get得到topic数量为20时，需要异步请求，加载更多数据
        if len(topics)==20:
            while True:
                off_set=off_set+20
                topics_XHR = self.getTopicsByXHR(topics_url,xToken, 0, off_set)
                #合并到topic
                topics.extend(topics_XHR)
                #如果返回的topic数量小于20说明不用再请求，终止
                if len(topics_XHR) < 20:
                    break

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
                if n==1:
                    print "插入新话题：",topic[1]


    '''
       start:一定要为0
       offset：实际为开始的话题索引0,40 代表从第41个话题还是返回
       每次返回20条数据
       不足20条说明已经到最后一组
       '''
    def getTopicsByXHR(self, topic_url,xToken,start, offset):

        #url = "https://www.zhihu.com/people/jesseo722/topics"
        data = {"start": start, "offset": offset}
        # page = self.session.get(topic_url).content

        #获取请求参数X-Xsrftoken
        # pattern = r'name="_xsrf" value="(.*?)"'
        # _xsrf = re.findall(pattern, page)
        # xToken = _xsrf[0]
        #print xToken
        self.session.headers["X-Xsrftoken"] = xToken
        self.session.headers["X-Requested-With"] = "XMLHttpRequest"

        #page返回的事json格式的
        page = self.session.post(topic_url, data).content
        #print page
        #注意里面的特殊字符的转义
        pattern = re.compile(
            r'zm-profile-section-main.*?zg-right zg-btn zg-btn-unfollow.*?<a href=\\"\\/topic\\/(.*?)\\".*?<strong>(.*?)<\\/strong>',
            re.S)
        topics = re.findall(pattern, page)

        #转换字符编码
        i = 0
        for topic in topics:
            str=topic[1].decode('unicode-escape') #将unicode字符解码成中文
            topic=(topic[0],str.encode('utf-8'))   #转成utf-8
            topics[i]=topic
            i=i+1
            #print topic

        return topics


