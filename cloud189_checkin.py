#!/usr/bin/env python3
import os, sys, json, re, time, http.cookiejar
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlencode, urlparse, quote
from urllib.error import HTTPError
import rsa

def main():
    username = os.environ.get('CLOUD189_USERNAME', '').strip()
    password = os.environ.get('CLOUD189_PASSWORD', '')
    account = {'username': username, 'password': password} if username or password else json.loads(os.environ.get('CLOUD189_ACCOUNT', '{}'))
    if not isinstance(account, dict) or not account.get('username') or not account.get('password'):
        raise RuntimeError('请配置天翼账号和密码（兼容 CLOUD189_ACCOUNT JSON）')
    client = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    last_url = ['']
    def request(url, data=None, headers=None):
        h = {'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36', 'Accept': 'application/json,text/html,*/*'}
        h.update(headers or {})
        req = Request(url, data=urlencode(data).encode() if data is not None else None, headers=h)
        with client.open(req, timeout=30) as r:
            last_url[0] = r.url
            return r.read().decode('utf-8', 'replace')
    entry = 'https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL=https://cloud.189.cn/web/redirect.html'
    page = request(entry)
    match = re.search(r"https?://[^\s'\"]+", page)
    if not match:
        raise RuntimeError('未获取到新版登录入口')
    auto_url = match.group()
    request(auto_url)
    login_page = last_url[0].replace('/index.html', '/login.html')
    login_page += ('&' if '?' in login_page else '?') + 'protocol=https&showback=true'
    page = request(login_page)
    match = re.search(r'''id=["']j_rsaKey["'][^>]*value=["']([^"']+)["']''', page)
    if not match:
        raise RuntimeError('新版登录页未提供公钥')
    public = rsa.PublicKey.load_pkcs1_openssl_pem(('-----BEGIN PUBLIC KEY-----\n' + match.group(1) + '\n-----END PUBLIC KEY-----').encode())
    conf = json.loads(request('https://open.e.189.cn/api/logbox/oauth2/wap/appConf.do?' + urlparse(last_url[0]).query, {}, {'Referer': login_page}))
    if str(conf.get('result')) != '0':
        raise RuntimeError('登录配置获取失败')
    fields = conf.get('data') or {}
    def encrypt(value):
        return '{RSA}' + rsa.encrypt(value.encode(), public).hex()
    user = account['username']
    if str(fields.get('hasAt')).lower() == 'true' and '@' not in user:
        user += '@189.cn'
    params = {
        'apptype': 'wap', 'appKey': fields.get('appKey','cloud'),
        'accountType': fields.get('accountType','02'), 'dynamicCheck': 'false',
        'userName': encrypt(user), 'epd': encrypt(account['password']),
        'version': 'v2.0', 'returnUrl': quote(fields.get('returnUrl',''), safe=''),
        'isConfigurable': 'true', 'isOauth2': str(fields.get('isOauth2',True)).lower(),
        'state': fields.get('state',''), 'paramId': fields.get('paramId',''),
        'lt': fields.get('lt',''), 'REQID': fields.get('reqId',''), 'callbackMsg':'callbackMsg'
    }
    raw = request('https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do?' + urlencode(params), headers={'lt': fields.get('lt',''), 'Referer': login_page})
    raw = re.sub(r'^callbackMsg\(', '', raw.strip())
    raw = re.sub(r'\);?$', '', raw)
    login = json.loads(raw)
    if str(login.get('result')) != '0':
        msg = str(login.get('msg', '登录失败'))
        for value in account.values():
            msg = msg.replace(str(value), '[隐藏]')
        raise RuntimeError('天翼登录未成功：' + msg[:120])
    target = login.get('toUrl', '')
    host = urlparse(target).hostname or ''
    if not host.endswith('.189.cn') or urlparse(target).scheme != 'https':
        raise RuntimeError('登录重定向地址异常')
    request(target)
    print('天翼账号登录成功')
    result = json.loads(request('https://m.cloud.189.cn/userSign.action?' + urlencode({
        'clientType': 'TELEANDROID', 'version': '8.6.3', 'model': 'SM-G930K', 'rand': int(time.time()*1000)
    })))
    if 'netdiskBonus' not in result:
        raise RuntimeError('签到未成功，错误代码：' + str(result.get('errorCode', '未知'))[:80])
    label = '今日已签到' if str(result.get('isSign')).lower() == 'true' else '签到成功'
    print(label + '，签到容量：' + str(result['netdiskBonus']) + ' MB')

if __name__ == '__main__':
    try:
        main()
    except HTTPError as e:
        print('请求失败 HTTP ' + str(e.code) + '，位置：' + urlparse(e.url).netloc + urlparse(e.url).path)
        sys.exit(1)
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print('执行失败：' + type(e).__name__ + '（敏感详情已隐藏）')
        sys.exit(1)
