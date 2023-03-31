import requests
import time
import math
import json
import jieba
from imageio import imread
from wordcloud import WordCloud, ImageColorGenerator
# 文件
import os
import re

headers = {
    'Host': 'api.bilibili.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54',
}


# 网页源码读取
def online(url):
    url = url
    text=requests.get(url,headers=headers).text
    data=json.loads(text)
    return data


#获取录播列表
def Get_series_list(mid):
    url = f'https://api.bilibili.com/x/polymer/space/seasons_series_list?mid={mid}&page_num=1&page_size=20'
    data = online(url)
    series_id=data['data']['items_lists']['series_list'][0]['meta']['series_id']
    # 获取录播总数
    Num=data['data']['items_lists']['series_list'][0]['meta']['total']
    pages = math.ceil(Num/20)
    #获取录播时间，BV号，名字
    series_list=[]
    for page in range(pages):
        url=f'https://api.bilibili.com/x/series/archives?mid={mid}&series_id={series_id}&only_normal=true&sort=desc&pn={page+1}&ps=30'
        data = online(url)
        for i in data['data']['archives']:
            try:
                #将时间戳pubdate转化为时间
                pubdate = time.strftime("%Y-%m-%d %H-%M", time.localtime(i['pubdate']))
                #去除title里不能作为文件名字的部分
                title = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '', i['title'])
                series_list.append([pubdate,i['bvid'],title])
            except:
                break
    print(f'录播列表已获取,共{len(series_list)}个录播')
    #存到 录播列表.json 文件里
    with open(f'{Path}\\录播列表{mid}.json','w',encoding='utf-8') as f:
        json.dump(series_list,f,ensure_ascii=False,indent=4)
    print(f'录播列表已保存到 录播列表{mid}.json 文件里')
    return series_list


#读取录播弹幕
def Get_danmu(pubdata,bvid,title):
    #获取cid
    url=f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    data = online(url)
    cid=data['data']['cid']
    #获取弹幕
    url=f'https://api.bilibili.com/x/v1/dm/list.so?oid={cid}'
    text=requests.get(url=url,headers=headers)
    text.encoding = 'utf-8'
    text=text.text
    pat_ = re.compile(r'">(.*?)</d><d ')
    pat = pat_.findall(text)
    #写入文件
    with open(f'{Path}\\[{pubdata}]{title}.txt','w',encoding='utf-8') as f:
        for i in pat:
            f.write(i+'\n')
        print(f'[{pubdata}]{title}弹幕已保存')


#读取缓存
def Read_series_list(mid):
    with open(f'{Path}\\录播列表{mid}.json','r',encoding='utf-8') as f:
        old_series_list=json.load(f)
    return old_series_list


#获取视频弹幕
def Get_All_danmu(mid):
    #读取缓存
    try:
        old_series_list=Read_series_list(mid)
        print('已读取缓存')
    except:
        old_series_list=[]
        print('未找到缓存')
    #获取录播列表
    series_list=Get_series_list(mid)
    #去除重复录播
    if 'old_series_list' in locals():
        series_list=[i for i in series_list if i not in old_series_list]
        print('开始下载弹幕')
    #获取弹幕
    for i in series_list:
        Get_danmu(i[0],i[1],i[2])

#————————————————————————————————————————————————————————

#生成词云
def Get_wordcloud(mid):
    #读取缓存
    try:
        old_series_list=Read_series_list(mid)
        print('\n已读取缓存')
    except:
        print('\n未找到缓存，是否获取弹幕？')
        if input('y/n:').lower()=='y':
            Get_All_danmu(mid)
            old_series_list=Read_series_list(mid)
        else:
            return
    #读取弹幕
    danmu=''
    for i in old_series_list:
        try:
            pubdata=i[0]
            title=i[2]
            with open(f'{Path}\\[{pubdata}]{title}.txt','r',encoding='utf-8') as f:
                #逐行读取
                for line in f.readlines():
                    #去除'\n'
                    line=line.strip('\n')
                    danmu+=line+' '
        except:
            pass
    stopwords = open(f'{os.getcwd()}\\stopwords.txt', "r", encoding=('utf8')).read()
    #切词
    wordcount = {}
    danmu = jieba.cut(danmu)
    for i in danmu:
        if len(i) > 1:
            if i not in stopwords:
                wordcount[i] = wordcount.get(i, 0) + 1
    #生成词云
    print('开始生成词云')
    fimg = os.getcwd()+'\\参考图.jpg'
    c_mask = imread(fimg)
    image_colors = ImageColorGenerator(c_mask)
    wc = WordCloud(
        # 词的处理
        font_path="站酷快乐体2016修订版.ttf",
        max_words=1000,  # 要显示的词的最大个数
        min_font_size=1,  # 显示的最小的字体大小
        font_step=2,  # 字号增加的步长
        relative_scaling=0.1,  # 词条频数比例和字号大小比例的换算关系
        prefer_horizontal=1,  # 词语水平方向排版出现的频率
        # 颜色与形状
        mask=c_mask,
        background_color="black",  # 背景颜色
        color_func=(image_colors),  # 按图上色
        # color_func=color_func,
        scale=10,  # 按照比例进行放大画布
            ).fit_words(wordcount)
    wc.to_file('词云.png')

#————————————————————————————————————————————————————————

#弹幕查询
def Search_danmu(mid):
    #读取缓存
    try:
        old_series_list=Read_series_list(mid)
        print('\n已读取缓存')
    except:
        print('\n未找到缓存，是否获取弹幕？')
        if input('y/n:').lower()=='y':
            Get_All_danmu(mid)
            old_series_list=Read_series_list(mid)
        else:
            return
    #读取弹幕
    danmu_list={}
    for i in old_series_list:
        try:
            pubdata=i[0]
            title=i[2]
            with open(f'{Path}\\[{pubdata}]{title}.txt','r',encoding='utf-8') as f:
                danmu_list[f'[{pubdata}]{title}']=[]
                #逐行读取
                for line in f.readlines():
                    #去除'\n'
                    line=line.strip('\n')
                    danmu_list[f'[{pubdata}]{title}'].append(line)
        except:
            pass
    #查询弹幕
    while True:
        danmu=input('\n请输入要查询的弹幕(直接回车则返回上一级):')
        if danmu=='':
            break
        Back_list={}
        for i in danmu_list:
            Back_list[i]=[]
            #模糊搜素
            for danmus in danmu_list[i]:
                if danmu in danmus:
                    Back_list[i].append(danmus)
        for i in list(Back_list.keys()):
            if Back_list[i]==[]:
                Back_list.pop(i)
        print('\n查询结果:')
        print(f'查询到{len(Back_list)}个文件中存在此弹幕')
        for i in Back_list:
            print(f'{i}:')
            print(' '*2,Back_list[i],'\n')




mid=input('请输入up主的uid:')
#去除非数字
mid = re.sub(r'\D', '', mid)
#创建文件夹
if not os.path.exists(f'{mid}弹幕'):
    os.mkdir(f'{mid}弹幕')
Path=os.getcwd()+f'\\{mid}弹幕'
while True:
    #请选择功能
    print('\n请选择功能:')
    print('1.获取弹幕'+'\n'+'2.生成词云'+'\n'+'3.弹幕查询')
    choice=input('请输入数字:')
    if choice=='1':
        Get_All_danmu(mid)
    elif choice=='2':
        Get_wordcloud(mid)
    elif choice=='3':
        Search_danmu(mid)
    print('完成\n')
