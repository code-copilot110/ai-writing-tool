#!/usr/bin/env python3
"""AIライティングツール用の機械的なセキュリティチェック。

標準ライブラリのみ（システムの Python 3.9 で動く）。ファイルは書き換えない。
出力は「調査の手がかり」であり最終判定ではない。判断は SKILL.md の手順で人（Claude）が行う。
秘密の値は絶対に出力しない（先頭4文字だけ見せて伏せる）。

使い方: python3 scan.py [プロジェクトのルート（省略時はカレント）]
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules", ".agents", ".claude", ".mypy_cache"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".json", ".sh", ".command", ".env", ""}
MAX_BYTES = 1_000_000

SECRET_PATTERNS = [
    ("Google APIキー", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("OpenAI 形式のキー", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("GitHub トークン", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("AWS アクセスキー", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("秘密鍵", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("キー代入（値あり）", re.compile(r"(?i)\b\w*(api[_-]?key|secret|token|password)\w*\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}")),
]

CODE_PATTERNS = [
    ("HIGH", "eval-exec", re.compile(r"\b(eval|exec)\s*\("), "動的コード実行"),
    ("HIGH", "shell", re.compile(r"\b(os\.system|shell\s*=\s*True)"), "シェル経由のコマンド実行"),
    ("MEDIUM", "subprocess", re.compile(r"\bsubprocess\."), "外部コマンド実行"),
    ("HIGH", "pickle", re.compile(r"\b(pickle|marshal)\.loads?\("), "信頼できないデータのデシリアライズ"),
    ("HIGH", "yaml-load", re.compile(r"\byaml\.load\((?!.*SafeLoader)"), "yaml.load（safe_load でない）"),
    ("HIGH", "tls-off", re.compile(r"verify\s*=\s*False"), "TLS 検証の無効化"),
    ("HIGH", "raw-html", re.compile(r"unsafe_allow_html\s*=\s*True|\bst\.html\(|components\.html\("), "生 HTML の描画（XSS の入口）"),
    ("LOW", "outbound-http", re.compile(r"\b(requests|httpx|urllib\.request)\.\w+\("), "外部への HTTP 通信（宛先がユーザー入力由来なら SSRF）"),
    ("MEDIUM", "key-logging", re.compile(r"(print|logging\.\w+|logger\.\w+|st\.(write|code|json))\(.*(api_key|settings)"), "キー/設定の出力の疑い"),
    ("LOW", "error-echo", re.compile(r"st\.(error|warning|exception)\(.*\{e[.}!:]?"), "例外内容の画面表示（キーや内部情報の混入がないか確認）"),
    ("INFO", "markdown-sink", re.compile(r"\bst\.(markdown|write)\("), "モデル出力の Markdown 描画（画像/リンク経由の情報流出。references/checks.md #2）"),
]


def emit(sev: str, code: str, where: str, msg: str) -> None:
    print(f"[{sev:<6}] {code:<14} {where}  {msg}")


def mask(s: str) -> str:
    return s[:4] + "…(伏せ字)"


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in TEXT_SUFFIXES or name.startswith(".env"):
                try:
                    if p.stat().st_size <= MAX_BYTES:
                        yield p
                except OSError:
                    pass


def read_lines(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def check_secrets_and_code(root: Path) -> None:
    for p in iter_files(root):
        rel = p.relative_to(root)
        is_env = p.name == ".env"
        is_example = p.name.endswith(".example")
        for i, line in enumerate(read_lines(p), 1):
            if not is_env and not is_example:
                for label, rx in SECRET_PATTERNS:
                    m = rx.search(line)
                    if m:
                        emit("HIGH", "secret", f"{rel}:{i}", f"{label} らしき文字列 {mask(m.group(0))}")
            if p.suffix == ".py":
                for sev, code, rx, msg in CODE_PATTERNS:
                    if rx.search(line):
                        emit(sev, code, f"{rel}:{i}", msg)


def check_env_and_gitignore(root: Path) -> None:
    gi = root / ".gitignore"
    ignored = gi.exists() and any(l.strip() in {".env", ".env*", "*.env"} for l in read_lines(gi))
    if not gi.exists():
        emit("HIGH", "gitignore", ".gitignore", "ファイルが無い（git 化した時に .env が入る）")
    elif not ignored:
        emit("HIGH", "gitignore", ".gitignore", ".env が除外されていない")
    else:
        emit("OK", "gitignore", ".gitignore", ".env は除外済み")

    env = root / ".env"
    if env.exists():
        mode = env.stat().st_mode & 0o777
        if mode & 0o077:
            emit("MEDIUM", "env-perms", ".env", f"権限が {oct(mode)}（他ユーザーが読める。chmod 600 を推奨）")
        else:
            emit("OK", "env-perms", ".env", f"権限 {oct(mode)}")
        has_val = any(re.match(r"\s*\w+\s*=\s*\S+", l) for l in read_lines(env) if not l.lstrip().startswith("#"))
        emit("INFO", "env-present", ".env", "存在する（値は読まない）" + ("・値あり" if has_val else "・値は空"))
    else:
        emit("INFO", "env-present", ".env", "無い（キーはサイドバー入力運用と推測）")

    if (root / ".git").exists() and shutil.which("git"):
        r = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", ".env"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            emit("HIGH", "env-tracked", ".env", "git で追跡されている（履歴にも残る）")
    else:
        emit("INFO", "git", ".", "git リポジトリではない（履歴漏洩の確認は不要。git init 時は .gitignore を先に）")


def key_is_shared(root: Path) -> bool:
    """サーバー側にキーが保存されているか。あれば全セッション（=LANの他人）がそのキーを使える。
    サイドバー入力のキーはセッションごとなので他人は使えない。"""
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return True
    return any(re.match(r"\s*GEMINI_API_KEY\s*=\s*\S+", l) for l in read_lines(root / ".env"))


def exposure_severity(shared: bool) -> tuple:
    if shared:
        return "HIGH", "サーバーにキーが保存済み。LAN の誰でもそのキーで生成できる"
    return "LOW", "キーは都度入力（セッション別）なので他人は自分のキーが要る。.env にキーを置くと HIGH になる"


def check_server_binding(root: Path, shared: bool) -> None:
    sources = [root / "start.command", root / ".streamlit" / "config.toml", Path.home() / ".streamlit" / "config.toml"]
    sources += [p for p in root.glob("*.sh")]
    text = ""
    for p in sources:
        for i, line in enumerate(read_lines(p), 1):
            if re.search(r"server[.\s]*address|^\s*address\s*=", line, re.I):
                emit("INFO", "bind-config", f"{p.name}:{i}", line.strip())
                text += line
            if re.search(r"enableXsrfProtection\s*=\s*false|server\.enableXsrfProtection[= ]false", line, re.I):
                emit("HIGH", "xsrf-off", f"{p.name}:{i}", "XSRF 保護が無効")
            if re.search(r"enableCORS\s*=\s*false|server\.enableCORS[= ]false", line, re.I):
                emit("MEDIUM", "cors-off", f"{p.name}:{i}", "CORS 保護が無効")
    sev, why = exposure_severity(shared)
    if re.search(r"0\.0\.0\.0", text):
        emit(sev, "bind", "起動設定", "0.0.0.0 で待ち受ける設定。" + why)
    elif not re.search(r"(localhost|127\.0\.0\.1)", text):
        emit(sev, "bind", "start.command / config.toml",
             "待ち受けアドレスの指定が無く、既定は全インターフェース（LAN から到達可）。" + why +
             "。--server.address localhost を推奨")
    else:
        emit("OK", "bind", "起動設定", "localhost に限定されている")


def check_listeners(shared: bool) -> None:
    if not shutil.which("lsof"):
        emit("INFO", "listen", "-", "lsof が無いため実機確認を省略")
        return
    r = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], capture_output=True, text=True)
    found = False
    seen = set()
    for line in r.stdout.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 9 or not re.search(r"(?i)python|streamlit", cols[0]):
            continue
        addr = cols[8]
        if (cols[1], addr) in seen:  # IPv4/IPv6 の二重待ち受けは1件にまとめる
            continue
        seen.add((cols[1], addr))
        found = True
        if addr.startswith(("*:", "[::]:", "0.0.0.0:")):
            emit(exposure_severity(shared)[0], "listen", addr,
                 f"{cols[0]}(pid {cols[1]}) が全インターフェースで待ち受け中（実機確認）。" + exposure_severity(shared)[1])
        else:
            emit("OK", "listen", addr, f"{cols[0]}(pid {cols[1]}) はローカル限定（実機確認）")
    if not found:
        emit("INFO", "listen", "-", "Python の待ち受けプロセスなし（未起動。静的な設定判断のみ）")


def check_dependencies(root: Path) -> None:
    req = root / "requirements.txt"
    for i, line in enumerate(read_lines(req), 1):
        s = line.strip()
        if s and not s.startswith("#") and "==" not in s and "<" not in s:
            emit("LOW", "dep-unpinned", f"requirements.txt:{i}", f"{s} は上限・固定なし（更新で挙動/脆弱性が変わりうる）")
    exe = shutil.which("pip-audit") or str(root / ".venv/bin/pip-audit")
    if exe and Path(exe).exists() and req.exists():
        r = subprocess.run([exe, "-r", str(req), "--progress-spinner", "off"], capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        emit("HIGH" if r.returncode else "OK", "pip-audit", "requirements.txt", out.splitlines()[-1] if out else "実行済み")
        if r.returncode:
            print(out)
    else:
        emit("INFO", "pip-audit", "-", "未導入のため脆弱性DB照合は未実施（導入は依存の追加なので、ユーザーに確認してから）")


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(f"# security-check scan: {root}\n# 対象外: {', '.join(sorted(SKIP_DIRS))}\n")
    shared = key_is_shared(root)
    print(f"# サーバー保存のキー: {'あり（.env か環境変数）' if shared else 'なし（都度入力運用）'}\n")
    check_server_binding(root, shared)
    check_listeners(shared)
    check_env_and_gitignore(root)
    check_secrets_and_code(root)
    check_dependencies(root)


if __name__ == "__main__":
    main()
