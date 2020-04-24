import os
import re
import sys
import json
import threading

from common import BilibiliMedia
from crawler import BilibiliCrawler
from utils import repair_filename, touch_dir

spider = BilibiliCrawler()

qn_dict = {
    80: "超清 1080P",
    64: "高清 720P",
    32: "清晰 480P",
    16: "流畅 360P"
}

CONFIG = dict()

class BilibiliParser():
    
    @staticmethod
    def info_api(avid, bvid):
        return "https://api.bilibili.com/x/player/pagelist?aid={}&bvid={}&jsonp=jsonp".format(avid, bvid)

    @staticmethod
    def parse_api(avid, cid, bvid, qn):
        return "https://api.bilibili.com/x/player/playurl?avid={}&cid={}&bvid={}&qn={}&type=&otype=json&fnver=0&fnval=16".format(avid, cid, bvid, qn)
    
    @staticmethod
    def danmaku_api(cid):
        return "https://comment.bilibili.com/{}.xml".format(cid)
    
    def get_title(self, url):
        """ 获取视频标题 """
        res = spider.get(url)
        title = re.search(r'<title .*>(.*)_哔哩哔哩 \(゜-゜\)つロ 干杯~-bilibili</title>', res.text).group(1)
        return title
    
    def get_videos(self, url):
        """ 根据url获取视频信息 """
        videos = []
        CONFIG['avid'], CONFIG['bvid'] = '', ''
        if re.match(r"https?://www.bilibili.com/video/av(\d+)", url):
            CONFIG['avid'] = re.match(r'https?://www.bilibili.com/video/av(\d+)', url).group(1)
        elif re.match(r"https?://b23.tv/av(\d+)", url):
            CONFIG['avid'] = re.match(r"https?://b23.tv/av(\d+)", url).group(1)
        elif re.match(r"https?://www.bilibili.com/video/BV(\w+)", url):
            CONFIG['bvid'] = re.match(r"https?://www.bilibili.com/video/BV(\w+)", url).group(1)
        elif re.match(r"https?://b23.tv/BV(\w+)", url):
            CONFIG['bvid'] = re.match(r"https?://b23.tv/BV(\w+)", url).group(1)
        
        info_url = self.info_api(avid=CONFIG['avid'], bvid=CONFIG['bvid'])
        res = spider.get(info_url)
        res = res.json()['data']

        for item in res:
            file_path = os.path.join(CONFIG['video_dir'], repair_filename('{}.mp4'.format(item["part"])))
            videos.append(BilibiliMedia(
                page = item['page'],
                name = item['part'],
                path = file_path,
                cid = item['cid'],
                spider = spider
            ))
        return videos

    def get_segment(self, media):
        """ 解析媒体信息，获取音频与视频信息 """
        cid, avid, bvid = media.cid, CONFIG["avid"], CONFIG["bvid"] 
        
        # 检查视频是否可以下载
        media_info = spider.get(self.parse_api(avid, cid, bvid, qn=80)).json()

        if media_info["code"] != 0:
            print("[Error] 无法下载 {} ，原因： {}".format(media.name, media_info["message"]))
            media.status.switch(Status.DONE)
            return 

        if not media_info['data'].get('dash'):
            print('[Error] 该视频尚不支持 H5 source')
            return 

        # 获取支持的视频清晰度
        accept_quality = set([video['id'] for video in media_info['data']['dash']['video']])
        if CONFIG['quality'] in accept_quality:
            qn = CONFIG['quality']
        else:    
            qn = max(accept_quality)
        
        print("[Info] 清晰度：{}".format(qn_dict[qn]))

        parse_url = self.parse_api(avid, cid, bvid, qn)
        media_info = spider.get(parse_url).json()

        for video in media_info['data']['dash']['video']:
            if video['id'] == qn:
                media.set_video(
                    url = video['base_url'],
                    qn = qn
                )
                break
        for audio in media_info['data']['dash']['audio']:
            media.set_audio(
                url = audio['base_url'],
                qn = qn
            )
            break
    
    def get_danmaku(self, cid, danmaku_path):
        """ 根据cid获取弹幕 """
        danmaku_url = self.danmaku_api(cid)
        res = spider.get(danmaku_url)
        res.encoding = "utf-8"
        with open(danmaku_path, "w", encoding="utf-8") as f:
            f.write(res.text)
        print("[Info] 弹幕下载完成！")

    def parse(self, url, config):
        """ 解析视频信息，获取下载链接 """

        CONFIG.update(config)
        title = self.get_title(url)
        print("[Info] 视频标题：{}".format(title))

        # 创建目录结构
        CONFIG["video_dir"] = touch_dir(repair_filename(os.path.join(
            CONFIG['dir'], title + "-bilibili")))
        if not CONFIG["video_dir"]:
            print('[Error] 视频已存在！')
            return []
        # CONFIG["video_dir"] = touch_dir(os.path.join(CONFIG['base_dir'], "Videos"))
        
        print("[Info] 保存路径：{}".format(os.path.dirname(os.path.abspath(__file__)) + '\\' + CONFIG["video_dir"]))
        print("[Info] 正在解析视频信息...")
        videos = self.get_videos(url)

        print("[Info] 视频共有{}P".format(len(videos)))

        CONFIG["videos"] = videos
        for video in videos:
            danmaku_path = os.path.splitext(video.path)[0] + ".xml"
            self.get_danmaku(video.cid, danmaku_path)
            self.get_segment(video)
        return videos
    

# if __name__ == "__main__":
#     parser = BilibiliParser()
#     avid, bvid, cid, qn = [882566744, 2, 172274931, 80]

#     info = parser.info_api(avid, bvid)
#     parse = parser.parse_api(avid, bvid, cid, qn)
#     subtitle = parser.subtitle_api(cid, avid, bvid)
#     danmaku = parser.danmaku_api(cid)
#     print(info, parse, subtitle, danmaku, sep='\n')