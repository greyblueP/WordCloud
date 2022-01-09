from random import sample
from typing import Counter
import requests
import time
import datetime
import urllib.request
import math
import jieba
from imageio import imread
from PIL import Image
from wordcloud import WordCloud, ImageColorGenerator
# 文件
import os
import re
import wordcloud


# 网页源码读取
def online(url):
    headers = {
        'Host': 'api.bilibili.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.56',
    }
    url = url
    req = urllib.request.Request(url=url, headers=headers)
    html = urllib.request.urlopen(req)  # 打开指定网址
    html = html.read()  # 读取网页源码
    html = html.decode('utf8')  # 解码
    return html


# 读取直播回放列表
# https://api.bilibili.com/x/series/archives?mid=2111566071&series_id=210610&only_normal=true&sort=desc&pn=1&ps=30
def list1(mid):
    url = 'https://api.bilibili.com/x/series/archives?mid=' + mid + \
        '&series_id=210610&only_normal=true&sort=desc&pn=1&ps=30'
    html = online(url)
    # 获取录播总数
    pat_0 = re.compile(r'"total":(.*?)},"archives"')
    pat0 = pat_0.findall(html)
    pages = math.ceil(int(pat0[0])/30)
    bvs = []
    titles = []
    for page in range(pages):
        url = 'https://api.bilibili.com/x/series/archives?mid=' + mid + \
            '&series_id=210610&only_normal=true&sort=desc&pn=' + \
            str(page+1)+'&ps=30'
        html = online(url)
        # BV号
        pat_1 = re.compile(r'"bvid":"(.*?)","ugc_pay":')
        pat1 = pat_1.findall(html)
        bvs += pat1
        # 视频标题
        pat_2 = re.compile(r'"title":"(.*?)","pubdate":')
        pat2 = pat_2.findall(html)
        titles += pat2
    return [bvs, titles]


# 读取视频弹幕
def list2(bvs, titles, time_begin, time_end):
    sum = 0
    wordcount = {}

    for i in range(len(bvs)):
        # for i in range(2):
        time.sleep(1.5)
        print('开始读取视频:['+str(i+1)+'/'+str(len(bvs))+']'+titles[i])
        # 获取cid
        bv = bvs[i]
        url = 'https://api.bilibili.com/x/web-interface/view?bvid='+bv
        html = online(url)
        pat_0 = re.compile(r'"cid":(.*?),"dimension"')
        pat0 = pat_0.findall(html)
        # 获取本视频时间
        pat_time = re.compile(r'"pubdate":(.*?),"ctime"')
        pattime = pat_time.findall(html)
        pattime = time.strftime(pattime, '%Y-%m-%d')
        pattime = time.strptime(pattime, '%Y-%m-%d')
        pattime = time.mktime(pattime)
        pattime = datetime.datetime.utcfromtimestamp(pattime)
        diffseconds_1 = (pattime-time_end).total_seconds()  # 大于零说明时间未到所需时间范围
        diffseconds_2 = (time_begin-pattime).total_seconds()  # 大于零说明时间已过所需时间范围
        if diffseconds_1 <= 0 and diffseconds_2 <= 0:
            # 获取弹幕表
            url = 'https://api.bilibili.com/x/v1/dm/list.so?oid='+pat0[0]
            html = requests.get(url)
            html.encoding = 'utf-8'
            html = html.text
            pat_1 = re.compile(r'">(.*?)</d><d ')
            pat1 = pat_1.findall(html)
            print('共读取到'+str(len(pat1))+'条弹幕')
            sum += len(pat1)

            # 切词
            pl = os.getcwd()+'\\stopwords'+'.txt'
            stopwords = open(pl, "r", encoding=('utf8')).read()  # 读取禁词
            txt = ''
            for j in range(len(pat1)):
                txt += pat1[j]+' '
            seg_list = jieba.cut(txt)  # 切词
            for word in seg_list:
                if word != '\t' and not len(word) == 1:
                    if not word in stopwords:
                        wordcount[word] = wordcount.get(word, 0)+1
        if diffseconds_2 > 0:
            break
    print('读取完毕，总计读取到'+str(sum)+'条弹幕')
    wordcloud(wordcount)

    # 保存到文件里
    file = open(os.getcwd()+'\\缓存.txt', 'w')
    for txt in wordcount:
        file.write(str(txt)+'*'+str(wordcount[txt])+'\n')
    file.close


# 读取缓存
def readsaves():
    file = open(os.getcwd()+'\\缓存.txt', 'r')
    sample = file.readlines()
    wordcount = {}
    for line in sample:
        line = line.rstrip('\n')
        sample_ = line.split('*')
        wordcount[sample_[0]] = int(sample_[1])
    file.close
    return wordcount


# 生成词云
def wordcloud(wordcount):
    wordcounts = sorted(wordcount.items(),
                        key=lambda x: x[1], reverse=True)  # 从大到小排序
    print(wordcounts[:10])
    # 防止差距过大
    if wordcounts[0][1] > wordcounts[1][1]*10:
        wordcount[wordcounts[0][0]] = wordcounts[1][1]*2
        wordcounts = sorted(wordcount.items(),
                            key=lambda x: x[1], reverse=True)  # 从大到小排序
        print('因第一条数据过大，修改为['+wordcounts[0][0]+':'+str(wordcounts[0][1])+']')

    t1 = time.perf_counter()
    print('开始生成词云')
    pl = os.getcwd()+'\\参考图'+'.png'
    fimg = pl
    c_mask = imread(fimg)
    image_colors = ImageColorGenerator(c_mask)
    wc = WordCloud(max_words=500,
                   font_path="./站酷快乐体2016修订版.ttf",
                   min_font_size=30,  # 字符大小范围
                   max_font_size=None,
                   font_step=6,  # 字号增加的步长
                   relative_scaling=0.4,  # 词条频数比例和字号大小比例的换算关系
                   prefer_horizontal=0.9,  # 词是否旋转90度
                   mask=c_mask,  # 词云使用的背景图（遮罩）
                   background_color="black",  # 图形背景色
                   color_func=(image_colors),
                   contour_width=1,
                   contour_color='black'
                   ).fit_words(wordcount)
    wc.to_file('词云.png')
    t2 = time.perf_counter()
    dt = format(t2-t1, '.2f')
    print('词云已生成,花费时间'+str(dt)+'秒')


def network():  # 从网络爬取
    # 输入mid
    mid = input('请输入uid:')
    if mid == '':
        mid = '2111566071'
        print('uid:', mid)

    # 记录视频时间范围
    time_begin = input('请输入开始记录的时间(格式:xxxx-xx-xx):')
    # strptime函数根据指定格式把一个时间字符串解析为时间元组
    time_begin = time.strptime(time_begin, '%Y-%m-%d')
    # mktime函数它接收struct_time对象作为参数，返回用秒数来表示时间的浮点数
    time_begin = time.mktime(time_begin)
    # utcfromtimestamp函数根据时间戳创建一个datetime对象,utc为格林威治时间
    time_begin = datetime.datetime.utcfromtimestamp(time_begin)

    time_end = input('请输入结束记录的时间(格式:xxxx-xx-xx):')
    time_end = time.strptime(time_end, '%Y-%m-%d')
    time_end = time.mktime(time_end)
    time_end = datetime.datetime.utcfromtimestamp(time_end)

    video = list1(mid)  # 读取视频列表
    list2(video[0], video[1], time_begin, time_end)  # 读取弹幕


def local():  # 从缓存生成
    wordcount = readsaves()
    wordcloud(wordcount)


# network()#网络爬取
local()  # 读取缓存
