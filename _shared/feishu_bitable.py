"""Shared Feishu Bitable helper for ported skills (stdlib only).

Credentials come from env (never printed):
  FEISHU_APP_ID          (required for live calls)
  FEISHU_APP_SECRET      (required for live calls)
  FEISHU_OWNER_OPEN_ID   owner transfer target (open_id of the user under this app)

DRY-RUN: Client(dry_run=True) never sends a write. Every would-be write is logged
(method, path, short body preview) and returns fake ids, so pipelines can be tested
without touching real bitables. Reads in dry-run also return empty results (no network).

Rules baked in:
  * any bitable created here is immediately transferred to the user (transfer_owner)
  * there is deliberately NO delete-app / delete-table helper.
"""
import json, os, socket, sys, time, urllib.error, urllib.request

BASE = "https://open.feishu.cn/open-apis"
TOKEN_ERRS = {99991661, 99991663, 99991664, 99991668, 99991671}
RETRY_ERRS = {1254290, 1254291, 1254607, 1255040, 1254036}

# Feishu field type codes
TEXT, NUMBER, SELECT, MULTI_SELECT, DATETIME, URL = 1, 2, 3, 4, 5, 15


class FeishuError(Exception):
    pass


def _default_app_id():
    return os.environ.get("FEISHU_APP_ID", "")


def owner_open_id():
    return os.environ.get("FEISHU_OWNER_OPEN_ID", "")


