---
name: atcoder-ruby
description: >-
  Verified CRuby 3.x facts and house conventions for writing competitive-programming
  solutions in Ruby (AtCoder ABC/ARC/AGC, Codeforces, yukicoder). Use this WHENEVER you
  write, review, debug, refactor, or give advice on a Ruby solution to a competitive
  problem — even if the user does not explicitly ask for it, and even when the task
  "looks trivial." It exists to stop the specific mistakes Claude makes on this repo:
  reassigning constants, mis-stating the time complexity of Array#shift / #unshift and
  other built-ins, hand-rolling data structures that ac-library-rb already provides, and
  giving performance advice that does not match how CRuby actually behaves. Trigger on
  mentions of AtCoder, ABC/ARC/AGC, competitive programming, a Ruby competitive-programming
  solution file, `gets`/`gets.split`,
  `ac-library-rb`, DSU/UnionFind, priority queue, segment tree, Fenwick/BIT, ModInt,
  ordered/sorted set or multiset (lower_bound / k-th / order statistics), coordinate
  compression, digit DP, or any "solve this in Ruby / make this Ruby solution faster / is
  this fast enough" request.
---

# AtCoder Ruby

Ruby on this repo is CRuby **3.4.x**. This user is a strong competitive Ruby programmer.
The point of this skill is not to teach competitive programming — it is to make sure the
Ruby *facts* you state and the code you write are correct and match the house style, so
you stop making the handful of mistakes documented below.

## Prime directive: don't invent Ruby facts

The failure mode this skill guards against is confident-but-wrong Ruby claims — e.g.
"`shift` is O(n), avoid it" (it is **O(1)** in CRuby) or reassigning a constant as if that
were normal. When you are about to assert a complexity, a performance claim, or an API
signature and you are not certain, **verify it instead of guessing**. A one-liner is
cheap and settles it:

```bash
ruby -e 'require "benchmark"; a=Array.new(2_000_000,0); p(Benchmark.realtime{2_000_000.times{a.shift}})'
# ~0.05s total => per-op cost is flat as N grows => O(1) amortized, not O(N)
```

Prefer measuring or reading the actual source (`gem which ac-library-rb`) over recalling a
half-remembered rule. See `references/complexity.md` for the built-in complexities people
most often get wrong.

## Constants and variables (the #1 mistake)

**Never reassign a constant.** Ruby *allows* it but only emits
`warning: already initialized constant`, and it means the design is wrong. A name that
changes is a variable, not a constant. Reassigning a constant is the single clearest
"this code was written by someone who doesn't know Ruby" tell — do not do it.

The house convention on this repo, which you should follow:

- **Input that never changes → UPPERCASE constant.** Read it once at the top and treat it
  as fixed. This is deliberate and idiomatic here, not a smell:
  ```ruby
  N, K = gets.split.map(&:to_i)
  A    = gets.split.map(&:to_i)
  AB   = Array.new(N) { gets.split.map(&:to_i) }
  ```
- **Fixed parameters → UPPERCASE constant.** Written the local way:
  ```ruby
  MOD = 10**9 + 7        # or: MOD = 998_244_353
  INF = 1 << 60          # NOT Float::INFINITY — a large integer stays Integer and is faster
  ```
- **Anything that mutates → lowercase local.** Accumulators, DP tables, answer buffers,
  loop indices, data-structure objects: `dp`, `ans`, `wsum`, `bit`, `seen`. These change,
  so they are lowercase.

Two facts that make this work and that you should not get wrong:

- A top-level constant **is visible inside method definitions** (a top-level *local*
  variable is not). So `MOD`, `N`, etc. can be used inside a `def` without passing them in.
- Reassigning the *name* warns, but **mutating the object the constant points to does
  not** (`A << x`, `dp[i] = v`). For read-only input this never comes up; just don't rebind
  the name.

## Complexity facts you must state correctly

Full table in `references/complexity.md`. The ones that cause wrong advice:

| Operation | Real CRuby cost | Wrong claim to avoid |
|---|---|---|
| `Array#shift` / `#unshift` | **O(1) amortized** (front-pointer trick) | "O(n), avoid it" — false; the house code uses `LR.shift` in a loop on purpose |
| `Array#push` / `#<<` / `#pop` | O(1) amortized | — |
| `Array#[i]` | O(1) | — |
| `Array#include?` / `#index` | O(n) linear scan | reaching for it in a hot loop instead of a `Set`/`Hash` |
| `Array#min` / `#max` / `#sum` | O(n) | assuming they cache |
| `Hash#[]` / `#include?`, `Set#include?` | O(1) average | — |
| `Array#sort` / `#sort_by` | O(n log n) | — |
| `Integer#prime?` (`n.prime?`) | **~2 µs at n ≈ 10^12** — Miller–Rabin internally | "Ruby's prime check is too slow" as a blanket claim. That is true only of `Prime.prime?` (~31 ms), a *different* method from the same library. See `references/primes.md`. |

