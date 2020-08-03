import os
import time
import requests
import re
import json
from lxml import etree
from urllib import parse


class bilibili():
    def __init__(self):
        #设置请求网页时的头部信息
        self.getHtmlHeaders={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q = 0.9'
        }
        #设置请求视频资源时的头部信息
        self.downloadVideoHeaders={
            'Origin': 'https://www.bilibili.com',
            'Referer': 'https://www.bilibili.com/video/av26522634',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        }
        self.domain = "https://www.bilibili.com/video/"

    '''url拼接得到所有需要的url，装在list中返回'''
    def getRight_urls(self,fanhao):
        url = parse.urljoin(self.domain,fanhao)
        # print(url)
        json_url ='https://api.bilibili.com/x/player/pagelist?bvid='+fanhao+'&jsonp=jsonp'
        # print(json_url)
        try:
            res = requests.get(url = json_url,headers=self.getHtmlHeaders)
            info_list = json.loads(res.text)['data']
            url_list = []
            for item in info_list:
                url_dict = {}
                if len(item) > 1:
                    url_dict['name'] = str(item['page']) +'--'+ item['part']
                elif len(item) < 1:
                    url_dict['name'] = item['part']
                num = item['page']
                url_dict['next_url'] = url + '?p={num}'.format(num=num)
                url_list.append(url_dict)
        except requests.RequestException:
            print("该资源可能为av开头或者过于老旧！")
        # for item in url_list:
        #     print(item)
        return url_list

    '''每个url请求所得到得返回数据，装在list中返回'''
    def getHtml(self,url_list):
        res_list = []
        for item in url_list:
            # print(item)
            res_dict = {}
            url = item['next_url']
            try:
                response = requests.get(url=url, headers= self.getHtmlHeaders)
                if response.status_code == 200:
                    res_dict['response'] = response.text
            except requests.RequestException:
                print('请求Html错误:')
            res_dict['name'] = item['name']
            res_list.append(res_dict)
        # for item in res_list:
        #     print(item)
        return res_list

    '''解析页面并得到想要的数据，将得到的数据装在list中返回'''
    def parseHtml(self,res_list):
        #方法一：用pq解析得到视频标题
        # doc = pq(html)
        # video_title = doc('#viewbox_report > h1 > span').text()

        #方法二：用etree加xpath解析页面和获取标题
        video_list = []
        for item in res_list:
            video_dict = {}
            html=item['response']
            doc = etree.HTML(html)
            video_dict['title'] = doc.xpath("//div[@id='viewbox_report']/h1/span/text()")[0]
            # 调试输出结果
            # print(doc)
            # print(video_dict['title'])

            #用正则、json得到视频url;用pq失败后的无奈之举
            #根据页面中的代码书写正则表达式
            pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
            #根据正则表达式在页面中提取对应字典，实践证明获取的两个结果相同，取第一个结果即可
            result = re.findall(pattern, html)[0]
            #将获取的字典转化为json格式
            temp = json.loads(result)
            #打印temp查看结果
            # print(temp)

            #av开头的链接和Bv开头的链接得到的json字段不一致
            #av开头字段为['data']['durl']，Bv开头字段为['data']['dash']['video']
            try:
                #字段为['data']['dash']['video']则是Bv开头，取baseUrl的值
                dict1= temp['data']['dash']['video'][0]
                dict2= temp['data']['dash']['audio'][0]
                # print(dict1)
                if 'baseUrl' in dict1.keys() :
                    video_dict['video_url'] = dict1['baseUrl']
                if 'baseUrl' in dict2.keys() :
                    video_dict['audio_url'] = dict2['baseUrl']
            #字段为['data']['durl']则是av开头，取url的值
            except:
                print("ERROR!")
            video_dict['name'] = item['name']
            video_list.append(video_dict)
        return video_list

    '''定义视频下载的方法'''
    def download_video(self,video_list):
        for item in video_list:
            # print(item)
            # 去掉创建文件时的非法字符
            title1 = re.sub(r'[\/:*?"<>|]', '-', item['title'])
            title = title1.replace(" ", "")
            video_url = item['video_url']
            #拼接文件名
            name1 = re.sub(r'[\/:*?"<>|]', '-', item['name'])
            name = name1.replace("&", "and")
            filename = name + '.mp4'
            #视频请求下载地址
            r = requests.get(url=video_url, stream=True, headers=self.downloadVideoHeaders)
            #根据请求页面的response headers得到content-length，也就是文件的总bit大小
            length = float(r.headers['content-length'])
            count = 0
            count_tmp = 0
            time1 = time.time()
            start_time = time.time()
            print('[Start download]:{filename},[File size]:{size:.2f} MB'.format(filename=filename,size=length / 1024 / 1024))  # 开始下载，显示下载文件大小
            path = r'E:\{dir_title}'.format(dir_title=title)
            if not os.path.exists(path):  # 看是否有该文件夹，没有则创建文件夹
                os.mkdir(path)
            filepath = path + '\\' + filename  # 设置图片name，注：必须加上扩展名
            with open(filepath, 'wb') as f:  # 显示进度条
                for chunk in r.iter_content(chunk_size=512):
                    if chunk:
                        f.write(chunk)
                        count += len(chunk)
                        if time.time() - time1 > 2:
                            speed = (count - count_tmp) / 1024 / 1024 / 2
                            count_tmp = count
                            print('\r' + '[下载进度]:%s%.2f%%' % ('>' * int(count * 50 / length), float(count / length * 100)),end=' ' + ' Speed:%.2f ' % speed + 'M/S')
                            time1 = time.time()
                end_time = time.time()  # 下载结束时间
                print('\nDownload completed!,times: %.2f秒\n' % (end_time - start_time))  # 输出下载用时时间
            f.close()

    '''定义音频下载的方法'''
    def download_audio(self, video_list):
        for item in video_list:
            # print(item)
            # 去掉创建文件时的非法字符
            title1 = re.sub(r'[\/:*?"<>|]', '-', item['title'])
            title = title1.replace(" ","")
            video_url = item['audio_url']
            # 拼接文件名
            name1 = re.sub(r'[\/:*?"<>|]', '-', item['name'])
            name = name1.replace("&","and")
            filename = name + '.mp3'
            # 视频请求下载地址
            r = requests.get(url=video_url, stream=True, headers=self.downloadVideoHeaders)
            # 根据请求页面的response headers得到content-length，也就是文件的总bit大小
            length = float(r.headers['content-length'])
            count = 0
            count_tmp = 0
            time1 = time.time()
            start_time = time.time()
            print('[Start download]:{filename},[File size]:{size:.2f} MB'.format(filename=filename,size=length / 1024 / 1024))  # 开始下载，显示下载文件大小
            path = r'E:\{dir_title}'.format(dir_title=title)
            if not os.path.exists(path):  # 看是否有该文件夹，没有则创建文件夹
                os.mkdir(path)
            filepath = path + '\\' + filename  # 设置图片name，注：必须加上扩展名
            with open(filepath, 'wb') as f:  # 显示进度条
                for chunk in r.iter_content(chunk_size=512):
                    if chunk:
                        f.write(chunk)
                        count += len(chunk)
                        if time.time() - time1 > 2:
                            speed = (count - count_tmp) / 1024 / 1024 / 2
                            count_tmp = count
                            print('\r' + '[下载进度]:%s%.2f%%' % ('>' * int(count * 50 / length), float(count / length * 100)),end=' ' + ' Speed:%.2f ' % speed + 'M/S')
                            time1 = time.time()
                end_time = time.time()  # 下载结束时间
                print('\nDownload completed!,times: %.2f秒\n' % (end_time - start_time))  # 输出下载用时时间
            f.close()

    '''音视频合并'''
    def CombineVideoAudio(self, video_list):
        # num = 1
        for item in video_list:
            title1 = re.sub(r'[\/:*?"<>|]', '-', item['title'])
            title = title1.replace(" ", "")
            name1 = re.sub(r'[\/:*?"<>|]', '-', item['name'])
            name = name1.replace("&", "and")
            log_filename = "音视频合并看这里.txt"
            log_filepath = r'E:\{dir_title}\{log_filename}'.format(dir_title=title,log_filename=log_filename)
            video_filename = name + '.mp4'
            video_filepath = r'E:\{dir_title}\{video_filename}'.format(dir_title=title,video_filename=video_filename) # 设置图片name，注：必须加上扩展名
            audio_filename = name + '.mp3'
            audio_filepath = r'E:\{dir_title}\{audio_filename}'.format(dir_title=title,audio_filename=audio_filename)# 设置图片name，注：必须加上扩展名
            out_filename = name + '-change.mp4'
            out_filepath = r'E:\{dir_title}\{out_filename}'.format(dir_title=title,out_filename=out_filename)
            cmd = 'ffmpeg -i ' + video_filepath + ' -i ' + audio_filepath + ' -strict -2 -f mp4 ' + out_filepath
            with open(log_filepath,'a+') as f:
                    f.write(cmd+'\n')
                    f.write("\n")
            f.close()
        with open(log_filepath, 'a+') as f:
            f.write("\n")
            f.write("------电脑安装好FFmpeg配置好path环境变量后，复制以下命令到cmd命令窗口可以实现将音视频合并。\n")
            f.write("------安装FFmpeg及配置path环境变量教程自行百度即可\n")
        f.close()
    print("--------log写入完毕--------")

    '''使用FFmpeg将音视频合并，由于不知名原因代码无法实现，故暂且手动合并音视频'''
            # print("开始拼接第{num}个文件：{name}".format(num=num,name=out_filename))
            # num +=1
            # cmd='ffmpeg -i ' + video_filepath + ' -i ' + audio_filepath + ' -strict -2 -f mp4 ' + out_filepath
            # print(cmd)
            # d = os.popen(cmd)
            # print(d.read())
            # os.remove(video_filepath)
            # os.remove(audio_filepath)
            # print("第{num}个文件拼接完成！".format(num=num))

    '''运行方法'''
    def run(self,url):
        self.download_video(self.parseHtml(self.getHtml(self.getRight_urls(fanhao))))
        self.download_audio(self.parseHtml(self.getHtml(self.getRight_urls(fanhao))))
        self.CombineVideoAudio(self.parseHtml(self.getHtml(self.getRight_urls(fanhao))))
        # self.parseHtml(self.getHtml(url))
        # self.getHtml(self.getRight_urls(fanhao))
        # self.getRight_urls(url)

if __name__ == '__main__':
    fanhao = 'BV1zx411x7J9'
    # fanhao = 'BV13t411771i'
    bilibili().run(fanhao)

