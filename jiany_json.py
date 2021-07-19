import json
import time, srt, pinyin, re
from fuzzywuzzy import fuzz

def comp_sub(c, h):   #对比自动字幕和脚本字幕的匹配度，分数越高越匹配；c代表自动字幕，h代表脚本字幕
    global af_sub_h, af_sub_c   #声明为全局变量
    ch_num = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九', '0': '零'}
    af_h = re.sub(' ', "", re.sub(r'\W', "", re.sub(r'[(（]\w+[)）]', "", h)))
    # 去除脚本字幕中的中英文标点符号、圆括号中的备注内容、空格
    txt = c
    for n in ch_num:
        txt = txt.replace(n, ch_num[n])
    af_c = re.sub(' ', "", txt)  # 把自动字幕中的阿拉伯数字换成汉语数字，并去除自动字幕中的空格
    txt = af_h
    for n in ch_num:
        txt = txt.replace(n, ch_num[n])    # 把脚本字幕中的阿拉伯数字换成汉语数字
    # 转换成拼音后进行比对
    c_py = pinyin.get(af_c, '', "strip")
    h_py = pinyin.get(af_h, '', "strip")
    res = fuzz.token_set_ratio(c_py, h_py)
    af_sub_h = af_h    #处理后的脚本字幕传给全局变量，用于gen_sub中比较长度
    af_sub_c = af_c    #处理后的自动字幕传给全局变量，用于gen_sub中比较长度
    return res

def gen_sub(sub_c,sub_h):  #给字幕打轴,sub_c表示自动字幕列表,sub_h表示脚本字幕列表
    global af_sub_h, af_sub_c   #声明为全局变量
    dic_h={}   #用于记录所有脚本字幕的匹配评分
    dic_c={}   #用于记录所有自动字幕的匹配评分
    i = 0     #自动字幕序号（索引）
    res = 0
    res2 = 0
    sub_i=0   #脚本字幕序号（索引）

    while (i < len(sub_c) and sub_i < len(sub_h)):  #只要不到最后一条脚本字幕和最后一条自动字幕就一直循环
        res=comp_sub(sub_c.__getitem__(i).content,sub_h[sub_i])
        if(res>score_1):   #如果匹配度大于score_1则直接将脚本字幕复制给自动字幕
            sub_c.__getitem__(i).content=sub_h[sub_i]
        elif((len(af_sub_c)>len(af_sub_h)) and sub_i+1<len(sub_h)): #如果自动字幕比脚本字幕长，且当前脚本字幕不是最后一条，则将下一个脚本字幕加入对比
            sub_stdc=sub_c.__getitem__(i).content  #对比用的自动字幕
            sub_tmp=sub_h[sub_i]
            dic_h[sub_i]=res  #保存第一次匹配的分数，为了方便匹配分数和相应的脚本字幕能一一对应上，我们把sub_i作为字典的key
            sub_i_bgn = sub_i   #记住此次匹配时的第一个脚本字幕序号
            res2 = comp_sub(sub_stdc,sub_tmp.strip()+sub_h[sub_i+1]) #将当前和下一行的脚本字幕结合在一起后与自动字幕进行匹配
            if (res2>=res): #如果联合下一个脚本字幕一起比对后匹配度更高，则执行以下程序
                while (res2>=res): #如果联合下一个脚本字幕一起比对后匹配度更高，则继续结合下一个脚本字幕比对，直至匹配度降低
                    sub_tmp = sub_tmp.strip() + sub_h[sub_i + 1]
                    sub_i += 1
                    res=res2                         #应该再加一个判断i+1是否大于len(sub_c)
                    dic_h[sub_i] = res
                    if(sub_i+1<len(sub_h)):   #如果sub_i+1不是最后一条脚本字幕
                        res2=comp_sub(sub_stdc,sub_tmp.strip()+sub_h[sub_i+1])
                    else:
                        break    #如果已经匹配过最后一条脚本字幕则跳出while循环
                if (res>score_2):  #将匹配度最高，且大于score_2分的脚本字幕赋值给自动字幕
                    sub_c.__getitem__(i).content = sub_tmp
                else:    #如果匹配度最高的得分低于score_2，则回退至一开始比对的脚本字幕
                    sub_i=sub_i_bgn
                    sub_c.__getitem__(i).content = sub_h[sub_i]
            else:   #如果联合下一个脚本字幕一起和当前自动字幕比对匹配度反而更低，则直接将当前脚本字幕赋值给自动字幕
                sub_c.__getitem__(i).content = sub_h[sub_i]
        elif((len(af_sub_c)<len(af_sub_h)) and i+1<len(sub_c)):   #如果脚本字幕比自动字幕长，且自动字幕不是最后一条字幕，则将下一个自动字幕加入对比
            sub_stdh=sub_h[sub_i]     #比对用的脚本字幕
            sub_tmp=sub_c.__getitem__(i).content
            i_bgn=i
            dic_c[i] = res  #保存第一次匹配的分数，使用字典类型记录匹配的分数，为了便于与自动字幕一一对应，使用i作为字典的key
            res2=comp_sub(sub_tmp+sub_c.__getitem__(i+1).content,sub_stdh)
            if(res2>=res): #如果结合下一个自动字幕一起比对后匹配度更高，则执行以下程序
                while (res2>=res): #如果联合下一个自动字幕一起比对后匹配度更高，则继续结合下一个脚本字幕比对，直至匹配度降低
                    sub_tmp=sub_tmp+sub_c.__getitem__(i+1).content
                    i += 1
                    res=res2
                    dic_c[i] = res
                    if (i + 1 < len(sub_c)):  #如果i+1不是最后一条自动字幕
                        res2=comp_sub(sub_tmp+sub_c.__getitem__(i+1).content,sub_stdh)
                    else:
                        break   #如果已到最后一条自动字幕则跳出while循环
                if(res>score_2):   #将匹配度最高的自动字幕的结束时间赋值给刚开始的自动字幕结束时间
                    sub_c.__getitem__(i_bgn).content = sub_stdh
                    sub_c.__getitem__(i_bgn).end =sub_c.__getitem__(i).end
                    dn=i
                    while (dn>i_bgn):
                        ttt = sub_c.__getitem__(dn).content
                        sub_c.__delitem__(dn)  #删除匹配过的自动字幕
                        dn -= 1
                    i = i_bgn  # 回归i计数，结合最后的i加1一起理解
                else:   # 如果匹配度最高的得分低于score_2，则回退至一开始比对的自动字幕
                    sub_c.__getitem__(i_bgn).content = sub_stdh
                    i = i_bgn  # 回归i计数，结合最后的i加1一起理解
            else:   # 如果联合下一个自动字幕一起和当前脚本字幕比对匹配度反而更低，则直接将当前脚本字幕赋值给自动字幕
                sub_c.__getitem__(i).content = sub_h[sub_i]
        else:  # 以上情况都不是，直接将脚本字幕覆盖自动字幕
            sub_c.__getitem__(i).content = sub_h[sub_i]
        i += 1      # 自动字幕序号加一，读取下一条自动字幕
        sub_i += 1   # 脚本字幕序号加一，读取下一条脚本字幕
        af_sub_h=""
        af_sub_c=""
        res=0
        res2=0
    with open(sub_path,'w+',encoding='utf-8') as sub_file:
        sub_file.writelines(srt.compose(sub_c))  # 生成打轴后的字幕