`shift`/`unshift` being O(1) is *why* a plain `Array` works as a queue or deque here — you
do not need a special structure just to pop the front. (`ac-library-rb`'s `Deque` exists
for when you want an explicit double-ended queue, but `Array#shift` is not the bottleneck.)

## Loops: readability first

`i = 0; while i < N …` is genuinely ~2–4× faster than `each`/`times` (see
`references/optimization.md`). **But do not preemptively write `while`.** Any problem whose
intended solution needs that constant-factor win is generally not meant to be solved in
Ruby at all — so if the algorithm is right, `each` / `times` / `map` / `sum` will pass, and
they read better. Default to the idiomatic block form:

```ruby
N.times { |i| ... }
A.each_with_index { |a, i| ... }
puts AB.sum { (it.sum + K - 1) / K }
```

Keep the `while`-is-faster fact in your back pocket for the rare "this TLE's by a hair and
the algorithm is already optimal" case — but reach for a better algorithm first. Do not
"optimize" clean block code into `while` loops unprompted.

## Use ac-library-rb — don't hand-roll data structures

For DSU/UnionFind, priority queue, segment tree, lazy segment tree, Fenwick/BIT, max flow,
min-cost flow, SCC, 2-SAT, convolution, and more, use **`ac-library-rb`** (installed).
Writing your own is slower to produce, more bug-prone, and not the house style. Full class
list and verified APIs in `references/ac-library-rb.md`.

The rule is "don't re-derive what the library gives you" — **not** "never write a data
structure." When `ac-library-rb` genuinely lacks the structure, hand-rolling (or reopening a
class) *is* the house style. The clearest gap:

- **Ordered set / multiset (order-statistics) — `ac-library-rb` has none.** For
  `lower_bound` / `upper_bound` / k-th element / count-less-than on a dynamic set, this repo
  copy-pastes a self-written `SortedMultiset` / `SortedSet` (square-root decomposition) or a
  `FwtSortedMultiSet` (Fenwick + coordinate compression). Both battle-tested implementations
  and how to choose are in **`references/sorted-set.md`** — use them instead of reinventing.
  Don't assume a `SortedSet` name means stdlib; this repo shadows stdlib names with its own.

Two things this repo does **not** use, because plain Ruby already covers them — don't reach
for them by default:

- **`Deque` — skip it.** CRuby's `Array` already has O(1) `shift`/`unshift`/`push`/`pop`, so
  a plain `Array` is your queue and deque. No special structure needed to pop the front.
- **`ModInt` — skip it.** Do modular arithmetic by hand with plain integers: `acc * x % MOD`,
  `base.pow(e, MOD)` for powers, `base.pow(MOD - 2, MOD)` for the inverse when `MOD` is
  prime. That's what the existing solutions do, and it avoids per-object overhead.

Load pattern — require the piece(s) you need. Both the qualified form
(`AcLibraryRb::DSU.new`, no `include`) and the `include AcLibraryRb` + short-name form appear
in this repo; either is fine. The examples below use the short-name form:

```ruby
require "ac-library-rb/dsu"
require "ac-library-rb/priority_queue"
include AcLibraryRb

dsu = DSU.new(N)
dsu.merge(a, b)
dsu.same?(a, b)          # => true / false

pq = PriorityQueue.new   # MAX-heap by default: pop returns the largest
pq.push(x)
pq.pop
pq = PriorityQueue.min(arr)   # min-heap when you want smallest-first
```

Do not confuse the ordering: **bare `PriorityQueue.new` is a max-heap.** For a min-heap use
`PriorityQueue.min(...)` or a comparator block `PriorityQueue.new { |a, b| a < b }`. Check
`references/ac-library-rb.md` before using any method — the APIs there were read from the
installed gem source, so match them exactly rather than guessing method names.

## Ruby ≠ C++: integers and division

- **Integers are arbitrary precision.** There is no overflow. Do **not** sprinkle `% MOD`
  "to prevent overflow" — only apply modulo when the problem asks for the answer mod M.
- `/` on integers **floors** toward negative infinity. Ceiling division is `(a + b - 1) / b`
  (for positive values) or `a.ceildiv(b)` (Ruby 3.2+). Use `a.fdiv(b)` when you actually
  want a Float, and prefer `divmod` / `gcd` / `pow(e, m)` over reinventing them.
- Modular exponentiation is `base.pow(exp, MOD)` — never `(base**exp) % MOD`, which builds
  a giant Bignum first.

## House style checklist

Match the existing `*.rb` files. See `references/idioms.md` for the full set with code;
the recurring ones worth knowing up front:

