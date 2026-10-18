#!/usr/bin/env python3
"""解答と愚直解をランダム入力で突き合わせ、最初に食い違った入力を表示する。

  stress.py --gen 'ruby gen.rb' --sol 'ruby main.rb' --brute 'ruby brute.rb' [-n 300] [--timeout 10]

--gen のコマンドには、末尾に試行番号（1, 2, ...）が引数として渡る。乱数の種に使うと再現できる。
--brute を省くと、--sol が異常終了・時間切れしないかだけを調べる。
出力は空白と改行の違いを無視して比べる（答えが一意に決まる問題向け）。

最大サイズの入力で時間を測るだけなら:
  stress.py --sol 'ruby main.rb' --input max.txt
"""
import argparse
import shlex
import subprocess
import sys
import time

sys.dont_write_bytecode = True


def run(cmd, data, timeout):
    start = time.time()
    try:
        r = subprocess.run(shlex.split(cmd), input=data, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"時間切れ（{timeout} 秒）", time.time() - start
    if r.returncode != 0:
        return None, f"異常終了（exit {r.returncode}）\n{r.stderr.strip()[-800:]}", time.time() - start
    return r.stdout, None, time.time() - start


def show(label, text, limit=2000):
    text = text if len(text) <= limit else text[:limit] + f"\n...（{len(text)} 文字中 {limit} 文字まで表示）"
    print(f"--- {label}\n{text.rstrip()}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sol", required=True)
    ap.add_argument("--brute")
    ap.add_argument("--gen")
    ap.add_argument("--input", help="この入力ファイル 1 件だけを流して時間を測る")
    ap.add_argument("-n", type=int, default=300)
    ap.add_argument("--timeout", type=float, default=10)
    args = ap.parse_args()

    if args.input:
        data = open(args.input, encoding="utf-8").read()
        out, err, sec = run(args.sol, data, args.timeout)
        print(f"{'失敗: ' + err if err else '正常終了'} / {sec:.2f} 秒（手元の計測。ジャッジの速度とは違う）")
        sys.exit(1 if err else 0)
    if not args.gen:
        ap.error("--gen か --input のどちらかが必要")

    slowest = 0.0
    for i in range(1, args.n + 1):
        data, err, _ = run(f"{args.gen} {i}", "", args.timeout)
        if err:
            sys.exit(f"生成器が失敗（試行 {i}）: {err}")
        out, err, sec = run(args.sol, data, args.timeout)
        slowest = max(slowest, sec)
        if err:
            print(f"試行 {i}: 解答が{err}")
            show("入力", data)
            sys.exit(1)
        if args.brute:
            exp, err, _ = run(args.brute, data, args.timeout)
            if err:
                print(f"試行 {i}: 愚直解が{err}")
                show("入力", data)
                sys.exit(1)
            if out.split() != exp.split():
                print(f"試行 {i}: 出力が食い違った")
                show("入力", data)
                show("解答の出力", out)
                show("愚直解の出力", exp)
                sys.exit(1)
    what = "愚直解と一致" if args.brute else "正常終了"
    print(f"{args.n} 件すべて{what}（解答の最長 {slowest:.2f} 秒）")


if __name__ == "__main__":
    main()
