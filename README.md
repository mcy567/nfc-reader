# nfc-reader

一步步教你制作移动式银行卡信息读取器：
https://zhuanlan.zhihu.com/p/93398713

运行程序执行：
python3 nfc.py

注：在执行前需要先配置邮件服务，即send_mails.py文件的下面几个字段

sender = '' #发件人的邮件地址                 e.g.: 111111@qq.com

password='' #发件人的客户端授权码(非密码)     e.g.: xxxxxxxxxxxxxx

host=''     #发件人用的邮件服务器             e.g.：QQ邮箱默认为 smtp.qq.com

receivers = ['']  # 接收邮件，可设置为你的邮箱并可添加多个   e.g.: 111111@qq.com
