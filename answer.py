# -*- coding: utf-8 -*-

import ConfigParser
import MySQLdb
import re
class answer:

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

    def getAnswerByQuestionId(self,question_id):
        url='https://www.zhihu.com/question/'+question_id
        content=self.session.get(url).content
        print content
        #答案token,作者姓名，作者token，question_id,点赞数，评论数，收藏数，最近访问
        source='zm-item-answer  zm-item-expanded.*?data-atoken="(.*?)".*?' \
               'author-link-line.*?author-link.*?href="/people/(.*?)">(.*?)</a>' \
               '.*?class="js-voteCount">(.*?)</span>.*?' \
               'answer-date-link meta-item.*?编辑于 (.*?)</a>.*?z-icon-comment.*?"(.*?) 条评论"'
        temp = source.decode('utf-8')
        xx = u"([/u4e00-/u9fa5]+)"
        # pattern=re.compile(ur'zm-item-answer  zm-item-expanded.*?data-atoken="(.*?)".*?author-link-line.*?'
        #                    'author-link.*?href="/people/(.*?)">(.*?)</a>.*?class="js-voteCount">(.*?)</span>'
        #                    '.*?answer-date-link meta-item.*?编辑于 (.*?)</a>'
        #                    '.*?z-icon-comment.*?"(.*?) 条评论"',re.S)
        # answers=re.findall(pattern,content)

        # print answers