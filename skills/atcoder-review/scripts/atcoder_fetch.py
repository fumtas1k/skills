#!/usr/bin/env python3
"""AtCoder の振り返りに必要な情報をまとめて取得する（標準ライブラリのみ）。

  atcoder_fetch.py info <contest_id> [--user ID] [--root DIR]
      問題一覧・配点・difficulty・解説リンク・手元の解答の状態・順位/パフォーマンス・
      提出履歴を JSON で出力する。
  atcoder_fetch.py task <contest_id> <task_id または 問題記号>
      問題文（日本語）をプレーンテキストで出力する。
  atcoder_fetch.py editorial <url または /contests/.../editorial/NNNN>
      解説ページをプレーンテキストで出力する（数式は TeX のまま、コードはそのまま）。
  atcoder_fetch.py set-user <ID>
      AtCoder ID を config.json に保存する。

取得したページは一時ディレクトリにキャッシュするので、同じ URL を何度読んでも
AtCoder へのアクセスは 1 回で済む。

提出履歴は AtCoder Problems の API から取る。API が使えないか未反映のとき、および
順位が未確定のときは、oj（online-judge-tools）のログインセッションで AtCoder 本体の
「自分の提出」と順位表を読む（読み取りのみ。cookie.jar は書き換えない）。
"""
import argparse
import gzip
import hashlib
import html
import http.cookiejar
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True

BASE = "https://atcoder.jp"
KENKOOOO = "https://kenkoooo.com/atcoder"
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG = SKILL_DIR / "config.json"
CACHE = Path(tempfile.gettempdir()) / "atcoder-review-cache"
OJ_COOKIES = [
    Path.home() / "Library/Application Support/online-judge-tools/cookie.jar",
    Path.home() / ".local/share/online-judge-tools/cookie.jar",
]
UA = "atcoder-review-skill/1.0 (personal post-contest review)"
READS_INPUT = re.compile(r"\b(gets|STDIN|ARGF|readlines?|read)\b|\$stdin|\$<")
FETCH_ERRORS = (urllib.error.URLError, TimeoutError, OSError)

_last_request = 0.0


def clip_difficulty(d):
    """AtCoder Problems のサイトと同じく、400 未満の difficulty を正の値に補正する（clipDifficulty）。"""
    if d is None:
        return None
    return round(d if d >= 400 else 400 / math.exp(1.0 - d / 400))


def fetch(url, ttl=24 * 3600):
    """URL の本文を返す。ttl 秒以内のキャッシュがあればそれを使う。"""
    global _last_request
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / hashlib.sha1(url.encode()).hexdigest()
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return path.read_text(encoding="utf-8")
    wait = 1.0 - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read()
        if res.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    _last_request = time.time()
    text = body.decode("utf-8", errors="replace")
    path.write_text(text, encoding="utf-8")
    return text


class NotLoggedIn(OSError):
    pass