class Client:
    def __init__(self, app_token=None, dry_run=False, log=print):
        self.app = app_token
        self.dry = dry_run
        self.log = log
        self._tok = None
        self._exp = 0
        self.calls = 0
        self._fake = 0

    # ---------- low level
    def _token(self, force=False):
        if force or not self._tok or time.time() > self._exp - 300:
            secret = os.environ.get("FEISHU_APP_SECRET")
            if not secret:
                raise FeishuError("FEISHU_APP_SECRET not set")
            r = self._raw("POST", "/auth/v3/tenant_access_token/internal",
                          {"app_id": _default_app_id(), "app_secret": secret}, None)
            if r.get("code") != 0:
                raise FeishuError("token error code=%s" % r.get("code"))
            self._tok = r["tenant_access_token"]
            self._exp = time.time() + int(r.get("expire", 7200))
        return self._tok

    def _raw(self, method, path, body, tok):
        h = {"Content-Type": "application/json; charset=utf-8"}
        if tok:
            h["Authorization"] = "Bearer " + tok
        rq = urllib.request.Request(BASE + path, method=method, headers=h,
                                    data=json.dumps(body).encode() if body is not None else None)
        try:
            return json.loads(urllib.request.urlopen(rq, timeout=60).read())
        except urllib.error.HTTPError as e:
            raw = e.read() or b"{}"
            try:
                d = json.loads(raw)
            except Exception:
                d = {"code": -e.code, "msg": raw[:300].decode("utf8", "replace")}
            d.setdefault("_http", e.code)
            return d

    def _is_write(self, method, path):
        if method == "GET":
            return False
        if path.split("?")[0].endswith("/records/search"):
            return False
        return True

    def call(self, method, path, body=None, tries=6):
        if self.dry:
            if self._is_write(method, path):
                prev = json.dumps(body, ensure_ascii=False)[:300] if body is not None else ""
                self.log(f"[DRY-RUN] {method} {path} {prev}")
                self._fake += 1
                fid = f"dry_{self._fake}"
                return {"app": {"app_token": fid, "url": f"https://dry-run/base/{fid}"},
                        "table_id": fid, "view": {"view_id": fid}, "field": {"field_id": fid},
                        "records": [{"record_id": f"{fid}_{i}"} for i in range(len((body or {}).get("records", [])))]}
            self.log(f"[DRY-RUN] (read skipped) {method} {path}")
            return {}
        last = None
        for i in range(tries):
            self.calls += 1
            try:
                r = self._raw(method, path, body, self._token(force=(i > 0 and last and last.get("code") in TOKEN_ERRS)))
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                last = {"code": -1, "msg": "network: %r" % e}
                time.sleep(2 * (i + 1))
                continue
            c = r.get("code")
            if c == 0:
                return r.get("data") or {}
            last = r
            if c in TOKEN_ERRS:
                continue
            if c in RETRY_ERRS or r.get("_http") in (429, 500, 502, 503, 504):
                time.sleep(min(30, 1.5 * 2 ** i))
                continue
            break
        raise FeishuError("%s %s -> code=%s msg=%s" % (method, path, last.get("code"), last.get("msg")))

    # ---------- app / tables / fields / views
    def create_app(self, name, folder_token=None, transfer=True):
        """Create a bitable; ALWAYS transfers ownership to the user. Returns (app_token, url)."""
        body = {"name": name}
        if folder_token:
            body["folder_token"] = folder_token
        d = self.call("POST", "/bitable/v1/apps", body)
        app = d.get("app", {})
        self.app = app.get("app_token")
        if transfer:
            self.transfer_owner(self.app)
        return self.app, app.get("url", "")

    def transfer_owner(self, token, open_id=None):
        oid = open_id or owner_open_id()
        if not oid:
            raise FeishuError(f"owner open_id missing (set FEISHU_OWNER_OPEN_ID)")
        q = "?type=bitable&need_notification=false&remove_old_owner=false&old_owner_perm=full_access"
        return self.call("POST", f"/drive/v1/permissions/{token}/members/transfer_owner{q}",
                         {"member_type": "openid", "member_id": oid})

    def tables(self):
        return self.call("GET", f"/bitable/v1/apps/{self.app}/tables?page_size=100").get("items", [])

    def create_table(self, name, fields):
        """fields: [{"field_name":..., "type": int, "property": {...}}]; first field becomes primary."""
        d = self.call("POST", f"/bitable/v1/apps/{self.app}/tables",
                      {"table": {"name": name, "default_view_name": "全部", "fields": fields}})
        return d.get("table_id")

    def fields(self, tid):
        return self.call("GET", f"/bitable/v1/apps/{self.app}/tables/{tid}/fields?page_size=100").get("items", [])

    def create_field(self, tid, field):
        """新增字段（只增不删）"""
        d = self.call("POST", f"/bitable/v1/apps/{self.app}/tables/{tid}/fields", field)
        return (d.get("field") or {}).get("field_id", "")

    def ensure_fields(self, tid, wanted):
        """补齐缺失字段（按 field_name 比对），返回新增的字段名列表。dry-run 下只记录。"""
        if self.dry:
            self.log(f"[DRY-RUN] ensure_fields {tid}: 将按需补齐 {len(wanted)} 个字段")
            return []
        have = {f["field_name"] for f in self.fields(tid)}
        added = []
        for f in wanted:
            if f["field_name"] not in have:
                self.create_field(tid, f); added.append(f["field_name"])
        return added

    def create_view(self, tid, name, view_type="grid"):
        d = self.call("POST", f"/bitable/v1/apps/{self.app}/tables/{tid}/views",
                      {"view_name": name, "view_type": view_type})
        return (d.get("view") or {}).get("view_id")

    def set_view_filter(self, tid, vid, field_id, operator, value):
        """value: Feishu expects a JSON string, e.g. '["optXXX"]' for selects or '"text"'."""
        return self.call("PATCH", f"/bitable/v1/apps/{self.app}/tables/{tid}/views/{vid}",
                         {"property": {"filter_info": {"conjunction": "and", "conditions": [
                             {"field_id": field_id, "operator": operator, "value": value}]}}})

    # ---------- records
    def list_records(self, tid, field_names=None, filter_=None):
        out, pt = [], None
        while True:
            body = {}
            if field_names:
                body["field_names"] = field_names
            if filter_:
                body["filter"] = filter_
            q = "?page_size=500" + ("&page_token=" + pt if pt else "")
            d = self.call("POST", f"/bitable/v1/apps/{self.app}/tables/{tid}/records/search" + q, body)
            out += d.get("items") or []
            if not d.get("has_more"):
                return out
            pt = d.get("page_token")

    def batch_create(self, tid, rows):
        ids = []
        for i in range(0, len(rows), 500):
            d = self.call("POST", f"/bitable/v1/apps/{self.app}/tables/{tid}/records/batch_create",
                          {"records": [{"fields": f} for f in rows[i:i + 500]]})
            ids += [x["record_id"] for x in d.get("records", [])]
        return ids

    def batch_update(self, tid, recs):
        for i in range(0, len(recs), 500):
            self.call("POST", f"/bitable/v1/apps/{self.app}/tables/{tid}/records/batch_update",
                      {"records": recs[i:i + 500]})


def ts_ms(dt=None):
    """Feishu datetime fields want epoch milliseconds."""
    return int((dt.timestamp() if dt else time.time()) * 1000)
