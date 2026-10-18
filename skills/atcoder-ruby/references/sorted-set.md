# Ordered set (SortedSet / SortedMultiset) — not in ac-library-rb

**`ac-library-rb` has no ordered set (order-statistics set / multiset).** To get the Ruby
equivalent of C++ `std::set` / `std::multiset` or Python's `sortedcontainers`, the house
style is to **copy a self-written class into the solution**. Use it for problems that need
`lower_bound` / `upper_bound` / the k-th element / count-less-than on a dynamic set (two
pointers + ordered set, range counts, a running median, etc.).

There are **two proven implementations**, both included in full below. Choose by use case:

| Implementation | Method | When to use | Complexity |
|---|---|---|---|
| `SortedMultiset` / `SortedSet` | square-root decomposition (buckets) | **General. Value range unknown ahead of time / arbitrary values inserted and removed dynamically.** First choice. | add/delete/kth `O(√N)`, lower_bound etc. `O(log N)` |
| `FwtSortedMultiSet` | Fenwick Tree + coordinate compression | **The set of possible values is fixed in advance** (you can collect them by reading queries first). Smaller constant factor. | add/delete/kth/count all `O(log N)` |

> **Caveat — the house style shadows stdlib names.** These classes reuse the names of standard
> classes: Ruby's bundled `SortedSet` (from the old `set` library), and a hand-written `Prime`,
> get **redefined with the same name by a local class**. Harmless in a single-file competitive
> solution, but **don't assume a `SortedSet` name means the stdlib one.** If the class
> definition sits in the file with no matching `require`, that local definition is what's used.

---

## 1. SortedMultiset / SortedSet (square-root decomposition) — first choice, copy-paste

Elements are split into buckets (an array of arrays) of `BK` (=1500) each; the bucket is
chosen by binary search and the in-bucket insert position by binary search; a bucket is split
when it exceeds `2*BK`.

Main API (`SortedMultiset`; `SortedSet` is a dedup wrapper with the same interface):

```
ms = SortedMultiset.new(array = nil)   # 初期配列を渡すと sort して構築
ms.add(v) / ms << v                    # 追加        O(√N)
ms.delete(v)                           # 1個削除 -> true/false   O(√N)
ms.delete_all(v)                       # 全部削除 -> 消した個数
ms.include?(v) / ms.member?(v)         # 存在判定    O(log N)
ms.lower_bound(v)                      # v 以上の最小値 (nil あり)  O(log N)
ms.upper_bound(v)                      # v より大きい最小値
ms.reverse_lower_bound(v)              # v 以下の最大値
ms.prev(v)                             # v 未満の最大値
ms.kth(k) / ms[k]                      # 0-indexed で k 番目       O(√N)
ms.count_less(v) / ms.count_le(v)      # v 未満 / v 以下の個数
ms.count_range(l, h)                   # 閉区間 [l, h] の個数
ms.count(v)                            # v の個数
ms.index(v)                            # v の最初の 0-indexed 位置 (nil あり)
ms.min / ms.max                        # O(1)
ms.shift / ms.pop                      # 最小 / 最大を取り出し       O(1) 償却
ms.size / ms.empty?
ms.each / ms.reverse_each / ms.to_a
```

