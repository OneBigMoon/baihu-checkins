import os,json,sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError
cookie=os.environ.get('CTRIP_COOKIE','')
if not cookie:
    print('缺少 CTRIP_COOKIE'); sys.exit(1)
body={'platform':'H5','openId':'','rmsToken':'','head':{'cid':'','ctok':'','cver':'1.0','lang':'01','sid':'8888','syscode':'09','auth':'','xsid':'','extension':[]}}
try:
    req=Request('https://m.ctrip.com/restapi/soa2/22769/signToday',data=json.dumps(body).encode(),headers={'Cookie':cookie,'Content-Type':'application/json','User-Agent':'Mozilla/5.0','Origin':'https://m.ctrip.com','Referer':'https://m.ctrip.com/activitysetupapp/mkt/index/membersignin2021'})
    with urlopen(req,timeout=30) as r: result=json.load(r)
    code=result.get('code')
    message=str(result.get('message',''))
    if code==0:
        print('携程签到成功；连续 '+str(result.get('continueDay',0))+' 天；基础积分 '+str(result.get('baseIntegratedPoint',0)))
    elif '已签' in message or 'already' in message.lower():
        print('携程今日已签到')
    else:
        print('携程签到未成功；code='+str(code)+'；message='+message[:100]);sys.exit(1)
except HTTPError as e:
    print('携程请求失败 HTTP '+str(e.code));sys.exit(1)
except Exception as e:
    print('携程执行异常：'+type(e).__name__);sys.exit(1)
