"""index.html → 단독 실행 파일(downloads) 로 만들기
   · 그림은 data URI 로 넣고, PWA <link> 는 지웁니다
   · progress.html 을 base64 로 단독 파일 안에 넣어 📅 진도표 버튼이 file:// 에서도 새 창으로 열리게 합니다
"""
import base64
import glob
import os
import re

SRC = "index.html"
PROGRESS = "progress.html"
OUT = "/workspace/downloads/우리집_가족_대시보드.html"

DROP_LINE = re.compile(
    r'^\s*<link[^>]+(manifest\.webmanifest|icons/(icon-\d+|favicon-\d+|apple-touch-icon))[^>]*>\s*$'
    r'|^\s*<meta[^>]+(apple-mobile-web-app|mobile-web-app-capable)[^>]*>\s*$'
)
TPL = re.compile(r'(<script type="text/template" id="progressPageB64">)(.*?)(</script>)', re.S)


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def main():
    html = open(SRC, encoding="utf-8").read()
    lines = [ln for ln in html.split("\n") if not DROP_LINE.match(ln)]
    html = "\n".join(lines)

    n = 0
    for p in sorted(glob.glob("assets/**/*.png", recursive=True)):
        key = p.replace(os.sep, "/")
        if key in html:
            html = html.replace(key, data_uri(p))
            n += 1
    assert "assets/" not in html, "인라인되지 않은 그림이 남아 있어요"

    prog = open(PROGRESS, encoding="utf-8").read()
    b64 = base64.b64encode(prog.encode("utf-8")).decode()
    assert "/" not in b64[:0]  # noop
    html, sub = TPL.subn(lambda m: m.group(1) + b64 + m.group(3), html)
    assert sub == 1, "진도표를 넣을 자리(#progressPageB64)를 찾지 못했어요"

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", OUT, len(html), "bytes · inlined", n, "images · progress.html", len(prog), "chars")


main()
