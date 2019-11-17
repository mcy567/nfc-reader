#coding=utf-8

import time 
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send(head, content) :
    try:
        local_date = time.strftime("%Y%m%d", time.localtime())   
        sender = '' #发件人的邮件地址                 e.g.: 111111@qq.com  
        password='' #发件人的客户端授权码(非密码)     e.g.: xxxxxxxxxxxxxx
        host=''     #发件人用的邮件服务器             e.g.：QQ邮箱默认为 smtp.qq.com
        receivers = ['']  # 接收邮件，可设置为你的邮箱并可添加多个   e.g.: 111111@qq.com 
        meg_text = content  #邮件内容
        message = MIMEMultipart()
        message.attach(MIMEText(meg_text, 'html', 'utf-8'))
        # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
        message['From'] = Header("fajianren", 'utf-8') #内容中显示的发件人
        message['To'] =  Header("shoujianren", 'utf-8')  #内容中显示的收件人
        message['Subject'] = Header(head, 'utf-8')  #邮件的题目
        
        # 构造附件1，传送当前目录下的 test.txt 文件
        #att1 = MIMEText(open('/tmp/hunting/mcy/'+local_date+'.xls', 'rb').read(), 'base64', 'utf-8')
        #att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        #att1["Content-Disposition"] = 'attachment; filename="' + local_date + '.xls"'
        #message.attach(att1)
        
        ## 构造附件2，传送当前目录下的 runoob.txt 文件
        #att2 = MIMEText(open('test/test.mp3', 'rb').read(), 'base64', 'utf-8')
        #att2["Content-Type"] = 'application/octet-stream'
        #att2["Content-Disposition"] = 'attachment; filename="two.mp3"'
        #message.attach(att2)
        
        smtpObj = smtplib.SMTP_SSL()    #这个点要注意
        smtpObj.connect(host)
        smtpObj.login(sender,password)  #邮箱登录
        smtpObj.sendmail(sender, receivers, message.as_string())
        smtpObj.close()
    except Exception as e:
        print('邮件发送失败：')
        print(e)
    else:
        print ("邮件发送成功")