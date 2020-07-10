#!/usr/bin/env python
# -*- coding:utf-8 -*-
import pyexcel as pe


filename = '/root/test.xls'
book = pe.get_book(file_name=filename)
for sheet in book:
    if sheet.name == 'cmdb':
        sheet.name_columns_by_row(0) 
        records = sheet.to_records()
        i = 1
        for record in records:
            ci   = unicode(record[u'配置项编号'])
            ip   = unicode(record[u'业务IP'])
            app1 = unicode(record[u'一级业务系统'])
            app2 = unicode(record[u'二级业务系统'])
            app3 = unicode(record[u'三级业务系统'])
            print '%s %s %s %s %s'%(ci,ip,app1,app2,app3)
            if i>11:
                break
            else:
                i = i+1

