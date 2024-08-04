import os
from os import path
import subprocess
import argparse
import time
from faster_whisper import WhisperModel

model_size = "medium"
# Run on GPU with FP16
model = WhisperModel(model_size)


def segments_to_ass_text(file_name, segments):
    def convert_seconds_to_time(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60

        return f"{int(hours):0>2d}:{int(minutes):0>2d}:{remaining_seconds:.2f}"

    prefix = f"""[Script Info]
Title: {file_name}
Original Script: Julen
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1280
PlayResY: 720
YCbCr Matrix: TV.709
ScaledBorderAndShadow: yes
    
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,方正准圆_GBK,34,&H90FFFFFF,&H90FFFFFF,&H90000000,&H80FFFFFF,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,0,1
    
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    subs = ""
    for segment in segments:
        line = f"Dialogue: 0,{convert_seconds_to_time(segment.start)},{convert_seconds_to_time(segment.end)},Default,,0,0,0,,{segment.text}\n"
        subs += line

    return prefix + subs

def do_whisper(audio_path):
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # or run on CPU with INT8
    # model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5, language="ja", vad_filter=True)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    segments_list = []

    for segment in segments:
        segments_list.append(segment)

    return segments_list

def extract_to_acc(file_path):
    basename, suffix = path.splitext(path.basename(file_path))
    audio_path = path.join(path.dirname(file_path), f"{basename}.aac")
    command = f'ffmpeg -i "{file_path}" -vn -acodec copy "{audio_path}"'
    subprocess.run(command, shell=True)
    return audio_path

def write_ass_file(file_path, ass_text):
    basename, suffix = path.splitext(path.basename(file_path))
    ass_path = path.join(path.dirname(file_path), f"{basename}.jpstt.ass")

    with open(ass_path, "w", encoding="utf-8") as file:
        # 写入文本
        file.write(ass_text)

def clean_up(files):
    for file in files:
        os.remove(file)

def subtitle_stt(file_path):
    start_time = time.time()

    print(f"--- extract audio ---")
    audio_path = extract_to_acc(file_path)

    print(audio_path)
    print(f"--- whisper stt ---")
    segments = do_whisper(audio_path)

    print(f"--- generate ass txt ---")
    sub_text = segments_to_ass_text(path.basename(file_path), segments)

    print(f"--- write ass file ---")
    write_ass_file(file_path, sub_text)

    print(f"--- clean up ---")
    clean_up([audio_path])

    end_time = time.time()
    print(f"代码执行时间: {end_time - start_time:.6f}s")

def main(directories):
    allowed_video_suffix = (".mp4", ".mkv")
    for directory in directories:
        file_paths = [path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith(allowed_video_suffix)]

        print(f"--- video count: {len(file_paths)} ---")
        print('\n\n')
        print('\n'.join(file_paths))

        for file_path in file_paths:
            print(f"--- start process {path.basename(file_path)} ---")
            subtitle_stt(file_path)


# 创建 ArgumentParser 对象
parser = argparse.ArgumentParser()

# 添加参数
parser.add_argument('--dirs', nargs='+', type=str, help='A list of dirs')

# 解析命令行参数
args = parser.parse_args()

main(args.dirs)