# -*- coding: utf-8 -*-
import requests
import re
import threading
import ConfigParser
import MySQLdb
import time
import util



class question:

    def __init__(self,session):
        self.session = session

        cf = ConfigParser.ConfigParser()
        cf.read("config.ini")

        host = cf.get("db", "host")
        port = int(cf.get("db", "port"))
        user = cf.get("db", "user")
        password = cf.get("db", "passwd")
        db_name = cf.get("db", "db")
        charset = cf.get("db", "charset")
        use_unicode = cf.get("db", "use_unicode")

        self.db = MySQLdb.connect(host=host, port=port, user=user, passwd=password, db=db_name, charset=charset,
                                  use_unicode=use_unicode)
        self.cursor = self.db.cursor()


    '''
       传入话题id,page,获取问题
       '''
    def updateQuestionsByTopicId(self, topic_id, page):
        url = "https://www.zhihu.com/topic/" + topic_id + "/top-answers?page=" + str(page)
        content = self.session.get(url).content
        pattern = re.compile('.*?feed-item feed-item-hook folding.*?<link itemprop.*?href="/question/(.*?)/answer/(.*?)"'
                             '.*?answerCount" content="(.*?)".*?question_link.*?>(.*?)</a>.*?'
                             'zm-item-vote-info" data-votecount="(.*?)"', re.S)

        questions = re.findall(pattern, content)
        # 问题id,最高回答id，回答数，问题名称，回答最高票数
        for question in questions:
            print u'问题：',question[3]

            is_exist = "SELECT LINK_ID FROM QUESTION WHERE LINK_ID = %s"
            self.cursor.execute(is_exist, question[0])
            result = self.cursor.fetchone()

            if result == None:
                insert_stmt = (
                "INSERT INTO QUESTION (NAME,LINK_ID,FOCUS,ANSWER,LAST_VISIT,TOP_ANSWER_NUMBER,TOPIC_ID) VALUES (%s, %s, %s ,%s,%s,%s,%s)")
                link_id = int(question[0])
                name = question[3]
                focus = 0
                anwser_count = int(question[2])
                last_visit = int(time.time())
                top_answer_vote = int(question[4])

                data = (name, link_id, focus, anwser_count, last_visit, top_answer_vote,topic_id)
                n = self.cursor.execute(insert_stmt, data)
                if n==1:
                    print u"插入问题：",name



