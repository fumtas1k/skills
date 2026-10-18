# Constant-factor speedups (CRuby, competitive Ruby)

Source: the universato "競プロにおけるRuby高速化" catalogue, cross-checked on CRuby 3.4.

**Read this first:** algorithm beats constant factor every time. Apply these only when the
algorithm is already right and the code is TLE-ing by a small margin, or when it costs
nothing (e.g. `.pow(e, m)` is both faster *and* cleaner). Do not uglify clean code chasing
a 1.2× win — the house style values readability, and any problem that *requires* these
tricks to pass is usually not intended for Ruby. The single biggest wins are output
batching and using the right algorithm/data structure, not micro-rewrites.

## Highest-value, always worth it

- **Modular power:** `base.pow(e, MOD)` — orders of magnitude faster than `(base**e) % MOD`
  (the latter materialises a huge Bignum first). Also cleaner. Always use `.pow`.
- **Batch output:** collect answers and print once. `puts array` prints each element on its
  own line. `p` is 3–4× slower than `puts` for numbers (it calls `inspect`) — use `puts`.
  A per-iteration `puts` in a big loop can dominate runtime; build a buffer instead.
  ```ruby
  ans = []
  N.times { |i| ans << compute(i) }
  puts ans            # one syscall-batched write, fast
  ```
- **`Float::INFINITY` → `INF = 1 << 60`:** keep values Integer; integer compares/arith are
  faster and avoid float surprises. Large enough for any AtCoder constraint.
- **Sum with a modulus:** add freely, take `% MOD` once at the end when possible; only
  reduce every step for *products* (to keep factors small). `arr.sum` beats
  `arr.inject(:+)`.

## Worth it in hot inner loops

- **`while` > `times`/`each` > `map` > `loop`.** A manual `i = 0; while i < N; …; i += 1;
  end` is ~2–4× faster than block iteration because it skips block-call overhead. Reserve
  for a proven hot loop; otherwise keep the readable block form (see SKILL.md — do not
  preemptively convert).
- **`Array.new(n, 0)` > `[0] * n` > `Array.new(n) { 0 }`.** The block form is ~10× slower
  because it calls the block n times. Use the block form only when you need distinct objects
  per slot (e.g. `Array.new(n) { [] }` — you *must* use a block here, or all rows alias the
  same array).
- **Bit ops:** `1 << n` beats `2**n`; `x & 1 == 1` slightly beats `x.odd?`; `x >> 1` for
  halving.
- **Membership:** replace `array.include?(x)` in a loop with a prebuilt `Set`/`Hash`
  (O(1) vs O(n)).
- **Index access:** `a[0]` is a touch faster than `a.first`; `a.size` faster than
  `a.count` (which is Enumerable). Hoist values that don't change out of the loop instead of
  re-indexing each iteration.
- **Range check:** `lo <= x && x <= hi` beats `x.between?(lo, hi)` — `between?` is a method
  call. Measured ~1.8× (20M iters: 0.83s vs 1.52s, CRuby 3.4). In grid search this matters:
  use an `inside?(r, c, h, w)` helper of raw comparisons for the 4-neighbour bounds check,
  not two `between?` calls (that combination has actually caused TLE on this repo). See
  `references/idioms.md`.

## String-heavy problems

- **`String#bytes`:** convert to an Integer array once and work on bytes — array access is
  ~3× faster than string indexing, and byte math (`b - 'a'.ord`) is cheap. Convert back only
  if needed.
- **`String#count("a-z")`:** C-level ASCII counting, 10–100× faster than
  `chars.count { }`.
- Build strings with `<<` / collect-and-`join`, never `s += t` in a loop.

## Hash / Set tuning

- Prefer `Symbol`, `Integer`, or frozen-`String` keys.
- Encode an integer pair `(x, y)` as one integer `x * K + y` instead of `[x, y]` when using
  it as a hash key — avoids array allocation and hashing cost.
- `Hash#size`, not `Hash#count`.

## Reading input fast

- `gets.split.map(&:to_i)` is the standard line reader.
- For very large input, read in bulk: `data = $stdin.read.split; ...` and consume with an
  index, or `$stdin.read.split("\n")`. Avoids per-line `gets` overhead.
- `gets.split.map(&:to_i).map(&:pred)` is the house one-liner for reading a 1-indexed line
  and converting it to 0-indexed in one pass (`pred` is `n - 1`). Used for edges, queries,
  and any 1-indexed array.

## Divide with care

- Integer `/` floors. Ceiling: `(a + b - 1) / b` (positive) or `a.ceildiv(b)` (Ruby 3.2+).
- `a.fdiv(b)` for a Float result; `a.divmod(b)` for quotient+remainder in one call.
