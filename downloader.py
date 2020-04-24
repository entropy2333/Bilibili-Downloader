import re
import sys
from parse import BilibiliParser
from common import BilibiliFileManager
from utils import FFmpeg, convert_danmaku

def check_url(url):
    """ 检查输入的url是否正确 """
    if re.match(r"https?://www.bilibili.com/video/av(\d+)", url) or \
        re.match(r"https?://b23.tv/av(\d+)", url) or \
        re.match(r"https?://www.bilibili.com/video/BV(\w+)", url) or \
        re.match(r"https?://b23.tv/BV(\w+)", url):
        return True
    else:
        return False

def downloader(args):

    quality_seq = [80, 64, 32, 16]

    config = {
        "url": args['url'],
        "dir": args['dir'],
        "quality": int(args['quality']),
        'block_size': eval(args['block_size']),
        'thread_num': int(args['thread_num'])
    }
    
    parser = BilibiliParser()
    # 解析视频信息
    videos = parser.parse(args['url'], config)
    
    if videos:
        # 创建文件管理器，并分发任务
        ffmpeg = FFmpeg()
        manager = BilibiliFileManager(config['thread_num'], config['block_size'], ffmpeg)
        # 启动任务
        manager.dispense_resources(videos)
        print("[Info] 视频已全部下载完成！")
    else:
        print("[Info] 没有需要下载的视频！")

    print("[Info] 正在转换弹幕格式...")
    convert_danmaku([video.path for video in videos])

# if __name__ == "__main__":
#     args = {
#         'url': 'https://www.bilibili.com/video/BV1dE411s7My',
#         'dir': '',
#         'quality': 112
#     }
#     download(args)