import os
import time
import math
import random

from utils import FFmpeg, Status
from concurrent.futures import ThreadPoolExecutor
from crawler import BilibiliCrawler

class BilibiliMedia():
    """
    Bilibili媒体类
    
    Properties:
        page -- 第几P
        path -- name.mp4
        video -- 视频
        audio -- 音频
    """

    def __init__(self, page, name, path, cid, spider):

        self.page = page
        self.name = name
        self.path = path
        self.cid = cid
        self.spider = spider

        self.video = None
        self.audio = None
        self.total = 0
        self.status = Status()

    def set_video(self, url, qn):
        self.video = BilibiliFile('video', url, qn, self.path, self.spider)

    def set_audio(self, url, qn):
        self.audio = BilibiliFile('audio', url, qn, self.path, self.spider)

    @property
    def medias(self):
        return (self.video, self.audio)
    
    def merge(self, ffmpeg):
        """ 调用ffmpeg合并音频与视频 """
        if self.video.status.done and self.audio.status.done:
            ffmpeg.join_video_audio(self.video.path, self.audio.path, self.path)
            os.remove(self.video.path)
            os.remove(self.audio.path)

class BilibiliFile():
    """
    Bilibili文件类

    Properties:
        type -- audio/video
        path -- name_type.m4s
    """     

    def __init__(self, type, url, qn, path, spider):

        self.type = type
        self.url = url
        self.qn = qn
        self.path = '{}_{}.m4s'.format(os.path.splitext(path)[0], self.type)
        self.spider = spider

        self.block_size = 10*1024*1024
        self.name = os.path.split(self.path)[-1]
        self.total = 0
        self.get_total()

        print("[Info] 正在下载{}，大小：{}MB".format(self.name, round(self.total / (1024*1024), 2)))
        self.blocks = []
        self.get_blocks()
        self.status = Status()
    
    def get_total(self):
        # 获取文件大小
        res = self.spider.head(self.url, headers={'Range': 'bytes=0-4'})
        if res.headers.get('Content-Range'):
            self.total = int(res.headers['Content-Range'].split('/')[-1])
        elif res.headers.get('Content-Length'):
            self.total = int(res.headers['Content-Length'])
        else:
            self.total = None

    def get_blocks(self):
        # 将文件分块
        for i in range(math.ceil(self.total/self.block_size)):
            block = BilibiliBlock(i, self.url, self.qn, self.path, self.spider)
            self.blocks.append(block)
    
    def merge(self):
        """ 合并block """
        # 检查是否所有block均已下载完成，如果是则合并
        if all([block.status.done for block in self.blocks]):
            with open(self.path, "wb+") as fw:
                for block in self.blocks:
                    with open(block.path, "rb") as fr:
                        fw.write(fr.read())
                    block.remove()

class BilibiliBlock():
    """
    Bilibili文件块类
    
    Properties:
        index -- block序号
        path -- name_type.m4s.index
        block_size -- block大小，默认为10MB
    """

    def __init__(self, index, url, qn, path, spider, block_size=10*1024*1024):

        self.index = index
        self.url = url
        self.qn = qn
        self.path = "{}.{:03}".format(path, index)
        self.spider = spider
        self.block_size = 10*1024*1024

        self.name = os.path.split(self.path)[-1]
        self.status = Status()

    def download(self):
        stream = True
        chunk_size = 1024
        # 更改状态
        self.status.switch(Status.DOWNLOADING)

        if not os.path.exists(self.path):
            # 设置 headers
            headers = dict(self.spider.headers)
            headers["Range"] = "bytes={}-{}".format(
                self.index * self.block_size,
                (self.index + 1) * self.block_size - 1)
            # 尝试建立连接
            connected = False
            while not connected:
                try:
                    res = self.spider.get(
                        self.url, stream=stream, headers=headers)
                    connected = True
                except:
                    print("[Error] 下载出错，正在重新尝试...")

            # 写入文件
            with open(self.path, 'wb+') as f:
                if stream == True:
                    for chunk in res.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            break
                        f.write(chunk)
                else:
                    f.write(res.content)
        self.status.switch(Status.DONE)

    def remove(self):
        """ 删除文件 """
        if os.path.exists(self.path):
            os.remove(self.path)

class BilibiliFileManager():
    """ bilibili 文件管理器 """

    def __init__(self, thread_num, block_size, ffmpeg):
        self.ffmpeg = ffmpeg
        self.mms = []
        self.thread_num = thread_num
        self.block_size = block_size

    def dispense_resources(self, resources, log=True):
        """ 资源分发，将资源切分为片段，并分发至线程池 """

        for i, mm in enumerate(resources):
            self.mms.append(mm)
            name = mm.name
            for media in mm.medias:
                if os.path.exists(media.path):
                    media.status.switch(Status.DONE)
                    continue
                with ThreadPoolExecutor(max_workers=self.thread_num) as executor:
                    for block in media.blocks:
                        executor.submit(block.download)
                print("[Info] {} 正在合并{} block...".format(name, media.type))
                media.merge()
                media.status.switch(Status.DONE)
                print("[Info] {} 合并{} block成功".format(name, media.type))
            print("[Info] {} 正在合并音频与视频...".format(name))
            mm.merge(self.ffmpeg)
            print("[Info] {} 合并音频与视频成功！".format(name))