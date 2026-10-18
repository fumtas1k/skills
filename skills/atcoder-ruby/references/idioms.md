# House-style idioms (this repo)

Recurring ways this author writes solutions. **These are not "correct because they're the
majority" — they're the shapes that fit in when you review or write a new solution here.**
Use alongside the general rules in SKILL.md. (Code, code comments, and quoted category tags
are kept in Japanese on purpose — that's the repo's actual house style.)

## File header comment (add it on new solutions)

Almost every solution begins with this fixed header. Follow it when writing a new solution:

```ruby
# -
# ABC340/E              # 問題ID  <大文字>/<問題記号>
# 動的計画法:その他       # AtCoder Problems のカテゴリタグ（大分類:中分類）
# フェニック木           # 具体的な手法（任意で複数行、日本語）
# 座標圧縮
```

- Line 1 is a literal `# -` (occasionally a number).
- Line 2 is the problem ID. Line 3+ are Japanese category / technique notes.
- Common categories: `その他` / `動的計画法:その他` / `数学的問題` / `全探索:全列挙` /
  `二分探索` / `深さ優先探索` / `幅優先探索` / `ナップサックDP` / `累積和` / `貪欲法` /
  `Union Find` / `素因数分解`, etc. (they mirror the AtCoder Problems tags).

## Recursion as a lambda + `.()` (the author's preference)

Many solutions write DFS/recursion as a **lambda** (not `def`) and call it with `f.(...)`,
using default arguments for the initial call:

```ruby
edges = Array.new(N + 1) { [] }   # 1-indexed 隣接リスト
colors = Array.new(2) { [] }
dfs = ->(pos = 1, pre = -1, color = 0) do
  colors[color] << pos
  edges[pos].each do |to|
    next if to == pre
    dfs.(to, pos, 1 - color)
  end
end
dfs.()   # ルートから開始
```

`method(:dfs)` or a `def` recursion works too, but the house habit is the lambda. If deep
recursion raises `SystemStackError`, rewrite as an explicit-stack iterative DFS (staying a
lambda does not raise the stack limit).

## Graph construction (the standard shapes)

```ruby
G = Array.new(N + 1) { [] }        # 1-indexed が多い。0-indexed なら Array.new(N) { [] }
M.times do
  u, v = gets.split.map(&:to_i)    # 1-indexed のまま使うなら N+1 確保
  G[u] << v
  G[v] << u                        # 無向グラフ
end
```

For sparse / non-integer vertex labels use `Hash.new { |h, k| h[k] = [] }` as the adjacency
list.

## Grid bounds: use `inside?`, not `between?` (the constant factor can TLE)

For grid search (looping over the 4 neighbours in BFS/DFS), do the bounds check with a hand
`inside?` of raw comparisons, **not** `r.between?(0, H-1) && c.between?(0, W-1)`. `between?`
is a method call and measures **~1.8× slower than raw comparison** (20M iters: 0.83s vs
1.52s, CRuby 3.4). The neighbour check runs in the innermost loop of grid search, so calling
`between?` twice there can TLE (this repo has actually hit that).

```ruby
# (r, c) が H×W グリッドの内側か
def inside?(r, c, h, w)
  0 <= r && r < h && 0 <= c && c < w
end

DR = [-1, 1, 0, 0]
DC = [0, 0, -1, 1]
4.times do |d|
  nr, nc = r + DR[d], c + DC[d]
  next unless inside?(nr, nc, H, W)
  # ...
end
```

For the same reason, a single-value range check `x.between?(lo, hi)` is faster expanded to
`lo <= x && x <= hi` in a hot loop (see `references/optimization.md`).

## Coordinate compression (one-liner)

Build a "value → compressed index" Hash:

```ruby
comp = arr.uniq.sort.each_with_index.to_h        # 値 => 0-indexed の順位
# あるいは map.with_index を使う形も同義:
comp = arr.uniq.sort.map.with_index.to_h
i = comp[x]                                       # x の圧縮 index
```

Descending: `arr.uniq.sort.reverse.map.with_index.to_h`.

## Binary search: `Range#bsearch` (parametric) / `bsearch_index`

To binary-search the answer directly, use `Range#bsearch`. Get comfortable with the boundary
handling:

```ruby
# 条件 pred が false...false,true...true と単調になる境界を探す
ans = (lo..hi).bsearch { |x| pred(x) }            # pred が true になる最小の x
puts (-1 .. MAX).bsearch { |x| judge(x) }         # 見つからなければ nil
# 「pred を満たす最大の x」は、探索後に -1 する形が多い:
x = (0 .. K + 1).bsearch { round(_1) >= K } - 1
```

For a position inside a sorted array use `bsearch_index`:

```ruby
i = sorted.bsearch_index { _1 >= key }            # lower_bound 相当（nil あり）
j = sorted.bsearch_index { _1 >  key }            # upper_bound 相当
```

**When `Range#bsearch` / `bsearch_index` can't express it, paste a hand helper.** It finds a
boundary that is monotone from the "ng" side to the "ok" side, given initial `ok` and `ng`.
`Range#bsearch` only handles "smallest x where pred flips false→true"; this form also works
when **`ng > ok` (reversed direction)** and when the predicate isn't an array-membership
check (multiple conditions, a query into another structure). The house helper:

```ruby
# ng: 条件を満たさない側の端, ok: 満たす側の端（ng と ok の大小は問わない）
# yield(mid) が true なら ok 側に寄せる。境界の ok 側の値を返す
def bsearch(ng, ok)
  while (ok - ng).abs > 1
    mid = (ok + ng) / 2
    yield(mid) ? ok = mid : ng = mid
  end
  ok
end

# 使用例: A[i] が x 以上になる最小の i（ok=N を「番兵」に、ng=-1 から）
i = bsearch(-1, N) { |mid| A[mid] >= x }
```

