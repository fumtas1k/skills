# ac-library-rb reference (installed gem, v1.2.0)

The AtCoder Library ported to Ruby. Use it instead of hand-rolling these structures — it's
the house style, it's less bug-prone, and it's already installed. Signatures below were read
from the installed gem source (`gem which ac-library-rb` → the `lib/` dir); match them
exactly rather than guessing method names. If you need a method not listed here, read the
source file rather than inventing one.

## Loading

Require the piece(s) you need, then `include AcLibraryRb` so the classes are unqualified —
this is the pattern used across this repo:

```ruby
require "ac-library-rb/dsu"
require "ac-library-rb/priority_queue"
include AcLibraryRb

dsu = DSU.new(N)
pq  = PriorityQueue.new
```

Alternatives: `require "ac-library-rb"` (loads everything, classes unqualified) or
`require "ac-library-rb/dsu"` + `AcLibraryRb::DSU.new` (qualified, no `include`). For an
AtCoder submission you typically inline the needed source, but locally the `require` form is
what the repo uses.

## Class list (by category)

| Category | Class | require path |
|---|---|---|
| Data structure | `DSU` (UnionFind) | `ac-library-rb/dsu` |
| Data structure | `FenwickTree` (BIT) | `ac-library-rb/fenwick_tree` |
| Data structure | `Segtree` | `ac-library-rb/segtree` |
| Data structure | `LazySegtree` | `ac-library-rb/lazy_segtree` |
| Data structure | `PriorityQueue` | `ac-library-rb/priority_queue` |
| Data structure | `Deque` | `ac-library-rb/deque` — *rarely needed, see below* |
| Graph | `MaxFlow` | `ac-library-rb/max_flow` |
| Graph | `MinCostFlow` | `ac-library-rb/min_cost_flow` |
| Graph | `SCC` | `ac-library-rb/scc` |
| Graph | `TwoSat` | `ac-library-rb/two_sat` |
| Math | `ModInt` | `ac-library-rb/modint` |
| Math | `Convolution` | `ac-library-rb/convolution` |
| Math | `pow_mod`, `inv_mod`, `crt`, `floor_sum` | same-named paths |
| String | `suffix_array`, `lcp_array`, `z_algorithm` | same-named paths |

**Not in ac-library-rb:** there is **no ordered set / multiset (order-statistics)** here —
no `std::set` / `std::multiset` equivalent. When you need `lower_bound` / `upper_bound` /
k-th / count-less on a dynamic set, use the self-written structures in
`references/sorted-set.md` (this is the accepted house style for that gap), not a
non-existent ac-library-rb class.

## DSU (Disjoint Set Union / UnionFind)

```ruby
dsu = DSU.new(n)       # n elements 0..n-1
dsu.merge(a, b)        # union; returns the new leader
dsu.same?(a, b)        # => true / false
dsu.leader(a)          # representative of a's set  (alias: dsu[a])
dsu.size(a)            # size of a's set
dsu.groups             # => Array of arrays, each a connected component
```

## PriorityQueue

**Bare `PriorityQueue.new` is a MAX-heap** (`pop` returns the largest). Don't get this
backwards.

```ruby
pq = PriorityQueue.new            # max-heap
pq = PriorityQueue.new(array)     # heapifies the array (max-heap)
pq = PriorityQueue.max(array)     # max-heap, explicit
pq = PriorityQueue.min(array)     # min-heap (pop returns smallest)
pq = PriorityQueue.new { |a, b| a < b }   # custom: block true means "a comes out before b"
                                          # { |a,b| a < b } => min-heap

pq.push(x)      # add
pq.pop          # remove & return the top
pq.get          # peek at the top without removing
pq.empty?       # => true / false
pq.size
```

Comparator direction: the block returns true when its first arg should be dequeued before
the second. `{ |a, b| a < b }` therefore yields smallest-first (min-heap); the default (no
block) is largest-first (max-heap).

## FenwickTree (BIT)

