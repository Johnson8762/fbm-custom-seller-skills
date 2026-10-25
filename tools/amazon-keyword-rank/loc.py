from curl_cffi import requests as r
import re, json, os, html as H_
# any live ASIN page works as the location-setup probe; set via env
PROBE_ASIN=os.environ.get("LOC_PROBE_ASIN","<ANY_LIVE_ASIN>")
H={"Accept-Language":"en-US,en;q=0.9"}
def mk(imp="chrome"):
    s=r.Session(impersonate=imp)
    h=H_.unescape(s.get("https://www.amazon.com/dp/"+PROBE_ASIN,headers=H).text)
    t1=re.search(r'"anti-csrftoken-a2z":"([^"]+)"',h).group(1)
    x=s.get("https://www.amazon.com/portal-migration/hz/glow/get-rendered-address-selections?deviceType=desktop&pageType=Detail&storeContext=NoStoreName&actionSource=desktop-modal",headers={**H,"anti-csrftoken-a2z":t1}).text
    m=re.search(r'CSRF_TOKEN\s*:\s*"([^"]+)"',x)
    tok=m.group(1) if m else t1
    y=s.post("https://www.amazon.com/portal-migration/hz/glow/address-change?actionSource=glow",
       headers={**H,"anti-csrftoken-a2z":tok,"content-type":"application/json"},
       data=json.dumps({"locationType":"LOCATION_INPUT","zipCode":"10001","deviceType":"web","storeContext":"generic","pageType":"Detail","actionSource":"glow"}))
    return s,y
if __name__=="__main__":
    s,y=mk(); print(y.status_code,y.text[:300])
    h=s.get("https://www.amazon.com/dp/"+PROBE_ASIN,headers=H).text
    from bs4 import BeautifulSoup
    b=BeautifulSoup(h,"lxml"); print(b.select_one("#glow-ingress-line2").get_text(strip=True), b.select_one(".a-price .a-offscreen"))
