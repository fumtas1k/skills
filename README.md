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
