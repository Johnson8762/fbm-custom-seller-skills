"""Feishu Bitable client with token refresh, retries and batching."""
import os,json,time,urllib.request,urllib.error,socket
BASE="https://open.feishu.cn/open-apis"
TOKEN_ERRS={99991661,99991663,99991664,99991668,99991671}
RETRY_ERRS={1254290,1254291,1254607,1255040,1254036}  # rate limit / write conflict / data not ready / timeout
class FeishuError(Exception): pass
class Client:
    def __init__(self,app_token):
        self.app=app_token; self._tok=None; self._exp=0; self.calls=0
    def token(self,force=False):
        if force or not self._tok or time.time()>self._exp-300:
            r=self._raw("POST","/auth/v3/tenant_access_token/internal",{"app_id":os.environ["FEISHU_APP_ID"],"app_secret":os.environ["FEISHU_APP_SECRET"]},None)
            if r.get("code")!=0: raise FeishuError("token: code=%s msg=%s"%(r.get("code"),r.get("msg")))
            self._tok=r["tenant_access_token"]; self._exp=time.time()+int(r.get("expire",7200))
        return self._tok
    def _raw(self,method,path,body,tok):
        h={"Content-Type":"application/json; charset=utf-8"}
        if tok: h["Authorization"]="Bearer "+tok
        rq=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers=h,method=method)
        try: return json.loads(urllib.request.urlopen(rq,timeout=60).read())
        except urllib.error.HTTPError as e:
            raw=e.read() or b'{}'
            try: d=json.loads(raw)
            except Exception: d={"code":-e.code,"msg":raw[:300].decode("utf8","replace")}
            d.setdefault("_http",e.code); return d
    def call(self,method,path,body=None,tries=6):
        last=None
        for i in range(tries):
            self.calls+=1
            try: r=self._raw(method,path,body,self.token(force=(i>0 and last is not None and last.get("code") in TOKEN_ERRS)))
            except (urllib.error.URLError,socket.timeout,TimeoutError,ConnectionError,json.JSONDecodeError) as e:
                last={"code":-1,"msg":"network: %r"%e}; time.sleep(2*(i+1)); continue
            c=r.get("code")
            if c==0: return r.get("data") or {}
            last=r
            if c in TOKEN_ERRS: continue
            if c in RETRY_ERRS or r.get("_http") in (429,500,502,503,504): time.sleep(min(30,1.5*2**i)); continue
            break
        raise FeishuError("%s %s -> code=%s msg=%s %s"%(method,path,last.get("code"),last.get("msg"),json.dumps(last.get("error",""),ensure_ascii=False)[:500]))
    # ---- tables / fields
    def tables(self):
        return self.call("GET",f"/bitable/v1/apps/{self.app}/tables?page_size=100").get("items",[])
    def fields(self,tid):
        return self.call("GET",f"/bitable/v1/apps/{self.app}/tables/{tid}/fields?page_size=100").get("items",[])
    # ---- records
    def list_records(self,tid,field_names=None,filter_=None):
        out=[]; pt=None
        while True:
            body={}
            if field_names: body["field_names"]=field_names
            if filter_: body["filter"]=filter_
            q="?page_size=500"+("&page_token="+pt if pt else "")
            d=self.call("POST",f"/bitable/v1/apps/{self.app}/tables/{tid}/records/search"+q,body)
            out+=d.get("items") or []
            if not d.get("has_more"): return out
            pt=d.get("page_token")
    def batch_create(self,tid,rows):
        ids=[]
        for i in range(0,len(rows),500):
            d=self.call("POST",f"/bitable/v1/apps/{self.app}/tables/{tid}/records/batch_create",{"records":[{"fields":f} for f in rows[i:i+500]]})
            ids+=[x["record_id"] for x in d.get("records",[])]
        return ids
    def batch_update(self,tid,recs):  # recs: [{"record_id":..,"fields":{..}}]
        for i in range(0,len(recs),500):
            self.call("POST",f"/bitable/v1/apps/{self.app}/tables/{tid}/records/batch_update",{"records":recs[i:i+500]})
    def batch_delete(self,tid,ids):
        for i in range(0,len(ids),500):
            self.call("POST",f"/bitable/v1/apps/{self.app}/tables/{tid}/records/batch_delete",{"records":ids[i:i+500]})