```ruby
# ソート済みマルチセット（重複を許可）
# 要素を複数のバケット（配列の配列）に分割して管理する平方分割構造。
class SortedMultiset
  BK = 1500
  attr_reader :size

  def initialize(a = nil)
    @a = []
    @size = 0
    if a
      b = a.sort
      i = 0
      while i < b.size
        @a << b[i, BK]
        i += BK
      end
      @size = b.size
    end
  end

  def add(v)
    if @a.empty?
      @a = [[v]]
      @size = 1
      return self
    end
    lo, hi = 0, @a.size - 1
    while lo < hi
      m = (lo + hi) >> 1
      @a[m][-1] < v ? lo = m + 1 : hi = m
    end
    b = @a[lo]
    lo2, hi2 = 0, b.size
    while lo2 < hi2
      m = (lo2 + hi2) >> 1
      b[m] < v ? lo2 = m + 1 : hi2 = m
    end
    b.insert(lo2, v)
    @size += 1
    if b.size > BK << 1
      mid = b.size >> 1
      @a.insert(lo + 1, b.slice!(mid..))
    end
    self
  end
  alias << add

  def delete(v)
    return false if @a.empty?
    lo, hi = 0, @a.size - 1
    while lo < hi
      m = (lo + hi) >> 1
      @a[m][-1] < v ? lo = m + 1 : hi = m
    end
    b = @a[lo]
    lo2, hi2 = 0, b.size
    while lo2 < hi2
      m = (lo2 + hi2) >> 1
      b[m] < v ? lo2 = m + 1 : hi2 = m
    end
    return false if lo2 >= b.size || b[lo2] != v
    b.delete_at(lo2)
    @size -= 1
    @a.delete_at(lo) if b.empty?
    true
  end

  def delete_all(v)
    c = 0
    c += 1 while delete(v)
    c
  end

  def include?(v)
    return false if @a.empty?
    lo, hi = 0, @a.size - 1
    while lo < hi
      m = (lo + hi) >> 1
      @a[m][-1] < v ? lo = m + 1 : hi = m
    end
    b = @a[lo]
    lo2, hi2 = 0, b.size
    while lo2 < hi2
      m = (lo2 + hi2) >> 1
      b[m] < v ? lo2 = m + 1 : hi2 = m
    end
    lo2 < b.size && b[lo2] == v
  end
  alias member? include?

  def lower_bound(v)
    return nil if @a.empty?
    lo, hi = 0, @a.size - 1
    while lo < hi
      m = (lo + hi) >> 1
      @a[m][-1] < v ? lo = m + 1 : hi = m
    end
    b = @a[lo]
    return nil if b[-1] < v
    lo2, hi2 = 0, b.size
    while lo2 < hi2
      m = (lo2 + hi2) >> 1
      b[m] < v ? lo2 = m + 1 : hi2 = m
    end
    b[lo2]
  end

  def upper_bound(v)
    return nil if @a.empty?
    lo, hi = 0, @a.size - 1
    while lo < hi
      m = (lo + hi) >> 1
      @a[m][-1] <= v ? lo = m + 1 : hi = m
    end
    b = @a[lo]
    return nil if b[-1] <= v
    lo2, hi2 = 0, b.size
    while lo2 < hi2
      m = (lo2 + hi2) >> 1
      b[m] <= v ? lo2 = m + 1 : hi2 = m
    end
    b[lo2]
  end

  def reverse_lower_bound(v)
    @a.empty? ? nil : ((c = count_le(v)) > 0 ? kth(c - 1) : nil)
  end

  def prev(v)
    @a.empty? ? nil : ((c = count_less(v)) > 0 ? kth(c - 1) : nil)
  end
  alias next_val upper_bound

  def kth(k)
    return nil if k < 0 || k >= @size
    @a.each do |b|
      s = b.size
      return b[k] if k < s
      k -= s
    end
    nil
  end
  alias [] kth

  def count_less(v)
    c = 0
    @a.each do |b|
      if b[-1] < v
        c += b.size
      else
        lo, hi = 0, b.size
        while lo < hi
          m = (lo + hi) >> 1
          b[m] < v ? lo = m + 1 : hi = m
        end
        return c + lo
      end
    end
    c
  end

  def count_le(v)
    c = 0
    @a.each do |b|
      if b[-1] <= v
        c += b.size
      else
        lo, hi = 0, b.size
        while lo < hi
          m = (lo + hi) >> 1
          b[m] <= v ? lo = m + 1 : hi = m
        end
        return c + lo
      end
    end
    c
  end

  def count_range(l, h)
    l > h ? 0 : count_le(h) - count_less(l)
  end

  def count(v)
    count_range(v, v)
  end

  def index(v)
    p = count_less(v)
    p < @size && kth(p) == v ? p : nil
  end

  def min = @a.empty? ? nil : @a[0][0]
  def max = @a.empty? ? nil : @a[-1][-1]

  def shift
    return nil if @a.empty?
    v = @a[0].shift
    @size -= 1
    @a.shift if @a[0].empty?
    v
  end

  def pop
    return nil if @a.empty?
    v = @a[-1].pop
    @size -= 1
    @a.pop if @a[-1].empty?
    v
  end

  def empty? = @size == 0

  def each(&bl)
    return enum_for(:each) unless bl
    @a.each { |b| b.each(&bl) }
  end

  def reverse_each(&bl)
    return enum_for(:reverse_each) unless bl
    @a.reverse_each { |b| b.reverse_each(&bl) }
  end

  def to_a = @a.flatten
end

# ソート済みセット（重複を許可しない）— SortedMultiset をラップ
class SortedSet
  attr_reader :size

  def initialize(a = nil)
    @ms = SortedMultiset.new
    @size = 0
    if a
      h = {}
      a.each do |v|
        next if h[v]
        h[v] = 1
        @ms.add(v)
      end
      @size = @ms.size
    end
  end

  def add(v)
    return false if @ms.include?(v)
    @ms.add(v)
    @size = @ms.size
    true
  end
  alias << add

  def delete(v)
    r = @ms.delete(v)
    @size = @ms.size if r
    r
  end

  def include?(v) = @ms.include?(v)
  alias member? include?

  def lower_bound(v) = @ms.lower_bound(v)
  def upper_bound(v) = @ms.upper_bound(v)
  def reverse_lower_bound(v) = @ms.reverse_lower_bound(v)
  def prev(v) = @ms.prev(v)
  def next_val(v) = @ms.upper_bound(v)
  def kth(k) = @ms.kth(k)
  alias [] kth
  def count_less(v) = @ms.count_less(v)
  def count_le(v) = @ms.count_le(v)
  def count_range(l, h) = @ms.count_range(l, h)
  def index(v) = @ms.index(v)
  def min = @ms.min
  def max = @ms.max

  def shift
    v = @ms.shift
    @size = @ms.size
    v
  end

  def pop
    v = @ms.pop
    @size = @ms.size
    v
  end

  def empty? = @ms.empty?
  def each(&bl) = @ms.each(&bl)
  def reverse_each(&bl) = @ms.reverse_each(&bl)
  def to_a = @ms.to_a
end
```