def get_sub_jiany():
    content = []    # 剪映产生的字幕内容
    subtitle = []   # 打轴过的字幕
    start = []     # 当前字幕开始时间
    duration = []  # 当前字幕持续时间
    ind = 0     # 字幕序号
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            subs = json.load(json_file)
            for i in subs['materials']['texts']:
                content.append(i['content'])
            for i in subs['tracks'][1]['segments']:
                start.append(i['target_timerange']['start'])
                duration.append(i['target_timerange']['duration'])
    except FileNotFoundError:
        print("\n请将C:/Users/USER/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft目录下的draft.json文件拷贝到当前目录！")
        return subtitle

    while ind < len(content):
        start_hhmmss = time.strftime('%H:%M:%S', time.gmtime(start[ind] // 1000000))  #剪映的起始时间整除一百万，得到相应的秒数，再利用time库将其转换为小时分钟秒钟
        start_ms = str(start[ind] // 1000 % 1000)   #剪映时间除以一百万的余数即为毫秒数
        start_tl = start_hhmmss + "," + start_ms   #拼接成字幕的起始时间
        end_hhmmss = time.strftime('%H:%M:%S', time.gmtime((start[ind]+duration[ind]) // 1000000))
        end_ms = str((start[ind]+duration[ind])//1000 % 1000)
        end_tl = end_hhmmss + "," + end_ms
        #使用srt库将字幕索引、起止时间、字幕内容拼装在一起
        subtitle.append(srt.Subtitle(index=ind,start=srt.srt_timestamp_to_timedelta(start_tl),
                                 end=srt.srt_timestamp_to_timedelta(end_tl), content=str(srt.make_legal_content(content[ind]))))
        print("start_real:",start_tl)
        print("content:",content[ind])
        print("end_real:",end_tl)
        ind += 1
    with open(jy_sub_path,'w+',encoding='utf-8') as jiany_file:  # 将剪映字幕导出成srt字幕
        jiany_file.writelines(srt.compose(subtitle))
    return subtitle

if __name__ == '__main__':
    json_path = './draft.json'  #剪映产生的json文件
    jy_sub_path = './jianying_sub.srt'
    hsub_path = './hand_sub.txt' #脚本字幕
    sub_path = './sub.srt'       #打轴后的字幕
    score_1 = 95  #第一次匹配的分数；分数越高对匹配度要求越高
    score_2 = 0  #结合下一行字幕一起匹配的分数；
    af_sub_c = ""   #预处理过的自动字幕字符串
    af_sub_h = ""   #预处理过的脚本字幕字符串

    subsc = get_sub_jiany()  # 获取剪映字幕
    if len(subsc) > 0:
        try:
            with open(hsub_path, 'r', encoding='utf-8') as subt: #打开脚本字幕
                subsh = subt.readlines()
            gen_sub(subsc, subsh)  # 给脚本字幕自动打轴
            print("\n剪映字幕和打轴字幕均已产生！\n ")
        except FileNotFoundError:
            print("\n剪映字幕已产生！\n ")