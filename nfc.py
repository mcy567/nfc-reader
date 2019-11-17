#coding=utf-8
import sys
import time
import requests

from smartcard.System import readers
from smartcard.util import toHexString, toBytes, HEX, PACK

from search_map import trade_type2str, create_card_info, read_tag, create_identityCard_info
import send_mails

def _card_type(typeStr):    #银行卡类型标注  
    # example: 'PBOC DEBIT' ==> 'PBOC DEBIT(借记卡)'
    if typeStr.upper() == 'PBOC DEBIT':
        typeStr = typeStr + '(借记卡)'
    elif typeStr.upper() == 'PBOC CREDIT':
        typeStr = typeStr + '(信用卡)'
    return typeStr


def _del20or00(astr):   #删除商户名称后边多余字符
    # example: 50424F435F4C4556454C32205445535400000000  ==> 50424F435F4C4556454C322054455354
    while astr[-2:] == '00' or astr[-2:] == '20':
        astr = astr[:-2]
    return astr
        
    
def _jie_duan1(rawStr): #返回字符串rawStr中'D'以前的字符，即银行卡号
    # example:  1111111111111111D191200000000000F ==> 1111111111111111111
    return rawStr[:rawStr.find('D')]
def _jie_duan2(rawStr): #返回字符串rawStr中'D'之后的4个字符，即失效日期
    # example:  1111111111111111D191200000000000F ==> 1912
    return rawStr[rawStr.find('D')+1:rawStr.find('D')+1+4]


def insert_chr(insertStr, intCount=4, intChr=' '):    #将银行卡号、日期等做下简单处理，便于观看
    # example: 1111111111111111111 ==> 1111 1111 1111 1111 111
    # example: 191210 ==> 19/12/10
    L = []
    for n in range(0,len(insertStr),intCount):    #每intCount个字符一个intChr
        L.append(insertStr[n:n+intCount])
    return intChr.join(L)
   
def log_analyzing(logStr):  #交易日志解析，转为字典，映射表参见<<JRT0025.5-2018 中国金融集成电路(IC)卡规范>>(下简称为JRT0025)第5部分 表45
    # example: 16070308461000000002000000000000000001560156494342432041544D000000000000000000000000010051 ==> {'9A': ['交易日期', '160703'], '9F21': ['交易时间', '084610'], '9F02': ['授权金额', '000000020000'], '9F03': ['其他金额', '000000000000'], '9F1A': ['终端国家代码', '0156'], '5F2A': ['交易货币代码', '0156'], '9F4E': ['商户名称', '494342432041544D'], '9C': ['交易类型', '01'], '9F36': ['应用交易计数器(ATC)', '0051']}
    log_tlv = {}
    log_tlv['9A'] = ['交易日期', logStr[0:6]]
    log_tlv['9F21'] = ['交易时间', logStr[6:12]]
    log_tlv['9F02'] = ['授权金额', logStr[12:24]]
    log_tlv['9F03'] = ['其他金额', logStr[24:36]]
    log_tlv['9F1A'] = ['终端国家代码', logStr[36:40]]
    log_tlv['5F2A'] = ['交易货币代码', logStr[40:44]]
    log_tlv['9F4E'] = ['商户名称', _del20or00(logStr[44:84])]
    log_tlv['9C'] = ['交易类型', logStr[84:86]]
    log_tlv['9F36'] = ['应用交易计数器(ATC)', logStr[-4:]]
    return log_tlv
    

def hex2gb2312(hexStr):     #将十六进制转换为gb2312字符
    # example: 494342432041544D ==> ICBC ATM
    return bytes(toBytes(hexStr)).decode('gb2312')


def tlv_analyzing(*tlv):    #对tlv格式进行解析,详细可参见JRT0025第5部分 附录A 表A.1
    tag = read_tag()
    newtag = {} 
    not_tlv2 = ('6F','70','72','73','77','80','A5','90')    # 2个字符的模板
    not_tlv4 = ('BF0C')                                     # 4个字符的模板
    for each_tlv in tlv:
        each_tlv_raw = each_tlv
        each_tlv = each_tlv + ' '
        # print(each_tlv)
        while len(each_tlv) != 1:   #说明还存在数据，如果为1则值为' '
            if each_tlv.startswith(not_tlv2):   #检测特殊情况,如果开头是2个字符的模板等
                if each_tlv[0:4] == '7081':     # 70为模板，以7081开头的一般长度有4位(81xx)，所以将7081xx删掉
                    each_tlv = each_tlv[6:]
                elif each_tlv[0:4] == '9081':   # 90为证书，暂不处理，直接连数据一起删掉
                    length = int(each_tlv[4:6], 16)
                    each_tlv = each_tlv[6+length*2:]
                else:
                    each_tlv = each_tlv[2+2:]   #将模板和长度删掉
            elif each_tlv.startswith(not_tlv4): #同上
                each_tlv = each_tlv[4+2:]
            else:                               #解析TLV
                if each_tlv[0:2] in [i for i in tag if len(i) == 2]:
                    length = int(each_tlv[2:4], 16)
                    value = each_tlv[4:4+length*2]
                    tag[each_tlv[0:2]][1] = value
                    each_tlv = each_tlv[4+length*2:]
                elif each_tlv[0:4] in [ j for j in tag if len(j) == 4]:
                    length = int(each_tlv[4:6], 16)
                    value = each_tlv[6:6+length*2]
                    tag[each_tlv[0:4]][1] = value
                    each_tlv = each_tlv[6+length*2:]
                else:                           #如果解析不了
                    print('发现未识别的标签：', each_tlv[0:2], 'or', each_tlv[0:4])
                    print('原始标签：', each_tlv_raw)
                    print('-' * 50)
                    break
    # print(tag)
    return tag   

    
