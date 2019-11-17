#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.db import models
from datetime import datetime
import time
class List(models.Model):
    name = models.CharField(max_length=30,primary_key=True)
    ips = models.TextField()
    osuser = models.CharField(max_length=20)
    ospwd = models.CharField(max_length=35)
    osarch = models.CharField(max_length=20)
    osbreed = models.CharField(max_length=20)
    osrelease = models.CharField(max_length=20)
    ospart = models.TextField()
    ospackages = models.TextField()
    osenv = models.CharField(max_length=35)
    notice_mail = models.EmailField(max_length=254)
    drive_path = models.URLField(max_length=200)
    raid = models.CharField(max_length=300)
    start_time = models.CharField(max_length=20,default=time.time)
    usetime= models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    owner = models.CharField(max_length=30)
    flag = models.CharField(max_length=20)
class Detail(models.Model):
    name = models.CharField(max_length=30)
    ip = models.GenericIPAddressField()
    mac = models.CharField(max_length=55)
    netmask = models.CharField(max_length=55,default='255.255.255.0')
    gateway = models.GenericIPAddressField(default='N/R')
    ipmi_ip = models.GenericIPAddressField(default='N/R')
    vendor = models.CharField(max_length=50,default='N/R')
    hardware_model= models.CharField(max_length=50)
    hardware_sn = models.CharField(max_length=150)
    apply_template= models.CharField(max_length=50)
    start_time = models.CharField(max_length=20,default=time.time)
    usetime= models.CharField(max_length=30)
    status = models.TextField()
    owner = models.CharField(max_length=30)
    flag = models.CharField(max_length=20)
    class Meta:
        unique_together=("name","ip")

class Users(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=50)
    email = models.CharField(max_length=30,null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    last_login = models.DateTimeField()
    is_superuser = models.CharField(max_length=20)
    is_active = models.CharField(max_length=20)
    is_online = models.CharField(max_length=20)
    registry_time = models.DateTimeField(default=datetime.now)
    class Meta:
        unique_together=("username",)
class Groups(models.Model):
    name = models.CharField(max_length=30)
class Rights(models.Model):
    name = models.CharField(max_length=50)
    content_type_id = models.IntegerField ()
    codename = models.CharField(max_length=100)
    class Meta:
        unique_together=("content_type_id","codename")
class User_Group(models.Model):
    user = models.ForeignKey("Users",to_field="id",default=1,on_delete=models.CASCADE)
    group = models.ForeignKey("Groups",to_field="id",default=1,on_delete=models.CASCADE)
    class Meta:
        unique_together=("user","group")

class Group_Right(models.Model):
    group = models.ForeignKey("Groups",to_field="id",default=1,on_delete=models.CASCADE)
    right = models.ForeignKey("Rights",to_field="id",default=1,on_delete=models.CASCADE)
    class Meta:
        unique_together=("group","right")
class User_Right(models.Model):
    user = models.ForeignKey("Users",to_field="id",default=1,on_delete=models.CASCADE)
    right = models.ForeignKey("Rights",to_field="id",default=1,on_delete=models.CASCADE)
    class Meta:
        unique_together=("user","right")