Argument order is `bsearch(ng, ok)` (the unsatisfied side first). Swapping ok/ng gives you
"largest value satisfying the predicate" from the same function; because it uses `abs`, it
doesn't depend on which of `ng`/`ok` is larger.

## Query handling with `case ... in` pattern matching

Dispatch typed queries with `case query / in [kind, args...]`:

```ruby
Q = gets.to_i
ans = []
Q.times do
  query = gets.split.map(&:to_i)
  case query
  in [1, x]        then structure.add(x)
  in [2, x, k]     then ans << structure.kth_from(x, k)
  in [3]           then ans << structure.pop
  end
end
puts ans
```

## Counting with `tally` (and `Hash.new(0)`)

`Array#tally` is the shortest way to count occurrences:

```ruby
freq = gets.split.map(&:to_i).tally               # => {値 => 個数}
freq = A.map(&:pred).tally                         # 0-indexed 化してから数える
```

Use `Hash.new(0)` for an incremental counter, `Hash.new { |h, k| h[k] = [] }` for grouping.

## Output habits

- **Pass an Array straight to `puts`.** `puts ans` prints one element per line (no `join`).
  ```ruby
  ans = []
  Q.times { ans << compute }
  puts ans                       # 各要素を 1 行ずつ。これが最頻出
  ```
- A single space-separated line is `puts results.join(" ")`.
- Early exit on yes/no problems is `puts "No"; exit` (`exit` is used freely here).
- `p` / `pp` are for debugging — strip them before submitting (a few files still have leftover
  ones — a review checkpoint). `printf` / `format` are essentially unused.

## Interactive problems

Call `$stdout.flush` after each output. `exit` on the judge's terminating signal (e.g.
`-1 -1`):

```ruby
puts answer
$stdout.flush
res = gets.split.map(&:to_i)
exit if res == [-1, -1]
```

## Prefer a rolling DP array (faster than a full 2D table, less memory)

**When the transition depends only on the previous row/stage, reuse a 1D array instead of
allocating the full 2D table.** `dp = [0] * M` updated per stage beats
`dp = Array.new(N) { [0] * M }` on **speed (measured N=M=3000: 0.34s → 0.25s, ~1.3–1.4×)**
and on memory, **O(N·M) → O(M)** (which also dodges MLE when N·M is large). Prefer it wherever
it applies.

Three forms, ordered loosest-condition-first (which is also fastest-first):

```ruby
# (1) その場更新（dup 不要・最速）:
#     j の走査方向を選べば旧行を壊さず上書きできる場合。0/1 ナップサックが典型。
dp = [0] * (W + 1)
items.each do |w, v|
  W.downto(w) { |j| dp[j] = [dp[j], dp[j - w] + v].max }   # 降順で各品を1回だけ使う
end

# (2) 2 バッファ swap（毎段すべてのセルを書き直すなら最速級・alloc なし）:
dp = [0] * M
ep = [0] * M
N.times do |i|
  M.times { |j| ep[j] = f(dp, i, j) }   # ep の全 j を必ず埋める（下記の注意）
  dp, ep = ep, dp                        # 参照を入れ替えるだけ
end

# (3) ep = dp.dup（新行が旧行の複数セルに依存し、その場更新だと壊れる場合の安全形）:
dp = [0] * M
N.times do |i|
  ep = dp.dup
  M.times { |j| ep[j] = g(dp, i, j) }    # 参照するのは常に旧行 dp、書くのは ep
  dp = ep
end
```

**When it doesn't apply / caveats:**
- **Keep the 2D table if you need the whole thing** — path reconstruction, a transition that
  reads row `i` later, or non-adjacent row dependencies (`dp[i]` also looks at `dp[i-2]`)
  can't be rolled. First confirm "does it depend only on the previous row?"
- **The two-buffer swap is only safe when every cell is overwritten each stage.** If you write
  only some cells, values from two stages ago leak and cause bugs. If you don't fully
  overwrite, use `ep = dp.dup`.
- **`dup` is a shallow copy.** If a row holds nested arrays (`dp[j]` is itself an array),
  `dp.dup` shares the inner arrays — use `dp.map(&:dup)` (the repo has `dp = ep.map { _1.dup }`).
  A shallow `dup` is enough for rows of plain integers.

## Digit DP template

Wrap "count of numbers ≤ x satisfying the condition" as `f(x)` and take the range difference
`f(R) - f(L-1)`. Get the digit array with `x.digits.reverse` (`digits`
returns low-to-high, so reverse to go high-to-low). The dp dimensions are
"digit index × state × tight/free flag":

```ruby
def f(x)
  ds = x.digits.reverse
  n = ds.size
  # dp[i][state][less] : i 桁目まで見て state、less=1 なら既に x 未満確定
  dp = Array.new(n) { Array.new(STATES) { Array.new(2, 0) } }
  # ... 上位桁から遷移。less=0（tight）のときだけ次の桁が ds[i] に制限される ...
  dp[-1].flatten.sum
end
puts f(R) - f(L - 1)
```

## Doubling (binary lifting)

Build a "state after 2^k steps" table by doubling. Read bits with `Integer#[]` (`k[d]` is the
2^d bit of k):

```ruby
LOG = 20
nxt = Array.new(LOG) { Array.new(N) }
nxt[0] = base_transition                            # 1 ステップ後
1.upto(LOG - 1) do |d|
  N.times { |i| nxt[d][i] = nxt[d - 1][nxt[d - 1][i]] }
end
# k ステップ進める:
pos = start
LOG.times { |d| pos = nxt[d][pos] if k[d] == 1 }
```
