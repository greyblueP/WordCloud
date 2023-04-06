import requests
import time
import math
import json
import jieba
from imageio import imread
from wordcloud import WordCloud, ImageColorGenerator
from PIL import ImageFont
import xmltodict
import os
import re


headers = {
    # 'Host': 'api.bilibili.com',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
}


# 网页源码读取
def online(url):
    url = url
    text = requests.get(url, headers=headers).text
    data = json.loads(text)
    return data


# 获取录播列表
def Get_series_list(mid: int):
    url = f"https://api.bilibili.com/x/polymer/space/seasons_series_list?mid={mid}&page_num=1&page_size=20"
    data = online(url)
    series_id = data["data"]["items_lists"]["series_list"][0]["meta"]["series_id"]
    # 获取录播总数
    Num = data["data"]["items_lists"]["series_list"][0]["meta"]["total"]
    pages = math.ceil(Num / 20)
    # 获取录播时间，BV号，名字
    series_list = []
    for page in range(pages):
        url = f"https://api.bilibili.com/x/series/archives?mid={mid}&series_id={series_id}&only_normal=true&sort=desc&pn={page+1}&ps=30"
        data = online(url)
        for i in data["data"]["archives"]:
            try:
                # #将时间戳pubdate转化为时间
                # pubdate = time.strftime("%Y-%m-%d %H-%M", time.localtime(i['pubdate']))
                # 去除title里不能作为文件名字的部分
                title = re.sub(r"[\/\\\:\*\?\"\<\>\|]", "", i["title"])
                series_list.append([i["pubdate"], i["bvid"], title])
            except:
                break
    print(f"录播列表已获取,共{len(series_list)}个录播")
    # 存到 录播列表.json 文件里
    with open(f"./{mid}弹幕/录播列表{mid}.json", "w", encoding="utf-8") as f:
        json.dump(series_list, f, ensure_ascii=False, indent=4)
    print(f"录播列表已保存到 录播列表{mid}.json 文件里")
    return series_list


# 读取录播弹幕
def Get_danmu(pubdata: int, bvid: str, title: str):
    # 获取cid
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    data = online(url)
    oid = data["data"]["cid"]
    pid = data["data"]["aid"]
    danmaku = data["data"]["stat"]["danmaku"]
    # 获取弹幕
    pat = []
    if danmaku <= 9400:
        url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={oid}"
        res = requests.get(url, headers=headers)
        res.encoding = "utf-8"
        pat = []
        # 解析xml
        for row in xmltodict.parse(res.text)["i"]["d"]:
            text = row["#text"]
            pat.append(text)
    else:
        segment_index = 1
        while True:
            url = f"https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={oid}&pid={pid}&segment_index={segment_index}"
            res = requests.get(url, headers=headers)
            res.encoding = "utf-8"
            text = res.text
            if text == "":
                break
            # 解析
            pattern = re.compile(r"\w{8}:[^\u4e00-\u9fa5](.*?)@")
            # 匹配
            match = pattern.findall(text)
            for i in match:
                if match:
                    pat.append(i)
            segment_index += 1

    # 写入文件
    with open(f"./{mid}弹幕/{pubdata}{title}.txt", "w", encoding="utf-8") as f:
        for i in pat:
            f.write(i + "\n")
        print(f"[{pubdata}]{title},{len(pat)}条弹幕已保存")


# 读取缓存列表
def Read_series_list(mid: int):
    with open(f"./{mid}弹幕/录播列表{mid}.json", "r", encoding="utf-8") as f:
        old_series_list = json.load(f)
    return old_series_list


