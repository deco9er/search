# -*- coding: utf-8 -*-

import os, sys, re, time, json, threading
import html as html_lib
import urllib.request, urllib.parse, urllib.error
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("[!] pip install colorama")
    sys.exit(1)

G   = Fore.GREEN
C   = Fore.CYAN
Y   = Fore.YELLOW
R   = Fore.RED
W   = Fore.WHITE
DIM = Style.DIM
B   = Style.BRIGHT
RST = Style.RESET_ALL

# ── лого ────────────────────────────────────────────────────
LOGO = r"""
  ██████╗  ███████╗  ██████╗  ██████╗   █████╗  ███████╗ ██████╗
  ██╔══██╗ ██╔════╝ ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝ ██╔══██╗
  ██║  ██║ █████╗   ██║      ██║   ██║ ╚██████║ █████╗   ██████╔╝
  ██║  ██║ ██╔══╝   ██║      ██║   ██║  ╚═══██║ ██╔══╝   ██╔══██╗
  ██████╔╝ ███████╗ ╚██████╗ ╚██████╔╝  █████╔╝ ███████╗ ██║  ██║
  ╚═════╝  ╚══════╝  ╚═════╝  ╚═════╝   ╚════╝  ╚══════╝ ╚═╝  ╚═╝
"""
TAGLINE = "  // INTERNAL SEARCH // v1.0.0 (beta)// pure stdlib + mistral api //"
DIV     = "  " + "═" * 68
DIV_S   = "  " + "─" * 68

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def ts():
    return datetime.now().strftime("%H:%M:%S")

def div(thin=False):
    print(f"{DIM}{G}{DIV_S if thin else DIV}{RST}")

def print_logo():
    for line in LOGO.splitlines():
        print(f"{B}{G}{line}{RST}")
        time.sleep(0.03)
    print(f"{DIM}{C}{TAGLINE}{RST}\n")

def status_bar():
    dot  = f"{B}{G}●{RST}"
    left = f"  {dot} {DIM}{G}SYSTEM ONLINE // MISTRAL{RST}"
    right= f"{DIM}{G}[{ts()}]{RST}"
    print(left + " " * 12 + right)

# ── спиннер ─────────────────────────────────────────────────
FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
MSGS   = [
    "ПАРСИНГ DUCKDUCKGO",
    "СКРАПИНГ РЕЗУЛЬТАТОВ",
    "ЗАПРОС К MISTRAL API",
    "СИНТЕЗ ОТВЕТА",
    "ГЕНЕРАЦИЯ СВОДКИ",
]

class Spinner:
    def __init__(self):
        self._stop   = threading.Event()
        self._thread = None
        self._idx    = 0

    def _run(self):
        i = t = 0
        while not self._stop.is_set():
            msg = MSGS[self._idx % len(MSGS)]
            sys.stdout.write(f"\r  {B}{G}{FRAMES[i%len(FRAMES)]}{RST} {DIM}{G}{msg}...{RST}   ")
            sys.stdout.flush()
            time.sleep(0.09)
            i += 1; t += 1
            if t >= 14:
                self._idx += 1; t = 0

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join()
        sys.stdout.write(f"\r{' '*72}\r")
        sys.stdout.flush()

# ── DDG скрапинг ─────────────────────────────────────────────
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def _strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()

def web_search(query, n=6):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ru,en"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return [{"title": "Ошибка сети", "url": "", "snippet": str(e)}]

    results = []
    blocks = re.findall(r'<div class="result(?:\s[^"]*)?">.*?</div>\s*</div>', body, re.DOTALL)
    for block in blocks[:n]:
        mt = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL)
        mu = re.search(r'href="([^"]+)"', block)
        ms = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', block, re.DOTALL)
        if not (mt and ms): continue

        title   = html_lib.unescape(_strip_tags(mt.group(1)))
        snippet = html_lib.unescape(_strip_tags(ms.group(1)))
        raw_url = mu.group(1) if mu else ""
        m_uddg  = re.search(r"uddg=([^&]+)", raw_url)
        url_out = urllib.parse.unquote(m_uddg.group(1)) if m_uddg else raw_url

        if snippet:
            results.append({"title": title, "url": url_out, "snippet": snippet})

    # fallback
    if not results:
        ta = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', body, re.DOTALL)
        sa = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', body, re.DOTALL)
        for t, s in zip(ta[:n], sa[:n]):
            results.append({
                "title":   html_lib.unescape(_strip_tags(t)),
                "url":     "",
                "snippet": html_lib.unescape(_strip_tags(s)),
            })

    return results

# ── Mistral API через urllib ──────────────────────────────────
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

SYSTEM = """Ты — мощный поисковый ассистент в стиле хакерского терминала.
Тебе дан запрос и сниппеты из интернета. Синтезируй краткую сводку.

ФОРМАТ (строго):
[HEAD] Заголовок
[•] ключевой факт
[•] ещё факт
[SRC] источник
[NOTE] примечание (если важно)

Правила:
- Язык ответа = язык запроса
- 4–8 пунктов [•], 1–2 секции [HEAD]
- Опирайся на сниппеты, не выдумывай
- Только суть, никакой воды"""