```ruby
bit = FenwickTree.new(n)          # n zeros
bit = FenwickTree.new(array)      # build from initial values
bit.add(i, x)                     # a[i] += x   (0-indexed)
bit.sum(r)                        # prefix sum a[0...r]
bit.sum(l, r)                     # range sum a[l...r)   (half-open)
```

## Segtree

```ruby
# Segtree.new(array, e, &op)  — e = identity, op = associative merge
seg = Segtree.new(a, 0) { |x, y| x + y }              # range-sum
seg = Segtree.new(a, -INF) { |x, y| [x, y].max }      # range-max
seg.set(i, x)          # point assign
seg.get(i)             # point read
seg.prod(l, r)         # fold over [l, r)  (half-open)
seg.all_prod           # fold over whole array
seg.max_right(l) { |v| ... }   # binary search on the tree
seg.min_left(r)  { |v| ... }
```

`LazySegtree` exists for range-apply + range-fold; it takes op / identity / mapping /
composition / mapping-identity. Its constructor is involved (`set_mapping` /
`set_composition` helpers) — read `lazy_segtree.rb` before using it rather than guessing.

## ModInt — usually you don't need this either

On this repo the convention is to do modular arithmetic **by hand with plain integers**, not
`ModInt`: multiply and take `% MOD`, and use `.pow(e, MOD)` for powers and
`.pow(MOD - 2, MOD)` (Fermat) for modular inverse when `MOD` is prime. This is what the
existing solutions do, e.g.:

```ruby
MOD = 998_244_353
pmul = P.reduce(1) { |acc, p| acc * p % MOD }
ans  = pmul * wsum.pow(N, MOD) % MOD * S.pow(MOD - 2, MOD).pow(N, MOD) % MOD
puts ans
```

So don't reach for `ModInt` by default — write the `% MOD` arithmetic directly. `ModInt`
exists (`ModInt.set_mod(MOD)`, then `+ - * / **` and `.inv` on `ModInt.new(x)`), but it adds
per-object overhead and isn't the style here. Read `modint.rb` if a task genuinely calls for
it.

## Deque — usually you don't need this

`Deque` provides O(1) `push`/`pop`/`shift`/`unshift`/`rotate`. But **on CRuby a plain
`Array` already has O(1) `shift`/`unshift`/`push`/`pop`**, so a normal `Array` works fine as
a queue or deque and is the simpler choice. Only reach for `Deque` if you specifically want
its extra interface; for ordinary front/back popping, just use an `Array`.

## Extending a class (open class / monkey-patch)

When a class lacks a method you need, **reopen it and add the method** — don't reimplement
the whole structure by hand. Reopen it under its **full namespace** (`AcLibraryRb::...`),
which is where the class is actually defined; the added method can read the object's
instance variables directly. This is a normal, accepted technique on this repo.

Real example — adding binary-search-on-BIT (`kth`: the 0-indexed position where the prefix
sum first reaches `k`) to `FenwickTree`, reading its `@size` / `@data` ivars:

```ruby
require "ac-library-rb/fenwick_tree"

class AcLibraryRb::FenwickTree
  # prefix sum が k 以上になる最小の 0-indexed 位置を返す
  def kth(k)
    idx = 0
    bw = 1 << (@size.bit_length - 1)
    while bw > 0
      nxt = idx + bw
      if nxt <= @size && @data[nxt] < k
        idx = nxt
        k -= @data[idx]
      end
      bw >>= 1
    end
    idx
  end
end

bit = AcLibraryRb::FenwickTree.new([1] * N)
pos = bit.kth(r)
```

Note: to reopen the class you reference it as `AcLibraryRb::FenwickTree` even if elsewhere
you `include AcLibraryRb` to use the short name — the definition lives in the module.

## Graph / math classes

`MaxFlow`, `MinCostFlow`, `SCC`, `TwoSat`, `Convolution`, and the free functions
`pow_mod` / `inv_mod` / `crt` / `floor_sum` follow the AtCoder Library C++ API closely. When
you need one, read its source file (`gem which ac-library-rb` → `lib/<name>.rb`) for the
exact constructor and method names instead of assuming — the ports are faithful but the
method spellings are worth confirming.