# 获取视频弹幕
def Get_All_danmu(mid: int):
    # 读取缓存
    try:
        old_series_list = Read_series_list(mid)
        print("已读取缓存列表")
    except:
        old_series_list = []
        print("未找到缓存列表")
    # 获取录播列表
    series_list = Get_series_list(mid)
    # 去除重复录播
    for i in old_series_list:
        for j in series_list:
            if i[1] == j[1]:
                series_list.remove(j)
    print(f"排除已有录播,共{len(series_list)}个录播需要下载")
    if len(series_list) > 0:
        print("开始下载")
        # 获取弹幕
        for i in series_list:
            Get_danmu(i[0], i[1], i[2])
            # time.sleep(1)


# ————————————————————————————————————————————————————————


# 生成词云
def Get_wordcloud(mid: int, starttime: int, endtime: int):
    # 读取缓存列表
    try:
        old_series_list = Read_series_list(mid)
        print("已读取缓存列表")
    except:
        print("未找到缓存列表，是否获取弹幕？")
        if input("y/n:").lower() == "y":
            Get_All_danmu(mid)
            old_series_list = Read_series_list(mid)
        else:
            return
    # 去除列表中在时间范围外的部分
    series_list = []
    for i in old_series_list:
        time = i[0]
        if time >= starttime and time <= endtime:
            series_list.append(i)
    # 读取弹幕
    danmu = ""
    Num = 0
    for i in series_list:
        try:
            pubdata = i[0]
            title = i[2]
            with open(f"./{mid}弹幕/{pubdata}{title}.txt", "r", encoding="utf-8") as f:
                # 逐行读取
                for line in f.readlines():
                    # 去除'\n'
                    line = line.strip("\n")
                    danmu += line + " "
                    Num += 1
        except:
            pass
    try:
        stopwords = open(f"./stopwords.txt", "r", encoding=("utf8")).read()
    except:
        # 创建文件
        with open(f"./stopwords.txt", "w", encoding=("utf8")) as f:
            f.write(" ")
        stopwords = open(f"./stopwords.txt", "r", encoding=("utf8")).read()
    # 切词
    wordcount = {}
    danmu = jieba.cut(danmu)
    for i in danmu:
        if len(i) > 1:
            if i not in stopwords:
                wordcount[i] = wordcount.get(i, 0) + 1
    # 整数转化为日期
    starttime = timestamp_to_date(starttime)
    endtime = timestamp_to_date(endtime)
    print("你选择时间范围为:", starttime, "至", endtime)
    print("时间范围内共有", len(series_list), "个文件")
    print(f"共{Num}条弹幕")
    # 对wordcount排序
    wordcount_ = sorted(wordcount.items(), key=lambda x: x[1], reverse=True)
    # 一行多个地输出前100个词及词频
    print("\n排名前20的词及词频:")
    for i in range(20):
        print("" * 4, wordcount_[i][0], wordcount_[i][1])
    # 生成词云
    # 判断是否存在文件叫'参考图.jpg'
    try:
        fimg = "./参考图.jpg"
        c_mask = imread(fimg)
    except:
        print('未找到"参考图.jpg",词云生成失败')
        return
    # 检查是否存在字体'站酷快乐体2016修订版.ttf'
    try:
        font_path = "站酷快乐体2016修订版.ttf"
        font = ImageFont.truetype(font_path, 20)
    except:
        font_path = "simhei.ttf"
    print("\n开始生成词云")
    image_colors = ImageColorGenerator(c_mask)
    wc = WordCloud(
        # 词的处理
        font_path=font_path,  # 字体路径
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
    wc.to_file("词云.png")
    print("词云已保存到 词云.png 文件里")


# ————————————————————————————————————————————————————————


# 弹幕查询
def Search_danmu(mid: int, starttime: int, endtime: int):
    # 读取缓存列表
    try:
        old_series_list = Read_series_list(mid)
        print("已读取缓存列表")
    except:
        print("未找到缓存列表，是否获取弹幕？")
        if input("y/n:").lower() == "y":
            Get_All_danmu(mid)
            old_series_list = Read_series_list(mid)
        else:
            return
    # 去除列表中在时间范围外的部分
    series_list = []
    for i in old_series_list:
        time = i[0]
        if time >= starttime and time <= endtime:
            series_list.append(i)
    # 读取弹幕
    danmu_list = {}
    for i in series_list:
        try:
            pubdata = i[0]
            title = i[2]
            with open(f"./{mid}弹幕/{pubdata}{title}.txt", "r", encoding="utf-8") as f:
                danmu_list[f"[{pubdata}]{title}"] = []
                # 逐行读取
                for line in f.readlines():
                    # 去除'\n'
                    line = line.strip("\n")
                    danmu_list[f"[{pubdata}]{title}"].append(line)
        except:
            pass
    # 时间戳转化为日期
    starttime = timestamp_to_date(starttime)
    endtime = timestamp_to_date(endtime)
    print("你选择时间范围为:", starttime, "至", endtime)
    print("时间范围内共有", len(series_list), "个文件")
    # 查询弹幕
    while True:
        danmu = input("请输入要查询的弹幕(直接回车则返回上一级):")
        if danmu == "":
            os.system("cls")
            break
        Back_list = {}
        for i in danmu_list:
            Back_list[i] = []
            # 模糊搜素
            for danmus in danmu_list[i]:
                if danmu in danmus:
                    Back_list[i].append(danmus)
        for i in list(Back_list.keys()):
            if Back_list[i] == []:
                Back_list.pop(i)
        print("\n查询结果:")
        print(f"查询到{len(Back_list)}个文件中存在此弹幕")
        for i in Back_list:
            print(f"{i}:")
            print(" " * 2, Back_list[i], "\n")
        input("按回车键继续")
        os.system("cls")


# ————————————————————————————————————————————————————————


def choicetime():
    # 是否选择时间范围
    whilechoice = input("是否选择时间范围(y/n):")
    if whilechoice.lower() == "y":
        # 开始时间
        starttime = input("请输入开始时间(格式:20200101):")
        while True:
            if re.match(r"\d{4}\d{2}\d{2}", starttime):
                break
            print("时间格式错误")
            starttime = input("请输入开始时间(格式:20200101):")
        # 结束时间
        endtime = input("请输入结束时间(格式:20200101):")
        while True:
            if re.match(r"\d{4}\d{2}\d{2}", endtime):
                break
            print("时间格式错误")
            endtime = input("请输入结束时间(格式:20200101):")
        # 转换为时间戳
        starttime = time.mktime(time.strptime(starttime, "%Y%m%d"))
        endtime = time.mktime(time.strptime(endtime, "%Y%m%d"))
        # 判断时间大小
        if starttime > endtime:
            starttime, endtime = endtime, starttime
    else:
        starttime = 0
        endtime = int(time.time())
    return starttime, endtime


# 时间戳转化为日期
def timestamp_to_date(timestamp):
    timeArray = time.localtime(timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d", timeArray)
    return otherStyleTime


while True:
    mid = input("请输入up主的uid:")
    # 去除mid里的非数字
    mid = "".join(re.findall(r"\d", mid))
    if mid != "":
        break
    print("未输入uid\n")
# mid=1792034157
# 创建文件夹
if not os.path.exists(f"{mid}弹幕"):
    os.mkdir(f"{mid}弹幕")
while True:
    os.system("cls")
    # 请选择功能
    print("请选择功能:")
    print("1.获取弹幕" + "\n" + "2.生成词云" + "\n" + "3.弹幕查询")
    choice = input("请输入数字(直接回车则退出):")
    os.system("cls")
    if choice == "2" or choice == "3":
        starttime, endtime = choicetime()
        os.system("cls")
    if choice == "1":
        Get_All_danmu(mid)
        input("按回车键返回上一级")
    elif choice == "2":
        Get_wordcloud(mid, starttime, endtime)
        input("按回车键返回上一级")
    elif choice == "3":
        Search_danmu(mid, starttime, endtime)
    else:
        break
