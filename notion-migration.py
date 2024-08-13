import os
from os import path
import argparse
import re
import html

def main(html_path, md_path):
    md_matches = []
    with open(html_path, 'r') as file:
        content = file.read()

        # 1. 读取匹配的字符串
        # 2. html.unescape()
        # 3. 替换 <strong>，</strong> 为 **，<br/> 为 \n，push to list
        pattern = '<p id="[a-zA-Z0-9-]+" class="">((?:(?!<p)[^\n])+)</p><p id="[a-zA-Z0-9-]+" class="">\\n</p>'
        matches = re.findall(pattern, html.unescape(content))

        for match in matches:
            md_matches.append(re.compile('<br/>').sub("\n", re.compile('<strong>|</strong>').sub("**", match)))

    with open(md_path, 'r+') as file:
        lines = file.readlines()

        new_lines = []
        for line in lines:
            temp = line
            # temp = re.compile('^- ').sub("### ", temp)
            # temp = re.compile('^ {4}').sub("", temp)
            new_lines.append(temp)

        content = '\n'.join(new_lines)

        # remove top two lines
        content = content[content.find('\n\n') + 2:]

        new_content_arr = []
        start = 0

        for line in md_matches:
            length = len(line)
            index = content.find(line, start)
            if ~index:
                new_content_arr.append(content[start:index + length])
                start = index + length
        # siyuan 使用 \u200d 创建空白行
        new_content = '\n\n\u200d'.join(new_content_arr) if len(new_content_arr) else content

        file.truncate(0)
        file.seek(0)
        file.write(new_content)

    # remove hash
    basename, suffix = path.splitext(path.basename(md_path))
    new_path = path.join(path.dirname(md_path), f"{basename[:basename.rfind(' ')]}{suffix}")
    os.rename(md_path, new_path)


# 创建 ArgumentParser 对象
parser = argparse.ArgumentParser()

# 添加参数
parser.add_argument('--html', nargs=1, type=str, help='html folder path')
parser.add_argument('--md', nargs=1, type=str, help='markdown folder path')

# 解析命令行参数
args = parser.parse_args()

html_base_path = path.normpath(args.html[0])
md_base_path = path.normpath(args.md[0])

relative_htmls = []
def recurse(dir_path=''):
    abs_path = path.join(html_base_path, dir_path)
    items = os.listdir(abs_path)

    for item in items:
        abs_item_path = path.join(abs_path, item)
        relative_item_path = path.join(dir_path, item)
        if path.isdir(abs_item_path):
            recurse(relative_item_path)
        elif item.endswith('.html'):
            relative_htmls.append(relative_item_path)

pairs = []
if path.isdir(html_base_path):
    recurse()
    pairs = [(path.join(html_base_path, html), path.join(md_base_path, f"{html.removesuffix('html')}md")) for html in relative_htmls]
else:
    pairs.append((html_base_path, md_base_path))

for pair in pairs:
    main(pair[0], pair[1])
