# -*- coding: utf-8 -*-
import requests
import re
import threading
import ConfigParser
import MySQLdb
import time
import datetime
import os
from bs4 import BeautifulSoup
import util

from xlwt import *

class question:

    def __init__(self):


        self.agent = 'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0'
        self.headers = {
            "Host": "www.zhihu.com",
            "Referer": "https://www.zhihu.com",
            'User-Agent': self.agent
        }

        self.session = requests.session()
        self.session.headers = self.headers

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
    根据话题id和排序方式展示最热和最新问题
    topic_id默认为‘hot’，或者为‘newest’
    '''
    def getQuestionsByTopicId(self,topic_id,style):
        if style=='hot':
            off_set = 3262.04139185
        else:
            off_set=time.time()

        url = "https://www.zhihu.com/topic/" + topic_id +"/"+style
        content = self.session.get(url,timeout=5).content
        #url_newest= "https://www.zhihu.com/topic/" + topic_id + "/newest"
        # content_hot=self.session.get(url_hot).content
        # content_newest=self.session.get(url_newest).content
        # soup=BeautifulSoup(content_newest,"lxml")
        # print soup.prettify()



        pattern = re.compile(
            '<div class="feed-main">.*?<h2>.*?<a class="question_link".*?href="/question/(.*?)".*?>(.*?)</a>'
            '.*?class="zm-item-vote">.*?<a .*?zm-item-vote-count.*?>(.*?)</a>', re.S)

        questions = re.findall(pattern, content)
        #print questions
        #获取——xsrf
        # 获取请求参数X-Xsrftoken
        pattern = r'name="_xsrf" value="(.*?)"'
        _xsrf = re.findall(pattern, content)
        xToken = _xsrf[0]
        # 当get得到topic数量为20时，需要异步请求，加载更多数据

        while True:
            questions_XHR = self.getQuestionsByXHR(topic_id,xToken,style,0,off_set)
            #print len(questions_XHR),questions_XHR
            # 合并到topic
            if len(questions_XHR)!=0:
                questions.extend(questions_XHR)
                #print len(questions)

            off_set=off_set-0.5

            count=len(questions)
            if count >= 20:
                break
            time.sleep(1)

        return questions



    def write2Excel(self,questions,path):
        book = Workbook()

        # for (k,v) in questions.items():
        #     sheet=book.add_sheet(k,cell_overwrite_ok=True)
        #
        #     col=0
        #     row=0
        #     for item in v:
        #         sheet.write(col, row, item[1].decode('utf-8'))  # 不解码要报错
        #         sheet.write(col, row + 1, item[2])
        #         url = 'https://www.zhihu.com/question/' + item[0]
        #         sheet.write(col, row + 2, Formula('HYPERLINK("' + url + '","' + item[0] + '")'))  # 创建超链接
        #         col = col + 1

        sheet_hot=book.add_sheet('hot',cell_overwrite_ok=True)
        sheet_newest=book.add_sheet('newest',cell_overwrite_ok=True)
        #设置宽度
        sheet_hot.col(0).width = 20000
        sheet_newest.col(0).width = 20000

        questions_hot=questions['hot']
        questions_newest=questions['newest']
        col=0
        row=0
        for question in questions_hot:
            sheet_hot.write(col,row,question[1].decode('utf-8')) #不解码要报错
            sheet_hot.write(col, row+1, question[2])
            url='https://www.zhihu.com/question/'+question[0]
            sheet_hot.write(col, row+2,  Formula('HYPERLINK("'+url+'","'+question[0]+'")')) #创建超链接
            col=col+1
        col=0
        row=0
        for question in questions_newest:
            sheet_newest.write(col, row, question[1].decode('utf-8'))  # 不解码要报错
            sheet_newest.write(col, row + 1, question[2])
            url = 'https://www.zhihu.com/question/' + question[0]
            sheet_newest.write(col, row + 2, Formula('HYPERLINK("' + url + '","' + question[0] + '")'))  # 创建超链接
            col = col + 1

        #保存文件名，用日期来保存,文件中含有中文可能会报错
        today=datetime.date.today()
        filename=str(today.strftime("%Y%m%d")+".xls")
        # #打开对应话题的文件夹，如果不存在则创建文件夹，文件夹以话题名命名（需要查表）
        # self.cursor.execute("SELECT NAME FROM TOPIC WHERE LINK_ID = %s",int(topic_id))
        # result = self.cursor.fetchone()
        # topic_name=result[0].encode('utf-8')
        # desPath='E:\\zhihu'+'\\'+topic_name
        # if not os.path.exists(desPath):
        #     os.makedirs(desPath.decode('utf-8'))

        #book.save(filename)
        path_file=path+'\\'+filename

        if os.path.exists(path_file):
            os.remove(path_file)

        book.save(path_file)
        print u"创建文件："+filename

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

    def getQuestionsByXHR(self, topic_id,xToken,style, start, offset):

        url = "https://www.zhihu.com/topic/"+topic_id+"/"+style
        data = {"start": start, "offset": offset}
        # page = self.session.get(url,timeout=4).content
        #
        # # 获取请求参数X-Xsrftoken
        # pattern = r'name="_xsrf" value="(.*?)"'
        # _xsrf = re.findall(pattern, page)
        # xToken = _xsrf[0]
        # print xToken
        self.session.headers["X-Xsrftoken"] = xToken
        self.session.headers["X-Requested-With"] = "XMLHttpRequest"

        # page返回的事json格式的
        page = self.session.post(url, data,10).content
        #print page

        pattern = re.compile(
            r'<div class=\\"feed-main\\">.*?<h2>.*?<a class=\\"question_link\\".*?href=\\"\\/question\\/(.*?)\\".*?>(.*?)<\\/a>.*?class=\\"zm-item-vote\\">.*?<a .*?zm-item-vote-count.*?>(.*?)<\\/a>', re.S)

        # 注意里面的特殊字符的转义

        questions = re.findall(pattern, page)

        # 转换字符编码
        i = 0
        for question in questions:
            str = question[1].decode('unicode-escape')  # 将unicode字符解码成中文
            question = (question[0], str.encode('utf-8'),question[2])  # 转成utf-8
            questions[i] = question
            i = i + 1
            # print topic

        return questions
