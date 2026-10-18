# Complexity of Ruby built-ins (CRuby 3.4)

This is the anti-hallucination table. All costs are CRuby-specific (the interpreter used on
AtCoder). If you ever doubt one, measure it — grow N and check whether per-op cost stays
flat (O(1)) or grows (O(n)):

```bash
ruby -e 'require "benchmark"; [10**5,10**6,5*10**6].each{|n| a=Array.new(n,0); t=Benchmark.realtime{n.times{a.shift}}; puts "#{n}: #{(t/n*1e9).round}ns/op"}'
```

## Array

| Operation | Cost | Notes |
|---|---|---|
| `a[i]`, `a[i] = x` | O(1) | index access is direct |
| `a.first`, `a.last` | O(1) | |
| `a << x`, `a.push(x)`, `a.pop` | O(1) amortized | back-of-array, occasional realloc |
| `a.shift`, `a.unshift(x)` | **O(1) amortized** | CRuby advances/keeps a front pointer; it does NOT move all elements. This surprises people coming from C++ `std::vector` — do not claim O(n). |
| `a.shift(k)`, `a.first(k)` | O(k) | |
| `a.include?(x)`, `a.index(x)`, `a.find` | O(n) | linear scan. In a hot membership test use a `Set` or `Hash` (O(1)). |
| `a.sum`, `a.min`, `a.max`, `a.count { }` | O(n) | no caching |
| `a.min(k)`, `a.max(k)` | O(n log k) | partial |
| `a.sort`, `a.sort_by`, `a.uniq`, `a.tally`, `a.group_by` | O(n log n) / O(n) | uniq/tally/group_by are hash-based O(n) |
| `a.reverse`, `a.map`, `a.select`, `a.each` | O(n) | don't call `reverse` repeatedly in a loop |
| `a.insert(i, x)`, `a.delete_at(i)` (middle) | O(n) | elements shift |
| `a.bsearch { }` | O(log n) | requires sorted/monotone data |
| `a.pack`, `a.flatten` | O(n) | |
| `a += b` | **O(n) and allocates a new array every time** | in a loop this is quadratic. Use `a.concat(b)` or `a.push(*b)` / `b.each { a << _1 }`. This is a real trap. |

### Why shift/unshift are O(1)
CRuby's `Array` stores `ptr`, `len`, `capa` plus optional headroom at the front. `shift`
increments the start pointer; `unshift` uses front headroom (reallocating in geometric
steps when it runs out). Amortized both are O(1). Empirically, one million `shift`s on a
million-element array run in ~40ms — impossible if it were O(n) per call (that would be
10^12 element moves). So a plain `Array` is a fine queue/deque; you do not need a special
structure to pop the front cheaply.

## Hash / Set

| Operation | Cost |
|---|---|
| `h[k]`, `h[k] = v`, `h.include?(k)`, `h.delete(k)` | O(1) average |
| `h.size` | O(1) — but `h.count` goes through Enumerable, O(n). Prefer `size`. |
| `s.include?(x)`, `s.add(x)` (`Set`) | O(1) average |
| iterating `h.each` | O(n) |

`Set` is available without `require "set"` on Ruby 3.2+. Symbol / Integer / frozen-String
keys are cheapest.

## String

| Operation | Cost |
|---|---|
| `s[i]` | O(1)-ish but ~3× slower than array access; for heavy work use `s.bytes` (Integer array) |
| `s.count("a")` | O(n) but C-level, very fast for ASCII |
| `s << t`, `s.concat(t)` | O(len t) amortized |
| `s + t` in a loop | allocates each time — build with `<<` or collect and `join` |
| `s.chars`, `s.split` | O(n) |

## Integer / math

| Operation | Cost |
|---|---|
| `a + b`, `a * b` for machine-word ints | O(1) |
| Bignum arithmetic | grows with digit count |
| `base.pow(e, m)` | O(log e) modular exponentiation — always use this, never `(base**e) % m` |
| `1 << n` | O(1) for small n; far faster than `2**n` |
| `n.gcd(m)`, `n.bit_length`, `n.digits` | cheap library methods; don't reimplement |
| `n.prime?` (`Integer#prime?`) | **~2 µs at n ≈ 10^12** — it is Miller–Rabin internally, not trial division |
| `Prime.prime?(n)` | **~31 ms at n ≈ 10^12** — generator + trial division to √n. Same library, 10^4× slower. Don't confuse the two; see `primes.md`. |

## Rule of thumb for AtCoder time limits (Ruby, ~10× slower than C++)

- ~10^6 simple operations: fine (tens of ms)
- ~10^7: usually fine with lean code (~0.1–0.4s)
- ~10^8: risky/TLE territory — need lean `while`/C-level methods or a better algorithm
- ~10^9: not happening in Ruby — change the algorithm
