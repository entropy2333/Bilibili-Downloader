import re
import os
import cv2
import subprocess
from danmaku2ass import Danmaku2ASS

class FFmpeg():
    """ FFmpeg类 """
    def __init__(self, ffmpeg_path='ffmpeg'):
        assert subprocess.run([ffmpeg_path], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).returncode == 1, "请配置正确的 FFmpeg 路径"
        self.path = os.path.normpath(ffmpeg_path)

    def exec(self, params):
        """ 调用 ffmpeg """
        cmd = [self.path]
        cmd.extend(params)
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def convert(self, input_path, output_path):
        """ 视频格式转换 """
        params = [
            '-i', input_path,
            '-c', 'copy',
            '-map', '0',
            '-y',
            output_path
        ]
        self.exec(params)

    def join_video_audio(self, video_path, audio_path, output_path):
        """ 将视频和音频合并 """

        params = [
            '-i', video_path,
            '-i', audio_path,
            '-vcodec', 'copy',
            '-y',
            output_path
        ]

        self.exec(params)

class Status():

    INITIALIZED = 1
    DOWNLOADING = 2
    DONE = 4

    def __init__(self):
        self.value = Status.INITIALIZED

    def switch(self, status=None):
        """ 切换到某一状态，默认为下一状态 """
        if status is None:
            self.value <<= 1
        else:
            self.value = status

    @property
    def initialized(self):
        """ 返回状态字段是否是 INITIALIZED """
        return self.value == Status.INITIALIZED

    @property
    def downloading(self):
        """ 返回状态字段是否是 DOWNLOADING """
        return self.value == Status.DOWNLOADING

    @property
    def done(self):
        """ 返回状态字段是否是 DONE """
        return self.value == Status.DONE

def touch_dir(path):
    """ 若文件夹不存在则新建，否则返回False """
    if not os.path.exists(path):
        os.makedirs(path)
        return os.path.normpath(path)
    else:
        print('[Error] 文件已经存在！')
        return False

def touch_file(path):
    """ 若文件不存在则新建，并返回标准路径 """
    if not os.path.exists(path):
        open(path, 'w').close()
    return os.path.normpath(path)

def repair_filename(filename):
    """ 修复不合法的文件名 """
    regex_path = re.compile(r'[\\/:*?"<>|]')
    return regex_path.sub('', filename)

def convert_danmaku(video_path_list):
    """ 将xml弹幕转换为ass弹幕 """
    # 检测插件是否已经就绪
    plugin_url = "https://raw.githubusercontent.com/m13253/danmaku2ass/master/danmaku2ass.py"
    plugin_path = "danmaku2ass.py"
    
    if not os.path.exists(plugin_path):
        print("[Info] 下载danmaku2ass插件中……")
        res = requests.get(plugin_url)
        with open(plugin_path, "w+", encoding="utf-8") as f:
            f.write(res.text)

    # 调用Danmaku2ASS插件进行转换
    for video_path in video_path_list:
        name = os.path.splitext(video_path)[0]
        if not os.path.exists(name + ".mp4") or \
            not os.path.exists(name + ".xml"):
            continue
        if not os.path.exists(name + '.ass'):
            cap = cv2.VideoCapture(name + ".mp4")
            __, frame = cap.read()
            h, w, __ = frame.shape
            Danmaku2ASS(
                name+".xml", "autodetect", name+".ass",
                w, h, reserve_blank=0,
                font_face=_('(FONT) sans-serif')[7:],
                font_size=w/40, text_opacity=0.8, duration_marquee=15.0,
                duration_still=10.0, comment_filter=None, is_reduce_comments=False,
                progress_callback=None)
        print("[Info] {} 弹幕格式转换成功".format(os.path.split(name)[-1]))