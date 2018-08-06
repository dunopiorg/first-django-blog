from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from django.utils import timezone
from django.db.models.signals import post_save
from . import config as cfg
import pymysql
import pandas as pd
from .lib import query_loader


class Post(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(blank=True, null=True)
    published_date = models.DateTimeField(blank=True, null=True)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()
        
    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=100, default='')
    city = models.CharField(max_length=100, default='')
    website = models.URLField(default='')
    phone = models.IntegerField(default=0)
    
    def create_profile(sender, **kwargs):
        if kwargs['created']:
            user_profile = UserProfile.objects.create(user=kwargs['instance'])
            
    post_save.connect(create_profile, sender=User)
    

class Lab2AIConnector(object):

    # region [INITIALIZATION]
    def __init__(self):
        self._HOST = cfg.AWS_SERVER
        self._USER = cfg.AWS_USER
        self._PASSWORD = cfg.AWS_PASSWORD
        self._DATABASE = cfg.AWS_DATABASE
        self._PORT = cfg.AWS_PORT
        self.ql = query_loader.QueryLoader('blog/query_xml')
    # endregion [INITIALIZATION]

    # region [QUERY EVENT]
    def insert_article(self, data):
        my_conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')
        try:
            with my_conn.cursor() as cursor:
                sql_query = """INSERT INTO minor_baseball.robot_article 
                 (game_id, le_id, serial, gyear, `status`, title, article, created_at, time_key)
                 VALUES ("{game_id}", {le_id}, {serial}, "{gyear}", 
                 "{status}", "{title}", "{article}", "{created_at}", CAST(NOW()+0 AS CHAR))""".format(**data)
                
                cursor.execute(sql_query)
            my_conn.commit()
        finally:
            my_conn.close()
    
    def insert_history(self, data, counter):
        my_conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')
        try:
            with my_conn.cursor() as cursor:
                sql_query = """INSERT INTO minor_baseball.robot_article_history 
                 (game_id, le_id, serial, gyear, `status`, title, article, created_at, time_key)
                 VALUES ("{game_id}", {le_id}, {serial}, "{gyear}", 
                 "{status}", "{title}", "{article}", "{created_at}",CAST(NOW()+0 AS CHAR))""".format(**data)
                
                cursor.execute(sql_query)
            my_conn.commit()
        finally:
            my_conn.close()
            
    def select_count(self, game_id, gyear):
        my_conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')
        result = None
        try:
            with my_conn.cursor() as cursor:
                sql_query = """SELECT count(game_id) as counter FROM minor_baseball.robot_article_history 
                 where game_id="{0}" and gyear={1}""".format(game_id, gyear)
                
                cursor.execute(sql_query)
                result = cursor.fetchone()
        finally:
            my_conn.close()
        
        return result

    # endregion [QUERY EVENT]

    # region [HITTER RECORD]
    def get_hitter_gamecontapp_record(self, hitter_code, game_key=None, limit=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if game_key is None:
            gmkey = ' '
        else:
            gmkey = " AND GMKEY = '{0}' ".format(game_key)

        if limit is None:
            limit_state = ' '
        else:
            limit_state = " LIMIT {0} ".format(limit)

        query_format = self.ql.get_query("query_hitter", "get_hitter_gamecontapp_record")
        query = query_format.format(HITTER=hitter_code, GMKEY=gmkey, LIMIT=limit_state)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_kbo_hitter_total(self, hitter_code):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_hitter", "get_kbo_hitter_total")
        query = query_format.format(HITTER=hitter_code)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_hitter_total(self, hitter_code, game_year=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if game_year is None:
            gyear = ''
        else:
            gyear = game_year

        query_format = self.ql.get_query("query_hitter", "get_kbo_hitter_total")
        query = query_format.format(HITTER=hitter_code, GYEAR=gyear)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_hitter(self, hitter_code, limit=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if limit is None:
            limit_state = ' '
        else:
            limit_state = " LIMIT {0} ".format(limit)

        query_format = self.ql.get_query("query_hitter", "get_hitter")
        query = query_format.format(HITTER=hitter_code, LIMIT=limit_state)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    # endregion [HITTER RECORD]

    # region [PITCHER RECORD]
    def get_pitcher(self, pitcher_code, limit=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if limit is None:
            limit_state = ' '
        else:
            limit_state = " LIMIT {0} ".format(limit)

        query_format = self.ql.get_query("query_pitcher", "get_pitcher")
        query = query_format.format(PITCHER=pitcher_code, LIMIT=limit_state)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_kbo_pitcher(self, pitcher_code, limit=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if limit is None:
            limit_state = ' '
        else:
            limit_state = " LIMIT {0} ".format(limit)

        query_format = self.ql.get_query("query_pitcher", "get_kbo_pitcher")
        query = query_format.format(PITCHER=pitcher_code, LIMIT=limit_state)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_pitcher_total(self, pitcher_code, game_year=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if game_year is None:
            gyear = ''
        else:
            gyear = " AND GYEAR = {0}".format(game_year)

        query_format = self.ql.get_query("query_pitcher", "get_pitcher_total")
        query = query_format.format(PITCHER=pitcher_code, GYEAR=gyear)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_pitcher_gamecontapp_record(self, pitcher_code, game_id=None, limit=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if game_id is None:
            game_id_state = ' '
        else:
            game_id_state = "AND GMKEY = '{0}' ".format(game_id)

        if limit is None:
            limit_state = ' '
        else:
            limit_state = " LIMIT {0} ".format(limit)

        query_format = self.ql.get_query("query_pitcher", "get_pitcher_gamecontapp_record")
        query = query_format.format(PITCHER=pitcher_code, GAME_ID=game_id_state, LIMIT=limit_state)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_kbo_pitcher_total(self, pitcher_code):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_pitcher", "get_kbo_pitcher_total")
        query = query_format.format(PITCHER=pitcher_code)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    # endregion [PITCHER RECORD]

    # region [ETC RECORD]
    def get_score(self, game_year=None, team_code=None):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        if game_year is None:
            gyear_state = ' '
        else:
            gyear_state = " and gday like '{0}%'".format(game_year)

        if team_code is None:
            team_code = ''
        else:
            team_code = " and (gmkey like like '%{0}___' or gmkey like '%{0}0')".format(team_code)

        query_format = self.ql.get_query("query_common", "get_score")
        query = query_format.format(GYEAR=gyear_state, TEAM=team_code)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_injury(self, player_code):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_injury")
        query = query_format.format(PCODE=player_code)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_minor_team_name_info(self):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_minor_team_name_info")
        query = query_format.format()

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_kbo_team_name_info(self):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_kbo_team_name_info")
        query = query_format.format()

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_team_rank(self, team_code):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_team_rank")
        query = query_format.format(TEAM=team_code)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_team_score(self, team_code):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_team_score")
        query = query_format.format(TEAM=team_code)

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_test_team_scores(self):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db=self._DATABASE, charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_test_team_scores")
        query = query_format.format()

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def set_rds_db_team_sentence(self, data):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db='oper_db', charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "set_rds_db_team_sentence")
        query = query_format.format(data['SUBJECT'],
                                    data['CATEGORY'],
                                    data['INDEX'],
                                    data['PRIORITY'],
                                    data['CONDITIONS'],
                                    data['SENTENCE'],
                                    data['PARAMETERS'],
                                    )

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            conn.commit()

        return result

    def delete_rds_db_team_sentence(self):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db='oper_db', charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "delete_rds_db_team_sentence")
        query = query_format.format()

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            conn.commit()

        return result

    def get_template_db_by_name(self, table_name):
        conn = pymysql.connect(host=self._HOST, port=self._PORT, user=self._USER, password=self._PASSWORD,
                               db='oper_db', charset='utf8mb4')

        query_format = self.ql.get_query("query_common", "get_template_db_by_name")
        query = query_format.format(table_name)

        df = pd.read_sql(query, conn)
        conn.close()
        return df
    # endregion [ETC RECORD]
