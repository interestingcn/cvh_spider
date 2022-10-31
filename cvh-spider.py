import time,requests,csv,os
from multiprocessing import Pool
'''
CVH - Spider
中国数字植物标本馆(www.cvh.ac.cn) 
信息聚合检索输出工具

华南农业大学生物信息学实验室 Scau - Bioinformatics Lab
LastUpdate： 2022.10.29
Author：wangzt
Github：https://github.com/interestingcn/cvh_spider
'''
def welcome():
    msg = '''   

   ___   __   __  _  _             ___     _ __     _        _                   
  / __|  \ \ / / | || |    ___    / __|   | '_ \   (_)    __| |    ___      _ _  
 | (__    \ V /  | __ |   |___|   \__ \   | .__/   | |   / _` |   / -_)    | '_| 
  \___|   _\_/_  |_||_|   _____   |___/   |_|__   _|_|_  \__,_|   \___|   _|_|_  
_|"""""|_| """"|_|"""""|_|     |_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""| 
"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-' 

                        [ 中国数字植物标本馆快速检索工具 ]     
                           华南农业大学生物信息学实验室                         
=========================================================================================     
    '''
    print(msg)

# Unified information output interface
def displayMsg(msg='',workname='Default'):
    now = time.asctime( time.localtime(time.time()) )
    print(f'{now} - {workname}: ' + msg)

def get(url):
    header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81",
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://www.cvh.ac.cn/spms/list.php',
            }
    proxies = {
        "https": "127.0.0.1:4780"
    }
    requests.packages.urllib3.disable_warnings()
    attempts = 0
    success = False
    while attempts <= 6 and not success:
        try:
            request = requests.get(url, headers=header, proxies=None, timeout=8, verify = False)
            success = True
            return request
        except:
            attempts += 1
            if int(attempts) <= 5:
                time.sleep(3)
                continue
            if attempts > 5:
                return False
    return False

def formatTime(string):
    if str(string).strip() != '' and string != None and str(string).lower() != 'none':
        return f'{string[:4]}年{string[4:6]}月{string[6:8]}日'
    else:
        return string

def formatNull(string):
    if string == '' or string == None or str(string).lower() == 'none':
        return str('N/A')
    else:
        return string

def get_item_info(input_keyword,page_offset):
    data = list()
    if page_offset == 0:
        url = f'https://www.cvh.ac.cn/controller/spms/list.php?&taxonName={input_keyword}'
    else:
        url = f'https://www.cvh.ac.cn/controller/spms/list.php?&taxonName={input_keyword}&offset={int(page_offset)}'

    displayMsg('正在检索页面信息：' + url,os.getpid())
    page_info = get(url).json()

    for line_info in page_info['rows']:
        collection_id = line_info['collectionID']
        item_url = f'https://www.cvh.ac.cn/controller/spms/detail.php?id={collection_id}'

        try:
            item_info = get(item_url).json()['rows']
        except:
            print('[Error] :')
            print(url)
            print(item_url)
            print(item_info)
            exit()
        # 馆藏编号
        gcbh = line_info['institutionCode'] + ' ' + line_info['collectionCode']
        # 学名
        xm = formatNull(line_info['canonicalName'])
        # 中文名
        zwm = formatNull(line_info['chineseName'])
        # 采集人
        cjr = formatNull(line_info['recordedBy'])
        # 采集号
        cjh = formatNull(line_info['recordNumber'])
        # 采集国家
        cjgj = formatNull(line_info['country'])
        # 采集省份
        cjsf = formatNull(line_info['stateProvince'])
        # 采集年份
        cjnf = formatNull(line_info['year'])
        # 采集时间
        cjsj = formatNull(formatTime(item_info['verbatimEventDate']))
        # 鉴定人
        jdr = formatNull(item_info['identifiedBy'])
        # 鉴定时间
        jdsj = formatNull(formatTime(item_info['verbatimEventDate']))
        # 海拔
        hb = formatNull(item_info['elevation'])
        # 生境
        sj = formatNull(item_info['habitat'])
        # 习性
        xx = formatNull(item_info['occurrenceRemarks'])
        # 物候期
        whq = formatNull(item_info['reproductiveCondition'])
        # 馆藏地
        gcd = formatNull(item_info['institution'])
        # 本页链接地址
        link = 'https://www.cvh.ac.cn/spms/detail.php?id='+ str(collection_id)
        data.append([gcbh, xm, zwm, cjr, cjh, cjgj, cjsf, cjnf, cjsj, jdr, jdsj, hb, sj, xx, whq, gcd, link])
    return data


if __name__ == '__main__':
    welcome()
    start_time = time.time()
    # input_keyword = 'Camellia'
    input_keyword = input('请输入需要搜索的关键字： ')
    displayMsg('当前检索内容：' + input_keyword)
    search_res = get(f'https://www.cvh.ac.cn/controller/spms/list.php?&taxonName={input_keyword}').json()
    total_num = search_res['total']
    displayMsg('存在相关内容数量：' + str(total_num))

    if total_num / 30 > total_num // 30:
        max_num =(total_num//30) + 1
    else:
        max_num = int(total_num / 30)
    # offset偏移量生成器
    offset_list = (i*30 for i in range(0,max_num))

    data = list()

    p = Pool(20)
    for page_offset in offset_list:
        res = p.apply_async(get_item_info, args=(input_keyword,page_offset,))
        data.append(res)
    p.close()
    p.join()

    l = list()
    for i in data:
        if i.get() != False:
            l += i.get()

    displayMsg('正在将结果保存到文件：' + input_keyword + '.csv' )
    with open(input_keyword + '.csv','w',encoding='utf-8-sig',newline='') as file:
        write = csv.writer(file)
        write.writerow(['馆藏编号','学名','中文名','采集人','采集号','采集国家','采集省份','采集年份','采集时间','鉴定人','鉴定时间','海拔','生境','习性','物候期','馆藏地','链接'])
        write.writerows(l)
    use_time = time.time() - start_time

    displayMsg('检索结果数目: ' + str(len(l)))
    displayMsg('本次任务耗时: ' + str(use_time))
    displayMsg('任务结束!')