# Primality testing and sieves (CRuby 3.4)

All numbers below were **measured** on ruby 3.4.5 / prime 0.1.4 (the same Ruby AtCoder runs
since the 2025-10 judge update). Re-measure rather than guess if you doubt one.

## `Prime.prime?` vs `Integer#prime?` — a 4-orders-of-magnitude difference

These come from the same `require "prime"` and look interchangeable. They are not.

| Call | Cost at n ≈ 10^12 | What it actually does |
|---|---|---|
| `Prime.prime?(n)` | **31 ms** | walks a `Prime::Generator23` and trial-divides up to √n. Unusable past ~10^9. |
| `n.prime?` (`Integer#prime?`) | **2 µs** | Miller–Rabin with deterministic bases (`miller_rabin_bases` / `miller_rabin_test`), falling back to a wheel-30 trial division only outside the MR range. |
| hand-rolled MR (below) | 4 µs | same idea, plus a small-prime pre-filter |

So **never say "Ruby's prime library is too slow" as a blanket claim** — say which method.
`Prime.prime?` is too slow; `Integer#prime?` is fine.

Miller–Rabin has been inside `Integer#prime?` since **prime v0.1.2 (2020-12)**, so every Ruby
you will meet on a judge has it. `miller_rabin_bases` returns `nil` (→ slow path) for very
small n, where it doesn't matter, and for n beyond its table (≥ ~3×10^24).

`require "prime"` costs ~24 ms of load time — drop the `require` if you end up not using it.

**AtCoder availability:** the official 2025-10 language list does not mention `prime`
(it lists `faster_prime`), but `require "prime"` does work on the judge — confirmed by an
accepted submission, not by the list. Treat the list as incomplete here.

## When to hand-roll Miller–Rabin anyway

`n.prime?` is enough for most problems. Hand-roll only when you are scanning **many
consecutive candidates** (e.g. "find the next prime ≥ N" for T queries): adding a
small-prime pre-filter kills ~70% of candidates in a few `%` ops before any modpow runs.

Measured on "next prime ≥ N", T = 5000, N ≤ 10^12:

| | typical input | worst case (5000 × a maximal gap of 540) |
|---|---|---|
| `m.prime?` | 0.09 s | 1.00 s |
| hand-rolled below | 0.08 s | **0.64 s** |

```ruby
# 64bit 整数全域で決定的なミラー・ラビンの基数
BASES  = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]
SMALLS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

# n が素数かどうかを決定的ミラー・ラビン法で判定します（64bit 整数の範囲で厳密）。
#
# 計算量: 基数 1 個につき O(log n) 回の剰余乗算。基数は 7 個の定数なので全体 O(log n)。
#         これは剰余乗算を O(1) と数えた場合で、n が機械語（CRuby では 63bit）に収まる
#         うちは実測もこの通り（10^12 で約 4 マイクロ秒）。多倍長に入ると剰余乗算自体が
#         ビット長 b に対して O(b^1.6..2) かかるため、ビット計算量では O(log^3 n) 相当。
#
# @param n [Integer] 判定対象の整数
# @return [Boolean] 素数であれば `true`、そうでなければ `false`
def prime?(n)
  return false if n < 2
  SMALLS.each do |p|
    return true  if n == p
    return false if (n % p).zero?
  end
  return true if n < 41 * 41   # 小素数で割り切れず 41^2 未満なら素数

  d = n - 1
  s = 0
  while d.even?
    d >>= 1
    s += 1
  end

  BASES.each do |a|
    x = (a % n).pow(d, n)      # a >= n の場合があるので剰余を取る
    next if x <= 1 || x == n - 1
    composite = true
    (s - 1).times do
      x = x * x % n
      if x == n - 1
        composite = false
        break
      end
    end
    return false if composite
  end
  true
end
```

Two things that are easy to get wrong:

- **`(a % n)` is required.** The 64-bit base set contains values up to 1795265022, which can
  exceed `n`. Without the `%`, `a.pow(d, n)` is still mathematically fine, but `x` can come
  out `0` when `n | a` — hence the `x <= 1` guard rather than `x == 1`.
- **Base sets and their proven bounds.** `[2,325,9375,28178,450775,9780504,1795265022]` is
  deterministic for all 64-bit n. `[2,3,5,7,11,13,17]` is deterministic only for
  n < 341,550,071,728,321 — and 341550071728321 itself is exactly the first composite it
  calls prime (verified against `Integer#prime?`). `[2,3,5,7]` covers n < 3,215,031,751.
  Quote a bound only if you are sure of it.

Scan odd candidates only: `m = n | 1` then `m += 2` (`n | 1` rounds an even n up, leaves odd
n alone). Handle `n <= 2` separately.

## Complexity of Miller–Rabin — state it with its counting model

Both of these are correct; say which one you mean.

- **Counting a modular multiplication as O(1)** (valid while n fits a machine word — CRuby's
  Fixnum is 63 bits, so anything up to ~9.2×10^18): one base costs O(log n) modmuls
  (`pow` is O(log d), plus ≤ s-1 ≤ log n squarings), and the base count is a constant 7.
  **→ O(log n).** This is the answer that matters for AtCoder-sized n.
- **Bit complexity**: a modmul on b = log n bits is O(b²) schoolbook, so **O(log³ n)** —
  the bound editorials usually quote. CRuby's bignum multiply is Karatsuba-or-better, so the
  real growth sits *below* b³ (measured exponent ≈ 2.0 in the 100–800 bit range).

Measured with the template above (one call, on a number that traverses all 7 bases):

| n | bits | s/call |
|---|---|---|
| 10^6 | 20 | 0.0000012 |
| 10^12 | 40 | 0.0000037 |
| 10^18 | 60 | 0.0000049 |
| 10^30 | 100 | 0.0001419 |
| 10^60 | 200 | 0.0005024 |
| 10^240 | 798 | 0.0092625 |

Note the ~29× jump between 60 and 100 bits: that is the **Fixnum → Bignum crossover**, an
interpreter artifact, not algorithmic. Below it, growth is near-linear in bit length.

For the "next prime ≥ N" pattern, the gap g averages ln N (≈28 at 10^12), giving
**O(log² N) expected modmuls per query** — but g has no useful proven bound, so quote it as
expected, not worst case (the maximal gap below 10^12 is 540).

## Sieve of Eratosthenes — cost, and when it's the wrong tool

Measured for the plain `[true] * (max+1)` sieve:

| limit | time |
|---|---|
| 10^6 | 0.105 s |
| 2×10^6 | 0.175 s |
| 10^7 | 0.918 s |

A sieve is right when you need **all** primes / smallest-prime-factor up to a bound. It is
the wrong tool for "is this one big number prime" or "next prime after N ≤ 10^12": √(10^12)
= 10^6 means trial division by π(10^6) = 78498 primes **per candidate**, which is ~9 s at
T = 5000. Miller–Rabin needs no precomputation and no memory at all.

Sizing trap to check every time: if you sieve to `MAX` and then answer queries by looking up
the next prime ≥ n, the answer for n slightly below `MAX` can be a prime **above** `MAX`
(e.g. `MAX = 2*10^6`, n = 1999994 → 2000003), and `primes.bsearch { it >= n }` quietly
returns `nil`.
