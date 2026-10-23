#!/usr/bin/env python3
"""签到安装者指定的贴吧；未加入或等级不足单独计为跳过。"""
import json
import os
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

cookie = os.environ.get('TIEBA_COOKIE', '').strip()
forums = list(dict.fromkeys(name.strip() for name in os.environ.get('TIEBA_FORUMS', '').split(',') if name.strip()))
if not cookie or not forums:
    print('请配置 TIEBA_COOKIE 和 TIEBA_FORUMS（英文逗号分隔吧名，不加“吧”后缀）。')
    sys.exit(1)


def call(path, data=None):
    request = Request('https://tieba.baidu.com' + path,
                      data=urlencode(data).encode() if data else None,
                      headers={'Cookie': cookie, 'User-Agent': 'Mozilla/5.0',
                               'Referer': 'https://tieba.baidu.com/',
                               'Content-Type': 'application/x-www-form-urlencoded'})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


try:
    auth = call('/dc/common/tbs')
    if str(auth.get('is_login')) != '1':
        print('贴吧登录失效，请更新 Cookie。')
        sys.exit(1)
    succeeded = skipped = failures = 0
    for name in forums:
        try:
            result = call('/sign/add', {'ie': 'utf-8', 'kw': name, 'tbs': auth['tbs']})
            code = str(result.get('no', result.get('error_code', '')))
            message = str(result.get('error') or result.get('error_msg') or '')
            if code == '0' or '已签' in message or '已经签' in message:
                succeeded += 1
                print(name + '：成功或已签到')
            elif code == '1011':
                skipped += 1
                print(name + '：跳过（未加入此吧或等级不足）')
            else:
                failures += 1
                print(name + '：未完成，错误码 ' + code)
        except Exception as error:
            failures += 1
            print(name + '：' + type(error).__name__)
        time.sleep(2)
    print('完成：成功 %s，跳过 %s，失败 %s，总计 %s。' % (succeeded, skipped, failures, len(forums)))
    sys.exit(1 if failures or not succeeded else 0)
except Exception as error:
    print('执行失败：' + type(error).__name__)
    sys.exit(1)
