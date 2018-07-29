from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from django.utils import timezone
from django.db.models.signals import post_save
from . import db_config as cfg
import pymysql


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
    
    def __init__(self):
        self._HOST = cfg.AWS_SERVER
        self._USER = cfg.AWS_USER
        self._PASSWORD = cfg.AWS_PASSWORD
        self._DATABASE = cfg.AWS_DATABASE
        self._PORT = cfg.AWS_PORT
    
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
    