if __name__ == '__main__':
    detection = 0   #检测扫描的银行卡是否和刚刚扫描的一致，如果一致则不再扫描，以免出现重复数据
    SELECT1 = [0x00,0xA4,0x04,0x00,0x07,0xA0,0x00,0x00,0x03,0x33,0x01,0x01] #选择卡片
    SELECT2 = [0x00,0xB2,0x01,0x14,0x00]    #银行卡号、生失效日期
    SELECT3 = [0x00,0xB2,0x01,0x0C,0x00]    #证件号、姓名、证件类型
    SELECT4 = [0x80,0xCA,0x9F,0x79,0x00]    #读取电子现金余额
    while True:     #程序持续运行
        try:        #选择卡片，发送请求数据，获取响应数据
            r = readers()   #以下代码及说明参见pyscard官方文档
            connection = r[0].createConnection()
            connection.connect()
            data1, sw1, sw2 = connection.transmit(SELECT1)
            if data1 == []:
                print('扫描到非银行卡')
                time.sleep(0.1)
                continue
            data2, sw1, sw2 = connection.transmit(SELECT2)
            if detection == data2:      #如果前后数据没变化，则重新扫描卡片
                continue
            data3, sw1, sw2 = connection.transmit(SELECT3)
            data4, sw1, sw2 = connection.transmit(SELECT4)
            data5_list = []
            for i in range(1,0xB):      #先从卡里读数据，后面再处理
                SELECT5 = [0x00,0xB2,i,0x5C,0x00]   #前 i 条交易日志
                data5, sw1, sw2 = connection.transmit(SELECT5)
                if data5 == []:
                    break
                else:
                    data5_list.append(data5)
        except:
            time.sleep(0.1)
        else:
            tlv1 = toHexString(data1,PACK)
            tlv2 = toHexString(data2,PACK)
            tlv3 = toHexString(data3,PACK)
            tlv4 = toHexString(data4,PACK)
            res = tlv_analyzing(tlv1,tlv2,tlv3,tlv4)
            s = ('''
银行卡类型：%(cardtype)s 
银行卡号：%(cardnumber)s
银行卡发卡行：%(cardbank)s
银行卡有效期：%(valid)s - %(invalid)s
电子现金余额：%(balance).2f
持卡人姓名：%(name)s
持卡人证件号：%(idcardnumber)s
证件归属地：%(idcardbelong)s
''' % {'cardtype': _card_type(hex2gb2312(res['50'][1])), 
'cardnumber': insert_chr(res['5A'][1].rstrip('F')) or insert_chr(_jie_duan1(res['57'][1])), 
'cardbank': create_card_info(res['5A'][1].rstrip('F')) or create_card_info(_jie_duan1(res['57'][1])), 
'valid': insert_chr(res['5F25'][1],2,'/'), 
'invalid': insert_chr(res['5F24'][1],2,'/') or insert_chr(_jie_duan2(res['57'][1]),2,'/'), 
'balance': int(res['9F79'][1])/100, 
'name': hex2gb2312(res['5F20'][1]), 
'idcardnumber': hex2gb2312(res['9F61'][1]), 
'idcardbelong': create_identityCard_info(hex2gb2312(res['9F61'][1])) }   )
            # print(s)
            s = s + '\n最近十次交易如下：'
            for data5 in data5_list:
                tlv5 = toHexString(data5,PACK)
                log_tlv = log_analyzing(tlv5)
                s = s + (
'''\n\n交易日期  交易时间  授权金额        商户名称        交易类型
%7s %9s %9.2f %15s %12s'''
% (insert_chr(log_tlv['9A'][1],2,'/'),
insert_chr(log_tlv['9F21'][1],2,':'),
int(log_tlv['9F02'][1])/100, 
hex2gb2312(log_tlv['9F4E'][1]), 
trade_type2str(log_tlv['9C'][1])))
            print(s)
            send_mails.send('NFC',s.replace('\n','<br>'))   #发送邮件
            print('*' * 80)
            detection = data2
 