def fetch_logged_in(url, ttl=600):
    """oj のログインセッションで AtCoder 本体のページを読む。ログインが要るページ用。"""
    global _last_request
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / hashlib.sha1(("login:" + url).encode()).hexdigest()
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return path.read_text(encoding="utf-8")
    jar_path = next((p for p in OJ_COOKIES if p.exists()), None)
    if jar_path is None:
        raise NotLoggedIn("oj の cookie.jar がない（`oj login https://atcoder.jp/` が必要）")
    jar = http.cookiejar.LWPCookieJar(str(jar_path))
    jar.load(ignore_discard=True, ignore_expires=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    wait = 1.0 - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with opener.open(req, timeout=60) as res:
        if urllib.parse.urlparse(res.geturl()).path == "/login":
            raise NotLoggedIn("oj のログインセッションが切れている（`oj login https://atcoder.jp/` が必要）")
        body = res.read()
        if res.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    _last_request = time.time()
    text = body.decode("utf-8", errors="replace")
    path.write_text(text, encoding="utf-8")
    return text


def try_fetch(url, errors, label, ttl=24 * 3600):
    try:
        return fetch(url, ttl)
    except FETCH_ERRORS as e:
        errors.append(f"{label}: {e} ({url})")
        return None


def fetch_or_exit(url):
    """単発のコマンド用。失敗したらトレースバックではなく 1 行で終わる。"""
    try:
        return fetch(url)
    except FETCH_ERRORS as e:
        sys.exit(f"取得に失敗: {e} ({url})")


def to_text(fragment):
    """HTML 断片をプレーンテキストにする。<pre> の中身と TeX はそのまま残す。"""
    pres = []

    def stash(m):
        pres.append(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))))
        return f"\n@@PRE{len(pres) - 1}@@\n"

    s = re.sub(r"<(script|style)\b.*?</\1>", "", fragment, flags=re.S)
    s = re.sub(r"<pre[^>]*>(.*?)</pre>", stash, s, flags=re.S)
    s = re.sub(r'<img[^>]*\bsrc="([^"]+)"[^>]*>', r"\n[図: \1]\n", s)
    s = re.sub(r"<h[1-6][^>]*>\s*", "\n\n## ", s)
    s = re.sub(r"<li[^>]*>\s*", "\n- ", s)
    s = re.sub(r"</t[dh]>", " | ", s)
    s = re.sub(r"<(br|/p|/div|/h[1-6]|/ul|/ol|/section|/tr)[^>]*>", "\n", s)
    s = re.sub(r"<var>(.*?)</var>", r"\\(\1\\)", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = "\n".join(line.strip() for line in s.split("\n"))
    s = re.sub(r"\n{3,}", "\n\n", s)
    for i, pre in enumerate(pres):
        s = s.replace(f"@@PRE{i}@@", "```\n" + pre.strip("\n") + "\n```")
    return s.strip()


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def find_root(start):
    """リポジトリのルート（Gemfile か .agents がある場所）を上方向に探す。"""
    p = Path(start).resolve()
    for cand in [p, *p.parents]:
        if (cand / "Gemfile").exists() or (cand / ".agents").exists():
            return cand
    return p


# ---------------------------------------------------------------- info

def parse_editorial_list(block):
    """<ul> 1 つ分の HTML から解説の一覧を取り出す。"""
    eds = []
    for attrs, body in re.findall(r"<li([^>]*)>(.*?)</li>", block, re.S):
        a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', body, re.S)
        if not a:
            continue
        href = html.unescape(a.group(1))
        if href.startswith("/jump?url="):
            href = urllib.parse.unquote(href[len("/jump?url="):])
        elif href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = BASE + href
        author = re.search(r'href="/users/([^"]+)"', body)
        eds.append({
            "official": "公式" in body.split("<a", 1)[0],
            "title": re.sub(r"<[^>]+>", "", a.group(2)).strip(),
            "url": href,
            "author": author.group(1) if author else None,
            "lang": "en" if "lang-other" in attrs else "ja",
            "video": "glyphicon-film" in body,
            "pdf": href.lower().split("?")[0].endswith(".pdf"),
        })
    return eds


def parse_editorial_index(page):
    """解説一覧ページから、問題ごとの解説・コンテスト全体の解説・開催時刻を取り出す。"""
    times = re.findall(r"<time class='fixtime fixtime-full'>([^<]+)</time>", page)
    result = {"start": None, "end": None, "tasks": {}, "contest_editorials": []}
    if len(times) >= 2:
        result["start"], result["end"] = times[0], times[1]
    for part in re.split(r"<h3>", page)[1:]:
        block = part.split("</ul>")[0]
        m = re.match(r"\s*(\S+) - (.*?)\s*<a class=\"small\" href=\"/contests/[^/]+/tasks/([^\"]+)\"", part, re.S)
        if m:
            result["tasks"][m.group(3)] = {
                "label": m.group(1), "title": html.unescape(m.group(2)),
                "editorials": parse_editorial_list(block),
            }
        elif part.lstrip().startswith("コンテスト全体の解説"):
            result["contest_editorials"] = parse_editorial_list(block)
    return result


def parse_points(page):
    """コンテストのトップページの配点表から {問題記号: 配点} を取り出す。"""
    i = page.find("<h3>配点</h3>")
    if i < 0:
        return {}
    table = page[i:page.find("</table>", i)]
    rows = re.findall(r"<td[^>]*>\s*([A-Za-z0-9]+)\s*</td>\s*<td[^>]*>\s*(\d+)\s*</td>", table)
    return {label.upper(): int(pt) for label, pt in rows}


def acc_config_dirs():
    """acc の設定ディレクトリの候補。`acc config-dir` の結果を優先し、OS ごとの既定の場所で補う。"""
    try:
        res = subprocess.run(["acc", "config-dir"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            yield Path(res.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    yield Path.home() / "Library/Preferences/atcoder-cli-nodejs"
    yield Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "atcoder-cli-nodejs"
    if os.environ.get("APPDATA"):
        yield Path(os.environ["APPDATA"]) / "atcoder-cli-nodejs/Config"


def load_acc_template():
    """acc の既定テンプレートの提出ファイルを行のリストで返す。見つからなければ None。"""
    for d in acc_config_dirs():
        try:
            name = json.loads((d / "config.json").read_text(encoding="utf-8")).get("default-template")
            if not name:
                continue
            tdir = d / name
            task = json.loads((tdir / "template.json").read_text(encoding="utf-8")).get("task", {})
            submit = task.get("submit") or (task.get("program") or [None])[0]
            if submit and (tdir / submit).exists():
                return [l.rstrip() for l in (tdir / submit).read_text(encoding="utf-8").splitlines()]
        except (OSError, ValueError):
            continue
    return None


def local_state(root, contest_id, tasks, start_epoch, end_epoch, errors):
    """手元の解答ファイルの状態（未着手かどうか、更新時刻、ヘッダータグ）を調べる。"""
    cdir = root / contest_id
    acc = {}
    if (cdir / "contest.acc.json").exists():
        data = json.loads((cdir / "contest.acc.json").read_text(encoding="utf-8"))
        for t in data.get("tasks", []):
            acc[t["id"]] = t.get("directory") or {}
    template = load_acc_template()
    out = {}
    for task_id, info in tasks.items():
        try:
            d = acc.get(task_id, {})
            sub = d.get("path") or info["label"].lower()
            submit = d.get("submit") or "main.rb"
            testdir = d.get("testdir") or "tests"
            f = cdir / sub / submit
            st = {"path": str(f.relative_to(root)) if f.exists() else None, "exists": f.exists()}
            if f.exists():
                text = f.read_text(encoding="utf-8", errors="replace")
                lines = [l.rstrip() for l in text.splitlines()]
                own = [l for l in lines if l and (template is None or l not in template)]
                # テンプレートと一致、中身が空、入力を読んでいない、のどれかなら未着手
                st["untouched"] = not own or not any(
                    READS_INPUT.search(l) for l in own if not l.lstrip().startswith("#"))
                st["own_lines"] = len(own)
                st["bytes"] = len(text.encode("utf-8"))
                mtime = int(f.stat().st_mtime)
                st["modified"] = datetime.fromtimestamp(mtime).astimezone().strftime("%Y-%m-%d %H:%M:%S%z")
                if start_epoch and end_epoch:
                    st["modified_minute"] = round((mtime - start_epoch) / 60, 1)
                    st["modified_after_end"] = mtime >= end_epoch
                tags = []
                if lines and lines[0].startswith("# -"):
                    for l in lines[1:]:
                        if not l.startswith("#"):
                            break
                        tags.append(l[1:].strip())
                st["header"] = tags
                tdir = cdir / sub / testdir
                st["samples"] = len(list(tdir.glob("*.in"))) if tdir.exists() else 0
                st["test_command"] = f"cd {cdir / sub} && oj t -c 'ruby {submit}' -d {testdir}"
            out[task_id] = st
        except (OSError, ValueError, TypeError) as e:
            errors.append(f"手元のファイルの確認に失敗（{task_id}）: {e}")
            out[task_id] = None
    return out


def fetch_submissions(user, contest_id, start_epoch, errors):
    """AtCoder Problems の API から、開始時刻以降のそのコンテストへの提出を集める。"""
    subs, seen, frm = [], set(), start_epoch
    for _ in range(40):  # 1 回 500 件。上限 2 万件まで追う
        raw = try_fetch(
            f"{KENKOOOO}/atcoder-api/v3/user/submissions?user={urllib.parse.quote(user)}"
            f"&from_second={frm}", errors, "提出履歴", ttl=600)
        if raw is None:
            return None
        page = json.loads(raw)
        new = [s for s in page if s["id"] not in seen]
        seen.update(s["id"] for s in new)
        subs.extend(s for s in new if s["contest_id"] == contest_id)
        if len(page) < 500 or not new:
            break
        frm = max(s["epoch_second"] for s in page)
    return subs


def parse_submission_rows(page, contest_id):
    """AtCoder 本体の提出一覧を、AtCoder Problems の API と同じ形の dict の列にする。"""
    rows = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        sid = re.search(r"/submissions/(\d+)", row)
        at = re.search(r"<time[^>]*>([^<]+)</time>", row)
        task = re.search(r"/tasks/([A-Za-z0-9_]+)", row)
        if not (sid and at and task):
            continue
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        who = re.search(r'/users/([^"\'?]+)', row)
        result = re.search(r"<span class=['\"]label[^>]*>([^<]+)</span>", row)
        length = re.search(r"(\d+) Byte", row)
        ms = re.search(r"(\d+) ms", row)
        rows.append({
            "id": int(sid.group(1)),
            "epoch_second": int(datetime.strptime(at.group(1).strip(), "%Y-%m-%d %H:%M:%S%z").timestamp()),
            "problem_id": task.group(1), "contest_id": contest_id,
            "user_id": who.group(1) if who else None,
            "language": cells[3] if len(cells) > 3 else None,
            "result": result.group(1).strip() if result else None,
            "length": int(length.group(1)) if length else None,
            "execution_time": int(ms.group(1)) if ms else None,
        })
    return rows


def fetch_submissions_atcoder(user, contest_id, errors):
    """AtCoder 本体の「自分の提出」から、そのコンテストへの提出を集める（oj のセッションを使う）。"""
    subs = []
    for page_no in range(1, 21):  # 1 ページ 20 件
        url = f"{BASE}/contests/{contest_id}/submissions/me?page={page_no}"
        try:
            rows = parse_submission_rows(fetch_logged_in(url), contest_id)
        except (*FETCH_ERRORS, ValueError) as e:
            errors.append(f"提出履歴（AtCoder 本体）: {e} ({url})")
            return None
        if any(r["user_id"] != user for r in rows):
            errors.append(f"提出履歴（AtCoder 本体）: oj でログイン中のアカウントが {user} ではない")
            return None
        subs.extend(rows)
        if len(rows) < 20:
            break
    return subs


def fetch_provisional_result(user, contest_id, errors):
    """結果が未確定のあいだ、順位表から暫定の順位を取る（oj のセッションを使う）。"""
    url = f"{BASE}/contests/{contest_id}/standings/json"
    try:
        rows = json.loads(fetch_logged_in(url, ttl=1800)).get("StandingsData", [])
    except (*FETCH_ERRORS, ValueError) as e:
        errors.append(f"順位表（AtCoder 本体）: {e} ({url})")
        return None
    for r in rows:
        if r.get("UserScreenName") == user:
            return {
                "place": r.get("Rank"), "rated": r.get("IsRated"),
                "old_rating": r.get("OldRating") or r.get("Rating"),
                "performance": None, "new_rating": None, "provisional": True,
            }
    return None


def summarize_submissions(subs, start_epoch, end_epoch):
    by_task = {}
    for s in sorted(subs, key=lambda s: s["epoch_second"]):
        t = by_task.setdefault(s["problem_id"], {
            "during_contest": [], "after_contest": [],
            "accepted_in_contest": False, "accepted_minute": None,
            "wrong_before_ac": 0, "accepted_after_contest": False,
        })
        entry = {
            "id": s["id"], "result": s["result"], "language": s["language"],
            "minute": round((s["epoch_second"] - start_epoch) / 60, 1),
            "exec_ms": s.get("execution_time"), "length": s.get("length"),
            "url": f"{BASE}/contests/{s['contest_id']}/submissions/{s['id']}",
        }
        if s["epoch_second"] < end_epoch:
            t["during_contest"].append(entry)
            if s["result"] == "AC" and not t["accepted_in_contest"]:
                t["accepted_in_contest"] = True
                t["accepted_minute"] = entry["minute"]
            elif not t["accepted_in_contest"] and s["result"] not in ("CE", "WJ", "IE"):
                t["wrong_before_ac"] += 1
        else:
            t["after_contest"].append(entry)
            if s["result"] == "AC":
                t["accepted_after_contest"] = True
    return by_task


def cmd_info(args):
    cid = args.contest.lower()
    root = find_root(args.root or os.getcwd())
    user = args.user or os.environ.get("ATCODER_USER") or load_config().get("user")
    errors, notes = [], []
    out = {"contest_id": cid, "url": f"{BASE}/contests/{cid}", "user": user}

    page = try_fetch(f"{BASE}/contests/{cid}/editorial?lang=ja", errors, "解説一覧", ttl=1800)
    index = parse_editorial_index(page) if page else {
        "start": None, "end": None, "tasks": {}, "contest_editorials": []}
    out["start"], out["end"] = index["start"], index["end"]
    tasks = index["tasks"]
    if not tasks:
        # 解説一覧が読めないときは contest.acc.json だけで続ける
        acc = root / cid / "contest.acc.json"
        if acc.exists():
            for t in json.loads(acc.read_text(encoding="utf-8")).get("tasks", []):
                tasks[t["id"]] = {"label": t["label"], "title": t["title"], "editorials": []}

    top = try_fetch(f"{BASE}/contests/{cid}?lang=ja", errors, "配点", ttl=24 * 3600) if tasks else None
    points = parse_points(top) if top else {}
    models = try_fetch(f"{KENKOOOO}/resources/problem-models.json", errors, "difficulty", ttl=3600)
    models = json.loads(models) if models else {}

    start_epoch = end_epoch = None
    if out["start"] and out["end"]:
        fmt = "%Y-%m-%d %H:%M:%S%z"
        start_epoch = int(datetime.strptime(out["start"], fmt).timestamp())
        end_epoch = int(datetime.strptime(out["end"], fmt).timestamp())
        out["duration_minutes"] = (end_epoch - start_epoch) // 60

    local = local_state(root, cid, tasks, start_epoch, end_epoch, errors)
    if tasks and not (root / cid).is_dir():
        notes.append(f"手元に {cid}/ がない（探した場所: {root}）。解答ファイルの状態は取得していない。")

    subs_by_task = {}
    if user:
        res = try_fetch(f"{BASE}/contests/{cid}/results/json", errors, "順位表", ttl=1800)
        mine = [r for r in json.loads(res) if r.get("UserScreenName") == user] if res else []
        if not mine:
            provisional = fetch_provisional_result(user, cid, errors)
            if provisional:
                out["result"] = provisional
                notes.append("順位は順位表からの暫定値（結果が未確定）。パフォーマンスとレート変化はまだ出ていない。")
            elif res:
                notes.append(f"順位表に {user} がいない（コンテスト中は不参加、結果が未確定、ID 違いのいずれか）。")
        if res:
            if mine:
                r = mine[0]
                out["result"] = {
                    "place": r.get("Place"), "rated": r.get("IsRated"),
                    "old_rating": r.get("OldRating"),
                    # unrated 参加ではパフォーマンスが 0、レートが据え置きで返るので出さない
                    "performance": r.get("Performance") if r.get("IsRated") else None,
                    "new_rating": r.get("NewRating") if r.get("IsRated") else None,
                }
        if start_epoch:
            subs = fetch_submissions(user, cid, start_epoch, errors)
            from_atcoder = False
            if subs is None or (not subs and time.time() - end_epoch < 24 * 3600):
                # AtCoder Problems が使えないか未反映のときは、本体から取る
                direct = fetch_submissions_atcoder(user, cid, errors)
                if direct is not None:
                    subs, from_atcoder = direct, True
                    notes.append("提出履歴は AtCoder 本体から取得した（AtCoder Problems が使えないか未反映のため、"
                                 "oj のログインセッションを使用）。")
            if subs is not None:
                subs_by_task = summarize_submissions(subs, start_epoch, end_epoch)
                if not subs and not from_atcoder and time.time() - end_epoch < 24 * 3600:
                    notes.append("提出履歴が 0 件。AtCoder Problems への反映はコンテスト終了から数時間"
                                 "遅れることがあるので、本人に提出状況を聞く。")
                elif not subs:
                    notes.append(f"{user} のこのコンテストへの提出は 0 件。")
                elif not any(t["during_contest"] for t in subs_by_task.values()):
                    notes.append("提出はすべてコンテスト終了後（バーチャル参加か後日の練習）。"
                                 "AC 時刻とペナルティは本番のものではない。")
    else:
        notes.append("AtCoder ID が未設定。順位・パフォーマンス・提出履歴は取得していない。"
                     "本人に ID を聞き、`atcoder_fetch.py set-user <ID>` で保存してから info を取り直す。")

    out["contest_editorials"] = index["contest_editorials"]
    out["tasks"] = []
    for task_id, info in tasks.items():
        model = models.get(task_id, {})
        out["tasks"].append({
            "id": task_id, "label": info["label"], "title": info["title"],
            "url": f"{BASE}/contests/{cid}/tasks/{task_id}",
            "points": points.get(info["label"].upper()),
            "difficulty": clip_difficulty(model.get("difficulty")),
            "raw_difficulty": model.get("difficulty"),
            "difficulty_is_experimental": model.get("is_experimental"),
            "local": local.get(task_id),
            "submissions": subs_by_task.get(task_id),
            "editorials": info["editorials"],
        })
    if tasks and all(t["difficulty"] is None for t in out["tasks"]):
        notes.append("difficulty が未算出（コンテスト直後は出ない）。配点（points）で難度を見積もる。")
    readable = lambda eds: any(e["official"] and e["lang"] == "ja" and not e["video"] and not e["pdf"] for e in eds)
    if tasks and not any(readable(t["editorials"]) for t in out["tasks"]):
        if index["contest_editorials"]:
            notes.append("問題ごとの公式解説がない。contest_editorials（コンテスト全体の解説。"
                         "PDF のことが多い）を WebFetch か Read で読む。")
        else:
            notes.append("公式解説がまだ公開されていない。")
    out["notes"], out["errors"] = notes, errors
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    if not tasks:
        sys.exit(1)


# ---------------------------------------------------------------- task / editorial

def resolve_task_id(cid, task):
    """問題記号（a, f など）を task_id に直す。古いコンテストは abc002_1 のような ID を持つ。"""
    task = task.lower()
    if "_" in task:
        return task
    try:
        index = parse_editorial_index(fetch(f"{BASE}/contests/{cid}/editorial?lang=ja", ttl=1800))
        for task_id, info in index["tasks"].items():
            if info["label"].lower() == task:
                return task_id
    except FETCH_ERRORS:
        pass
    return f"{cid}_{task}"


def cmd_task(args):
    cid = args.contest.lower()
    task = resolve_task_id(cid, args.task)
    page = fetch_or_exit(f"{BASE}/contests/{cid}/tasks/{task}?lang=ja")
    title = re.search(r'<span class="h2">\s*(.*?)\s*<a', page, re.S)
    limits = re.search(r"実行時間制限[^<]*", page)
    m = re.search(r'<span class="lang-ja">(.*?)</span>\s*<span class="lang-en">', page, re.S)
    if m:
        body = m.group(1)
    else:
        i = page.find('id="task-statement"')
        i = page.find(">", i) + 1 if i >= 0 else 0
        j = page.find('<div id="task-statement-end"', i)
        k = page.find("<hr", i)
        ends = [x for x in (j, k) if x > 0]
        body = page[i:min(ends) if ends else len(page)]
    print(f"# {to_text(title.group(1)) if title else task}")
    if limits:
        print(limits.group(0).strip())
    print()
    print(to_text(body))


def cmd_editorial(args):
    url = args.url
    if url.startswith("/"):
        url = BASE + url
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "atcoder.jp" or "/editorial/" not in parsed.path:
        sys.exit("このコマンドで読めるのは atcoder.jp/contests/<id>/editorial/<番号> だけ。"
                 "ブログや PDF は WebFetch か Read で読む: " + url)
    if "lang=" not in url:
        url += ("&" if "?" in url else "?") + "lang=ja"
    page = fetch_or_exit(url)
    heads = list(re.finditer(r"<h2[^>]*>", page))
    start = heads[-1].start() if heads else 0
    end = page.find("投稿日時", start)
    body = page[start:end if end > 0 else len(page)]
    # 見出しは「D - 問題名 解説 by 著者」の 1 行にまとめる（中の改行やアイコン画像を落とす）
    body = re.sub(r"<h2[^>]*>(.*?)</h2>",
                  lambda m: "<h2>" + " ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split()) + "</h2>",
                  body, flags=re.S)
    print(to_text(body))


def cmd_set_user(args):
    cfg = load_config()
    cfg["user"] = args.user
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved: {CONFIG}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info")
    p.add_argument("contest")
    p.add_argument("--user")
    p.add_argument("--root")
    p.set_defaults(func=cmd_info)
    p = sub.add_parser("task")
    p.add_argument("contest")
    p.add_argument("task")
    p.set_defaults(func=cmd_task)
    p = sub.add_parser("editorial")
    p.add_argument("url")
    p.set_defaults(func=cmd_editorial)
    p = sub.add_parser("set-user")
    p.add_argument("user")
    p.set_defaults(func=cmd_set_user)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
