#!/usr/bin/env python3
import os, json, time, hashlib, re, sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
COOKIE = os.environ.get('SMZDM_COOKIE','').strip()
KEY = 'apr1$AwP!wRRT$gJ/q.X24poeBInlUJC'
def api(path, data=None):
    form = {'weixin':'1','basic_v':'0','f':'android','v':'10.4.26','time':str(round(time.time())*1000)}
    form.update(data or {})
    plain = '&'.join(k+'='+re.sub(r'\s+','',str(form[k]),count=1) for k in sorted(form) if str(form[k]) != '')
    form['sign'] = hashlib.md5((plain+'&key='+KEY).encode()).hexdigest().upper()
    req = Request('https://user-api.smzdm.com'+path, data=urlencode(form).encode(), headers={
        'Cookie':COOKIE, 'User-Agent':'smzdm_android_V10.4.26 rv:866 (Redmi Note 3;Android10.0;zh)smzdmapp',
        'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'})
    with urlopen(req,timeout=25) as r:
        result = json.load(r)
    if str(result.get('error_code')) != '0':
        message = str(result.get('error_msg',result.get('msg','接口拒绝请求')))
        raise RuntimeError('接口错误 '+str(result.get('error_code'))+'：'+message[:100])
    return result.get('data') or {}
def main():
    if not COOKIE:
        raise RuntimeError('缺少 SMZDM_COOKIE')
    data = api('/task/list_v2')
    groups = (data.get('rows') or [{}])[0].get('cell_data',{}).get('activity_task',{}).get('default_list_v2')
    if groups is None:
        raise RuntimeError('任务列表结构已变化，未执行任务')
    tasks = [t for g in groups for t in g.get('task_list',[])]
    print('获取任务列表成功，共 '+str(len(tasks))+' 项')
    claimed = 0
    for task in tasks:
        name = re.sub('<[^>]+>','',str(task.get('task_name','任务')))
        status = str(task.get('task_status'))
        print(name+'：'+{'3':'奖励可领取','2':'未完成'}.get(status,'状态 '+status))
        event = task.get('task_event_type','')
        if status == '2' and event == 'interactive.view.article':
            link = (task.get('task_redirect_url') or {}).get('link','')
            aid = str(task.get('article_id','0'))
            cid = str(task.get('channel_id',''))
            from urllib.parse import urlparse
            if aid != '0' and urlparse(link).scheme == 'https' and (urlparse(link).hostname or '').endswith('.smzdm.com'):
                with urlopen(Request(link,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as article:
                    article.read()
                time.sleep(30)
                api('/task/event_view_article_sync',{'article_id':aid,'channel_id':cid,'task_id':task['task_id']})
                print(name+'：浏览完成')
                status = '3'
            else:
                print('暂未适配此浏览入口')
        elif status == '2':
            print('待人工完成类型：'+str(event))
        if status != '3':
            continue
        robot = api('/robot/token').get('token','')
        if not robot:
            raise RuntimeError('奖励领取需要人工验证')
        reward = api('/task/activity_task_receive',{'robot_token':robot,'geetest_seccode':'','geetest_validate':'','geetest_challenge':'','captcha':'','task_id':task['task_id']})
        print('已领取：'+re.sub('<[^>]+>','',str(reward.get('reward_msg','成功'))))
        claimed += 1
        time.sleep(3)
    print('本次领取 '+str(claimed)+' 项奖励')
if __name__ == '__main__':
    try:
        main()
    except HTTPError as e:
        print('接口 HTTP '+str(e.code)); sys.exit(1)
    except RuntimeError as e:
        print(str(e)); sys.exit(1)
    except Exception as e:
        print('执行失败：'+type(e).__name__); sys.exit(1)