def mistral_chat(api_key, messages, model="mistral-large-latest", max_tokens=900):
    payload = json.dumps({
        "model":      model,
        "messages":   messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        MISTRAL_URL,
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept":        "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip(), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return None, f"HTTP {e.code}: {body[:200]}"
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}"
    except Exception as e:
        return None, str(e)

# ── рендер ───────────────────────────────────────────────────
def render(query, text, sources):
    print()
    div()
    print(f"  {B}{G}✓{RST} {DIM}{G}[{ts()}] ЗАПРОС:{RST} {B}{W}{query}{RST}")
    div(thin=True)
    print()

    for line in text.splitlines():
        s = line.strip()
        if not s:
            print(); continue

        if s.startswith("[HEAD]"):
            txt = s[6:].strip()
            print(f"  {B}{C}◆  {txt}{RST}")
            print(f"  {DIM}{C}{'─'*(len(txt)+4)}{RST}")
        elif s.startswith("[•]") or s.startswith("[·]"):
            print(f"  {G}  ▸{RST} {W}{s[3:].strip()}{RST}")
        elif s.startswith("[SRC]"):
            print(f"  {DIM}{G}  └─ SRC: {s[5:].strip()}{RST}")
        elif s.startswith("[NOTE]"):
            print(f"  {B}{Y}  ⚑{RST} {Y}{s[6:].strip()}{RST}")
        elif s[:2] in ("• ", "- ", "* "):
            print(f"  {G}  ▸{RST} {W}{s[2:].strip()}{RST}")
        elif re.match(r"^#{1,3} ", s):
            h = re.sub(r"^#+\s*", "", s)
            print(f"  {B}{C}◆  {h}{RST}")
        else:
            print(f"  {DIM}{W}{s}{RST}")

    if sources:
        print()
        div(thin=True)
        print(f"  {DIM}{G}SOURCES:{RST}")
        for i, r in enumerate(sources[:4], 1):
            t = r.get("title","")[:60]
            u = r.get("url","") or "—"
            print(f"  {DIM}{G}[{i}]{RST} {DIM}{W}{t}{RST}")
            if u != "—":
                print(f"      {DIM}{G}└─ {u[:70]}{RST}")

    print()
    div(thin=True)
    print(f"  {DIM}{G}// [DONE] [{ts()}]{RST}")
    div()

# ── поиск ────────────────────────────────────────────────────
def do_search(api_key, query):
    sp = Spinner()
    sp.start()

    results = web_search(query)
    context = "\n\n".join(
        f"[{i}] {r['title']}\n    {r['snippet']}\n    URL: {r['url']}"
        for i, r in enumerate(results, 1)
    ) or "Результаты недоступны."

    answer, err = mistral_chat(api_key, [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": f"Запрос: {query}\n\nРезультаты:\n{context}"},
    ])

    sp.stop()

    if err:
        if "401" in err or "Unauthorized" in err:
            print(f"\n  {R}// [ERROR] Неверный API ключ (401){RST}")
            print(f"  {Y}// Создай новый: https://console.mistral.ai → API Keys{RST}")
            print(f"  {Y}// Затем введи /key{RST}")
        else:
            print(f"\n  {R}// [ERROR] {err}{RST}")
        return

    render(query, answer, results)

# ── хелп ─────────────────────────────────────────────────────


def print_help():
    print(f"\n  {B}{C}КОМАНДЫ:{RST}")
    for cmd, desc in [("/help","справка"),("/clear","очистить"),
                      ("/key","сменить ключ"),("/exit","выход")]:
        print(f"  {G}  {cmd:<10}{RST} {DIM}{W}{desc}{RST}")
    print()



# ── ключ ─────────────────────────────────────────────────────
def get_key():
    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if key:
        print(f"  {DIM}{G}// ключ из MISTRAL_API_KEY{RST}")
        return key
    print(f"  {DIM}{G}// Введи Mistral API ключ{RST}")
    print(f"  {DIM}{G}// Получить: https://console.mistral.ai → API Keys{RST}")
    print(f"  {B}{G}▶ {RST}", end="")
    key = input().strip()
    if not key:
        print(f"  {R}// пустой ключ — выход{RST}")
        sys.exit(1)
    return key

# ── main ─────────────────────────────────────────────────────
def main():
    clear()
    print_logo()
    status_bar()
    div()
    print()

    api_key = get_key()

    print()
    div(thin=True)
    print_help()
    div()

    while True:
        try:
            print(f"\n  {DIM}{G}deco9er@search:~${RST} ", end="")
            raw = input().strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {DIM}{G}// bye.{RST}\n")
            break

        if not raw:
            continue

        cmd = raw.lower()

        if cmd in ("/exit", "/quit", "exit", "quit", "q"):
            print(f"\n  {DIM}{G}// bye.{RST}\n"); break
        elif cmd == "/help":
            print_help()
        elif cmd == "/clear":
            clear(); print_logo(); status_bar(); div()
        elif cmd == "/key":
            print(f"  {DIM}{G}▶ новый ключ: {RST}", end="")
            nk = input().strip()
            if nk:
                api_key = nk
                print(f"  {G}// ключ обновлён{RST}")
        elif cmd.startswith("/"):
            print(f"  {R}// неизвестная команда. /help{RST}")
        elif raw.isdigit() and 1 <= int(raw) <= len(EXAMPLES):
            q = EXAMPLES[int(raw) - 1]
            print(f"  {DIM}{G}// запрос: {q}{RST}")
            do_search(api_key, q)
        else:
            do_search(api_key, raw)

if __name__ == "__main__":
    main()
