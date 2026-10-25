"""Minimal Feishu Open API helper (stdlib only).
Credentials come from env: FEISHU_APP_ID, FEISHU_APP_SECRET (never hard-code them)."""
import os,json,urllib.request,urllib.error
APP_ID=os.environ.get("FEISHU_APP_ID","")  # <YOUR_FEISHU_APP_ID>
def req(method,path,body=None,token=None):
    h={"Content-Type":"application/json; charset=utf-8"}
    if token: h["Authorization"]="Bearer "+token
    r=urllib.request.Request("https://open.feishu.cn/open-apis"+path,data=json.dumps(body).encode() if body is not None else None,headers=h,method=method)
    try: return json.loads(urllib.request.urlopen(r,timeout=30).read())
    except urllib.error.HTTPError as e: return json.loads(e.read() or b'{}')
def tok():
    return req("POST","/auth/v3/tenant_access_token/internal",{"app_id":os.environ["FEISHU_APP_ID"],"app_secret":os.environ["FEISHU_APP_SECRET"]})["tenant_access_token"]
