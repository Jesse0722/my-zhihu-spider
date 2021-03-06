# -*- coding: utf-8 -*-

import requests

import cookielib
import re
import time
import os.path
import ConfigParser
import MySQLdb
from bs4 import BeautifulSoup
import topic
import question
import answer


def get_content(toUrl,count):
    """ Return the content of given url

           Args:
               toUrl: aim url
               count: index of this connect

           Return:
               content if success
               'Fail' if fail
       """
    agent = 'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0'
    headers = {
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        'User-Agent': agent
    }
    session = requests.session()
    session.headers = headers
    session.cookies = cookielib.LWPCookieJar(filename='cookies')

    try:
        content=session.get(toUrl,timeout=15).content

    except Exception,e:
        if count % 1==0:
            print str(count) + ", Error: " + str(e) + " URL: " + toUrl
        return "FAIL"

    return content


class util:

    def __init__(self):

        # 构造 Request headers
        self.agent = 'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0'
        self.headers = {
            "Host": "www.zhihu.com",
            "Referer": "https://www.zhihu.com",
            'User-Agent': self.agent
        }

        self.session = requests.session()
        self.session.headers=self.headers
        self.session.cookies = cookielib.LWPCookieJar(filename='cookies')


        try:
            self.session.cookies.load(ignore_discard=True)
        except:
            print("Cookie 未能加载")

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



    def get_xsrf(self):
        index_url='http://www.zhihu.com'
        index_page=self.session.get(index_url)
        html=index_page.text
        pattern=r'name="_xsrf" value="(.*?)"'
        _xsrf=re.findall(pattern,html)
        return _xsrf[0]

    def get_captcha(self):
        t=str(int(time.time()*1000))
        captcha_url='http://www.zhihu.com/captcha.gif?r='+t+'&type=login'
        r=self.session.get(captcha_url)
        #保存图片
        with open('captcha.jpg','wb') as f:
            f.write(r.content)
            f.close()

        print(u'请到 %s 目录找到captcha.jpg手动输入' %os.path.abspath('captcha.jpg'))
        captcha=raw_input(u'请输入验证码\n>')
        return captcha

    def isLogin(self):
        # 通过查看用户个人信息来判断是否已经登录
        #执行此方法前已经从文件中加载了cookies到session
        url = "https://www.zhihu.com/settings/profile"
        r=self.session.get(url,allow_redirects=False)
        #-----一下是获取域名
        #html=r.text
        #soap=BeautifulSoup(html,"lxml")
        #print soap.prettify()

        login_code=r.status_code
        #login_code = session.get(url, headers=headers,allow_redirects=False).status_code
        print "status_code:",login_code

        if int(x=login_code) == 200:
            return True
        else:
            return False

    def login(self,secret, account):
        # 通过输入的用户名判断是否是手机号
        if re.match(r"^1\d{10}$", account):
            print("手机号登录 \n")
            post_url = 'http://www.zhihu.com/login/phone_num'
            postdata = {
                '_xsrf': self.get_xsrf(),
                'password': secret,
                'remember_me': 'true',
                'phone_num': account,
            }
        else:
            print("邮箱登录 \n")
            post_url = 'http://www.zhihu.com/login/email'
            postdata = {
                '_xsrf': self.get_xsrf(),
                'password': secret,
                'remember_me': 'true',
                'email': account,
            }
        try:
            # 不需要验证码直接登录成功
            login_page = self.session.post(post_url, data=postdata)
            login_code = login_page.text
            print(login_page.status)
            print(login_code)
        except:
            # 需要输入验证码后才能登录成功
            print u"需要验证码登录"
            postdata["captcha"] = self.get_captcha()
            login_page = self.session.post(post_url, data=postdata)
            login_code = eval(login_page.text)
            print(login_code['msg'])
            self.session.cookies.save()




    def getToken(self):
        url = "https://www.zhihu.com/settings/profile"
        r=self.session.get(url,allow_redirects=False)
        content=r.content
        soap=BeautifulSoup(content,'lxml')
        token=soap.find('span',class_='token').get_text()

        home_page="http://www.zhihu.com/people/"+token
        print "home_page:"+home_page
        return token


    '''
    传入话题id,page,获取问题
    '''






# try:
#     input = raw_input
# except:
#     pass



if __name__=='__main__':
    obj=util()
    if obj.isLogin():
        print("您已经登陆")
    else:
        account = raw_input('请输入你的用户名\n>  ')
        secret = raw_input("请输入你的密码\n>  ")
        obj.login(secret, account)



    begin=int(time.time())
    print u"正在抓取个人您知乎数据...."
    #获取个人主页token
    token=obj.getToken()
    print u"获取个人主页token：",token


    obj_topic = topic.topic(obj.session)
    obj_question=question.question()
    obj_answer=answer.answer()


    # topic_id = '19551432'
    # questions=obj_question.getQuestionsByXHR(topic_id,'hot',0,3200.29677322)
    # for question in questions:
    #     print question[1]
    #questions = obj_question.getQuestionsByTopicId('19551432', 'hot')
    # topic_id='19551432'
    #
    # questions = obj_question.getQuestionsByTopicId(topic_id)
    #
    # # 创建话题文件夹（需要查表）
    # obj.cursor.execute("SELECT NAME FROM TOPIC WHERE LINK_ID = %s", int(topic_id))
    # result = obj.cursor.fetchone()
    # topic_name = result[0].encode('utf-8') #编译成中文
    # desPath = 'E:\\zhihu' + '\\' + topic_name.decode('utf-8')
    # if not os.path.exists(desPath):
    #     os.makedirs(desPath)
    #
    # #保存的excel写入文件夹
    # obj_question.write2Excel(questions,desPath)

    #obj_answer.getAnswerByQuestionId('27346629')
    # 获取topics
    print u"-------------正在获取关注话题---------------"
    topics=obj_topic.getTopics(token)
    for topic in topics:
        print topic[1]
    print u"-------------获取关注话题结束---------------"
    #话题入库
    print u"-------------正在从数据库中更新关注话题---------------"
    obj_topic.updateTopics(topics)
    print u"-------------更新关注话题结束---------------"
    #获取热门问题写入excel
    print u"-------------正在抓取您关注话题的精华问题---------------"
    for topic in topics:
        print u'您关注了话题：', topic[1]
        begin = int(time.time())
        questions={}
        questions_hot = obj_question.getQuestionsByTopicId(topic[0],'hot')
        questions_newest = obj_question.getQuestionsByTopicId(topic[0], 'newest')
        questions['hot']=questions_hot
        questions['newest']=questions_newest
        # 创建话题文件夹（需要查表）
        obj.cursor.execute("SELECT NAME FROM TOPIC WHERE LINK_ID = %s", int(topic[0]))
        result = obj.cursor.fetchone()
        topic_name = result[0].encode('utf-8')  # 编译成中文
        desPath = 'E:\\zhihu' + '\\' + topic_name.decode('utf-8')
        if not os.path.exists(desPath):
            os.makedirs(desPath)

        print questions
        obj_question.write2Excel(questions, desPath)
        end = int(time.time())
        print u"使用时间："+str(end-begin)
    # #问题入库
    # print u"-------------正在抓取您关注话题的精华问题---------------"
    # for topic in topics:
    #     print u"----当前话题：",topic[1],"-----"
    #     obj_question.updateQuestionsByTopicId(topic[0],1)

    obj.db.close()
    obj_question.db.close()
    obj_topic.db.close()
    end=int(time.time())
    print("Spend time :"+str(end-begin))


