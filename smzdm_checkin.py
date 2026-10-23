#!/usr/bin/env python3
"""什么值得买每日签到；仅使用官网接口，不自动处理验证码。"""
import json
import os
import re
import sys
import time
from urllib.request import Request, urlopen

cookie = os.environ.get('SMZDM_COOKIE', '').strip()
if not cookie:
    print('执行失败：未注入 SMZDM_COOKIE。')
    sys.exit(1)
url = 'https://zhiyou.smzdm.com/user/checkin/jsonp_checkin?callback=checkin&_=' + str(int(time.time()*1000))
request = Request(url, headers={'Cookie': cookie, 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.smzdm.com/', 'Accept': '*/*'})
try:
    with urlopen(request, timeout=30) as response:
        body = response.read().decode('utf-8')
    match = re.fullmatch(r'\s*(?:checkin|callback)\s*\((.*)\)\s*;?\s*', body, re.S)
    result = json.loads(match.group(1) if match else body)
    code = result.get('error_code')
    message = str(result.get('error_msg') or '')
    data = result.get('data') or {}
    if code == 0:
        print('签到接口成功：累计签到 %s 天，本次积分 %s。' % (data.get('checkin_num', '未知'), data.get('add_point', '未知')))
    elif '已签到' in message or '已经签到' in message:
        print('执行成功：今日已签到。')
    else:
        print('签到未完成：错误码 %s，%s；如要求验证码，请在官网手动完成。' % (code, message[:200]))
        sys.exit(1)
except Exception as exc:
    print('执行失败：%s。请检查网络或登录状态。' % type(exc).__name__)
    sys.exit(1)
