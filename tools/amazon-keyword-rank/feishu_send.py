"""Send a Feishu message (text / post / image / file) from a Feishu custom app bot to one recipient.
Apps are configured purely through env vars (nothing hard-coded):
  default : FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_RECEIVE_OPEN_ID
  <name>  : FEISHU_<NAME>_APP_ID / FEISHU_<NAME>_APP_SECRET / FEISHU_<NAME>_RECEIVE_OPEN_ID
            e.g. --app scout -> FEISHU_SCOUT_APP_ID ... (open_id differs per app, so each app has its own recipient id)
Usage: python3 feishu_send.py --app scout --text "内容" | --title T --text "多行" | --post post.json | --image a.png | --file clip.mp4
Import: from feishu_send import send; send("scout", title="...", text="...")"""
import os,json,argparse,sys,uuid,urllib.request,mimetypes
from feishu import req
def _env(app,key):
    pre="FEISHU_" if app in (None,"","default") else "FEISHU_%s_"%app.upper()
    v=os.environ.get(pre+key)
    if not v: raise RuntimeError("missing env "+pre+key)
    return v
def token(app):
    return req("POST","/auth/v3/tenant_access_token/internal",{"app_id":_env(app,"APP_ID"),"app_secret":_env(app,"APP_SECRET")})["tenant_access_token"]
def send(app,text=None,post=None,title=None):
    oid=_env(app,"RECEIVE_OPEN_ID")
    if post is None and title:
        post={"zh_cn":{"title":title,"content":[[{"tag":"text","text":l}] for l in text.split("\n")]}}
    body={"receive_id":oid,"msg_type":"post" if post else "text","content":json.dumps(post if post else {"text":text},ensure_ascii=False)}
    return req("POST","/im/v1/messages?receive_id_type=open_id",body,token(app))
def _upload(app,path,url,fields,filefield):
    b=uuid.uuid4().hex; parts=b""
    for k,v in fields.items(): parts+=f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    ct=mimetypes.guess_type(path)[0] or "application/octet-stream"
    parts+=f'--{b}\r\nContent-Disposition: form-data; name="{filefield}"; filename="{os.path.basename(path)}"\r\nContent-Type: {ct}\r\n\r\n'.encode()+open(path,"rb").read()+f'\r\n--{b}--\r\n'.encode()
    r=urllib.request.Request("https://open.feishu.cn/open-apis"+url,data=parts,headers={"Authorization":"Bearer "+token(app),"Content-Type":"multipart/form-data; boundary="+b},method="POST")
    try: return json.loads(urllib.request.urlopen(r,timeout=300).read())
    except urllib.error.HTTPError as e: return json.loads(e.read() or b"{}")
def _msg(app,msg_type,content):
    oid=_env(app,"RECEIVE_OPEN_ID")
    return req("POST","/im/v1/messages?receive_id_type=open_id",{"receive_id":oid,"msg_type":msg_type,"content":json.dumps(content)},token(app))
def send_image(app,path):
    d=_upload(app,path,"/im/v1/images",{"image_type":"message"},"image")
    k=(d.get("data") or {}).get("image_key")
    return _msg(app,"image",{"image_key":k}) if k else d
def send_file(app,path):
    """Video (.mp4) is sent as a playable media message; anything else as a file (max 30MB)."""
    ext=os.path.splitext(path)[1].lower().lstrip(".")
    ft={"mp4":"mp4","pdf":"pdf","doc":"doc","docx":"doc","xls":"xls","xlsx":"xls","ppt":"ppt","pptx":"ppt","opus":"opus"}.get(ext,"stream")
    d=_upload(app,path,"/im/v1/files",{"file_type":ft,"file_name":os.path.basename(path)},"file")
    k=(d.get("data") or {}).get("file_key")
    if not k: return d
    return _msg(app,"media" if ft=="mp4" else "file",{"file_key":k})
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--app",default="default"); ap.add_argument("--text"); ap.add_argument("--title"); ap.add_argument("--post"); ap.add_argument("--image"); ap.add_argument("--file")
    a=ap.parse_args()
    if a.image: r=send_image(a.app,a.image)
    elif a.file: r=send_file(a.app,a.file)
    else: r=send(a.app,text=a.text,post=json.load(open(a.post)) if a.post else None,title=a.title)
    print("feishu send:",r.get("code"),r.get("msg")); sys.exit(0 if r.get("code")==0 else 1)