- **File header comment.** New solutions start with the house header — `# -`, then the
  problem ID, then Japanese category/technique tags (the great majority of solutions do this):
  ```ruby
  # -
  # ABC340/E
  # 動的計画法:その他
  # フェニック木
  ```
- **Recursion as a lambda**, called with `.()` — `dfs = ->(pos = 1, pre = -1) { ... }` then
  `dfs.()`. This repo prefers lambdas over `def` for DFS.
- **Coordinate compression one-liner:** `comp = arr.uniq.sort.each_with_index.to_h`.
- **Parametric binary search:** `(lo..hi).bsearch { |x| pred(x) }` and `bsearch_index` on
  sorted arrays; when neither fits (reverse direction, non-array predicate), the repo's
  `bsearch(ng, ok)` helper handles it (either ordering of ng/ok).
- **Grid bounds:** an `inside?(r, c, h, w)` helper of raw comparisons, **not** `between?` —
  `between?` is a method call and has caused TLE in neighbour loops (~1.8× slower).
- **Query dispatch with pattern matching:** `case query / in [1, x] / in [2, x, k]`.
- **Counting:** `arr.tally` (and `Hash.new(0)` for incremental counters).
- **DP: prefer a rolling 1D array** when the transition only depends on the previous row —
  `dp = [0] * M` reused (in-place, two-buffer swap, or `ep = dp.dup`) beats a full
  `Array.new(N) { [0] * M }` on both speed (~1.3–1.4×) and memory (O(M) not O(N·M)). Keep the
  2D table only when you need the whole thing (path reconstruction, non-adjacent deps). See
  `references/idioms.md`.
- **Output:** `puts ans` on an Array prints one element per line (no `join` needed); early
  exit on judgement problems is `puts "No"; exit`. Strip stray `p` / `pp` before submitting.
- Input values → UPPERCASE constants; mutable state → lowercase locals.
- `MOD = 10**9 + 7` / `MOD = 998_244_353`, `INF = 1 << 60`.
- Ruby 3.4 idioms are welcome: `it` / numbered `_1` block params, `map(&:to_i)`,
  `Array.new(n) { ... }`.
- **0-indexing on input:** the house idiom for reading 1-indexed values and shifting them
  to 0-indexed in one line is `gets.split.map(&:to_i).map(&:pred)` (`pred` = "minus one").
  Use it for vertex/edge lists, queries, etc.:
  ```ruby
  U, V = gets.split.map(&:to_i).map(&:pred)     # a 1-indexed edge -> 0-indexed
  C    = gets.split.map(&:to_i).map(&:pred)     # a whole 1-indexed array -> 0-indexed
  ```
- **Prefix sums** are built with a `reduce` that seeds `[0]` and appends running totals —
  the house one-liner is:
  ```ruby
  csum = X.reduce([0]) { |acc, x| acc << acc[-1] + x }   # csum[i] = X[0...i].sum, length N+1
  ```
  So `csum[r] - csum[l]` is the sum of `X[l...r]`. (`each_with_object` or a manual loop are
  fine too, but this is the idiom you'll see in the repo.)
- Bulk output: build an array/string and `puts ans` once, rather than `puts` in a hot loop
  (and prefer `puts` over `p` for numbers — see `references/optimization.md`).
- Helper methods via `def` at top level; they can see top-level constants.
- **Extending library classes is fair game.** When a `ac-library-rb` class is missing a
  method you want (e.g. binary-search-on-BIT), reopen it and add the method rather than
  reimplementing the whole structure. Reopen it under its **full namespace**
  (`class AcLibraryRb::FenwickTree`), because that's where the class actually lives; you can
  read its ivars (`@size`, `@data`) from the added method. See `references/ac-library-rb.md`
  for a worked example.

When in doubt about what "the house style" is, read a recent existing solution nearby and
mirror it.

## Reference files

- `references/complexity.md` — Big-O of Ruby built-ins (the anti-hallucination table).
- `references/optimization.md` — constant-factor speedups (output, `Array.new`, bit ops,
  `String#bytes`, `while` vs `each`, `pow`), with the "why" and when it's worth it.
- `references/ac-library-rb.md` — every ac-library-rb class + its real API, read from the
  installed gem source.
- `references/sorted-set.md` — self-written ordered set / multiset (the gap ac-library-rb
  doesn't fill): copy-paste `SortedMultiset`/`SortedSet` (√-decomposition) and the
  Fenwick+coord-compression variant, with API tables and when to use which.
- `references/primes.md` — primality testing: `Prime.prime?` vs `Integer#prime?` (10^4× apart),
  the deterministic Miller–Rabin template and its proven base bounds, sieve costs, and when a
  sieve is the wrong tool.
- `references/idioms.md` — House-style idioms with code: file header, lambda recursion,
  coordinate compression, `Range#bsearch`, `case/in` query dispatch, `tally`, array `puts`
  output, interactive `$stdout.flush`, digit-DP and doubling templates.