---

## 2. FwtSortedMultiSet (Fenwick Tree + coordinate compression) — when the value set is known

**Pass the possible values as a unique-sorted array `sorted` up front** (collected by reading
queries first). It can then only hold values from that set, but every operation is `O(log N)`
with a small constant factor.

Constructor and key methods:

```ruby
ss = FwtSortedMultiSet.new(query_values.sort.uniq)  # 扱う値集合を先に固定
ss.add(v)                 # O(log N)
ss.delete(v)              # 1個削除。存在しなければ false
ss.delete_all(v)          # 全削除
ss.delete_at(rank)        # rank 番目(1-origin)を削除して返す
ss.kth(rank)              # rank 番目(1-origin)に小さい要素。BIT 上二分探索 O(log N)
ss.lower_bound(v)         # v 以上の最初の要素の順位(1-origin)
ss.upper_bound(v)         # v より大きい最初の要素の順位
ss.count_range(l, r)      # 閉区間 [l, r] の個数
ss.count(v) / ss[v]       # v の個数
ss.prev / ss.next / ss.prev_strict / ss.next_strict  # 近傍要素
ss.min / ss.max / ss.size / ss.empty?
ss.each                   # 昇順列挙 (Enumerable を include)
```

Full implementation:

```ruby
# Fenwick Tree（BIT）と座標圧縮を用いた順序付きマルチセット。
# 扱える要素は initialize 時に渡した sorted（ユニーク・ソート済み）に含まれるものだけ。
class FwtSortedMultiSet
  include Enumerable
  attr_reader :size

  def initialize(sorted)
    @sorted = sorted
    @n = sorted.size
    @data = [0] * (@n + 1)
    @indexes = sorted.each_with_index.to_h
    @size = 0
    @bw = 1 << (@n.bit_length - 1)
  end

  def add(key)
    @size += 1
    _update(key, 1)
  end

  def delete(key)
    return false if count(key).zero?
    @size -= 1
    _update(key, -1)
    true
  end

  def delete_at(rank)
    return nil if rank < 1 || rank > @size
    key = kth(rank)
    delete(key)
    key
  end

  def delete_all(key)
    cnt = self[key]
    return if cnt.zero?
    @size -= cnt
    _update(key, -cnt)
  end

  # key 以上の最初の要素の順位(1-origin)。全て未満なら size + 1
  def lower_bound(key)
    idx = @sorted.bsearch_index { _1 >= key }
    idx ? _sum(idx) + 1 : @size + 1
  end

  # key より大きい最初の要素の順位(1-origin)
  def upper_bound(key)
    idx = @sorted.bsearch_index { _1 > key }
    idx ? _sum(idx) + 1 : @size + 1
  end

  # 閉区間 [left, right] の個数
  def count_range(left, right)
    l_idx = @sorted.bsearch_index { _1 >= left }
    r_idx = @sorted.bsearch_index { _1 > right }
    return 0 if l_idx.nil? || (r_idx && l_idx >= r_idx)
    _sum(r_idx || @n) - _sum(l_idx)
  end

  # rank 番目(1-origin)に小さい要素。BIT 上二分探索
  def kth(rank)
    return nil if rank < 1 || rank > @size
    i = 0
    w = @bw
    while w > 0
      ni = i + w
      if ni <= @n && @data[ni] < rank
        i = ni
        rank -= @data[i]
      end
      w >>= 1
    end
    @sorted[i]
  end

  def min = kth(1)
  def max = kth(@size)

  # maybe_key 以下の最大の要素
  def prev(maybe_key)
    rank = upper_bound(maybe_key) - 1
    rank >= 1 ? kth(rank) : nil
  end

  # maybe_key 以上の最小の要素
  def next(maybe_key)
    rank = lower_bound(maybe_key)
    rank <= @size ? kth(rank) : nil
  end

  # maybe_key 未満の最大の要素
  def prev_strict(maybe_key)
    rank = lower_bound(maybe_key) - 1
    rank >= 1 ? kth(rank) : nil
  end

  # maybe_key より大きい最小の要素
  def next_strict(maybe_key)
    rank = upper_bound(maybe_key)
    rank <= @size ? kth(rank) : nil
  end

  def count(key)
    idx = @indexes[key]
    return 0 unless idx
    _sum(idx + 1) - _sum(idx)
  end
  alias [] count

  def empty? = @size.zero?

  def each
    return to_enum(:each) unless block_given?
    return if @size.zero?
    prev_sum = 0
    @sorted.each_with_index do |val, idx|
      cur_sum = _sum(idx + 1)
      (cur_sum - prev_sum).times { yield val }
      prev_sum = cur_sum
    end
  end

  private

  def _update(key, diff)
    i = @indexes[key] + 1
    while i <= @n
      @data[i] += diff
      i += i & -i
    end
  end

  def _sum(r)
    res = 0
    while r > 0
      res += @data[r]
      r -= r & -r
    end
    res
  end
end
```

The heart of this structure is `kth`'s binary-search-on-BIT (walk to the smallest position
where the prefix sum reaches `rank`). Alternatively, reopen `AcLibraryRb::FenwickTree` and add
`kth` to it (see the "extending a class" section of `references/ac-library-rb.md`).
