#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "speaker_cards_payload.json"
HTML_OUT = ROOT / "Star-DART-OPC-复赛路演手卡_PingFang.html"
SCRIPT_OUT = ROOT.parent / "Star-DART-OPC-复赛路演讲稿_终稿PPT对齐版.md"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    cards = payload["cards"]
    pages: list[str] = []
    for idx, card in enumerate(cards, start=1):
        paragraphs = "\n".join(f"<p>{esc(p)}</p>" for p in card.get("paragraphs", []))
        pages.append(
            f"""
            <section class="page">
              <div class="accent"></div>
              <header>
                <div class="page-count">第 {idx} / {len(cards)} 页</div>
                <div class="time">{esc(card.get("time", ""))}</div>
              </header>
              <h1>{esc(card.get("title", f"Page {idx}"))}</h1>
              <main>{paragraphs}</main>
              <footer>{esc(payload.get("footer", ""))}</footer>
            </section>
            """
        )

    doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{esc(payload.get("title", "Speaker Cards"))}</title>
  <style>
    @page {{
      size: A4 landscape;
      margin: 0;
    }}
    * {{
      box-sizing: border-box;
    }}
    html, body {{
      margin: 0;
      background: #eef3f7;
      color: #1f2933;
      font-family: "PingFang SC", "PingFang UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      font-variant-east-asian: proportional-width;
      -webkit-font-smoothing: antialiased;
      print-color-adjust: exact;
      -webkit-print-color-adjust: exact;
    }}
    .page {{
      position: relative;
      width: 297mm;
      height: 210mm;
      padding: 22mm 24mm 18mm;
      page-break-after: always;
      background: #f7f9fc;
      overflow: hidden;
    }}
    .page::before {{
      content: "";
      position: absolute;
      inset: 13mm;
      border: 1.2px solid #d8e1ea;
      border-radius: 5mm;
      background: #ffffff;
      z-index: 0;
    }}
    .accent {{
      position: absolute;
      left: 13mm;
      right: 13mm;
      top: 13mm;
      height: 3mm;
      background: #1976a3;
      z-index: 1;
    }}
    header, h1, main, footer {{
      position: relative;
      z-index: 1;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin: 0 0 11mm;
      color: #4c5967;
      font-size: 15pt;
      font-weight: 500;
    }}
    h1 {{
      margin: 0 0 11mm;
      color: #18212b;
      font-size: 29pt;
      line-height: 1.14;
      font-weight: 650;
      letter-spacing: 0;
    }}
    main {{
      height: 125mm;
      overflow: hidden;
    }}
    p {{
      margin: 0 0 6.2mm;
      font-size: 18.5pt;
      line-height: 1.48;
      font-weight: 420;
      letter-spacing: 0;
      overflow-wrap: break-word;
      word-break: normal;
    }}
    footer {{
      position: absolute;
      right: 24mm;
      bottom: 17mm;
      color: #7792a3;
      font-size: 10.5pt;
      font-weight: 400;
    }}
  </style>
</head>
<body>
{''.join(pages)}
</body>
</html>
"""
    HTML_OUT.write_text(doc, encoding="utf-8")
    script_lines = [
        "# Star-DART OPC 复赛路演讲稿（终稿 PPT 对齐版）",
        "",
        "> 来源：根据 `Star-DART OPC 复赛路演 终稿.pptx` 的 10 页终稿结构，对齐原讲稿重排。",
        "> 调整：原讲稿第 6 页“实现过程与当前闭环”压缩并入第 5 页；原第 7 页起顺延对齐 PPT 第 6-10 页。",
        "",
    ]
    for idx, card in enumerate(cards, start=1):
        script_lines.append(f"## 第 {idx} 页｜{card.get('title', f'Page {idx}')}")
        script_lines.append("")
        if card.get("time"):
            script_lines.append(f"> 建议时间：{card['time']}")
            script_lines.append("")
        for paragraph in card.get("paragraphs", []):
            script_lines.append(str(paragraph))
            script_lines.append("")
    SCRIPT_OUT.write_text("\n".join(script_lines).rstrip() + "\n", encoding="utf-8")
    print(HTML_OUT)
    print(SCRIPT_OUT)


if __name__ == "__main__":
    main()
