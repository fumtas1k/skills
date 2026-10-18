# skills

自作の Agent Skills です。

| スキル | 内容 |
|---|---|
| [atcoder-ruby](skills/atcoder-ruby/SKILL.md) | Ruby（CRuby 3.4）で競技プログラミングの解答を書く・直すときの事実確認とコーディング規約 |
| [atcoder-review](skills/atcoder-review/SKILL.md) | AtCoder のコンテスト後の振り返り（手元の解答・公式解説・提出履歴の突き合わせ） |

## 導入

```bash
# プロジェクトに入れる（.agents/skills/ に実体をコピーし、skills-lock.json に記録）
npx skills add fumtas1k/skills --skill atcoder-ruby

# 更新
npx skills update
```

`atcoder-review` の AtCoder ID は `scripts/atcoder_fetch.py set-user <ID>` で `config.json` に保存されます（git 管理外）。

## 前提と注意

どちらも作者個人の環境と流儀に合わせて書いています。使う場合は、自分の流儀に合わせて書き換えてください。

- **house style**: 解答の先頭のヘッダー（`# -` / 問題 ID / アルゴリズムのタグ）、DFS はラムダで書く、ModInt と Deque は使わない、順序付き集合は自作の `SortedMultiset` を貼る、など。`atcoder-ruby` はこれを「従うべき規約」として扱います。
- **振り返りの方針**: Ruby で TLE しても定数倍の調整は提案しない、など。`atcoder-review` はこれに従います。
- **想定する環境**: Ruby（CRuby 3.4）、[atcoder-cli](https://github.com/Tatamo/atcoder-cli)（acc）のフォルダ構成、[online-judge-tools](https://github.com/online-judge-tools/oj)（oj）のログインセッション。oj の cookie は macOS と Linux の既定の場所だけを探します。
- **evals**: `evals/evals.json` は作者の手元の解答（`abc477`・`abc478`）を前提にした回帰テストで、他の環境ではそのまま使えません。
