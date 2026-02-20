# Examples

Three archetype profiles that span the lifecycle: a young saver, a mid-career professional, and a near-retirement investor. These correspond to the YAML files in `examples/profiles/`.

## Why These Three?

These archetypes illustrate the model's key insight: the recommended equity allocation depends heavily on the ratio of human capital (H) to financial wealth (W). Young workers have enormous H/W ratios and get high equity allocations. As workers age, W accumulates and H declines, naturally producing a lifecycle "glide path" without arbitrary rules.

All three profiles use the same market assumptions: mu=5%, r=2%, sigma=18% (real terms).

---

## Young Saver (Age 25)

**Persona:** An early-career professional with modest savings, high income growth potential, and an aggressive risk tolerance. Almost all of their total wealth is human capital.

**Profile:** `examples/profiles/young_saver.yaml`

```yaml
age: 25
retirement_age: 67
investable_wealth: 25000
after_tax_income: 70000
risk_tolerance: 7

income_model:
  type: growth
  g: 0.02
```

**Results:**

| Metric | Value |
|---|---|
| Human capital (H) | ~$2,870,000 |
| H/W ratio | ~115x |
| alpha* (baseline) | 70.0% |
| Unconstrained allocation | ~8,100% |
| Recommended allocation | **100%** (capped) |

**Interpretation:** This investor's human capital dwarfs their financial wealth by over 100x. The model would recommend extreme leverage if allowed, but capped at 100%, it says: "put everything in stocks." This makes intuitive sense -- a 25-year-old with 42 years of growing income ahead has enormous implicit bond exposure through their career. Their investable portfolio should compensate by being fully equity.

---

## Mid-Career Professional (Age 45)

**Persona:** A peak-income professional with substantial savings accumulated over 20 years. Still has significant human capital, but the gap between H and W has narrowed.

**Profile:** `examples/profiles/mid_career.yaml`

```yaml
age: 45
retirement_age: 67
investable_wealth: 500000
after_tax_income: 120000
risk_tolerance: 5

income_model:
  type: flat
```

**Results:**

| Metric | Value |
|---|---|
| Human capital (H) | ~$2,041,000 |
| H/W ratio | ~4.1x |
| alpha* (baseline) | 46.3% |
| Unconstrained allocation | ~235% |
| Recommended allocation | **~96%** (capped) |

**Interpretation:** At 45, this investor still has 22 years of $120k income ahead -- worth about $2M in present value. With an H/W ratio of 4x and moderate risk tolerance, the model recommends nearly full equity. The allocation is below 100% because gamma=4.47 (risk_tolerance=5) produces a more conservative alpha* than the young saver's gamma=2.64 (risk_tolerance=7).

---

## Near-Retirement Investor (Age 60)

**Persona:** A senior professional with substantial savings but only 7 years of remaining income. Conservative risk tolerance reflects a shorter time horizon and greater focus on wealth preservation.

**Profile:** `examples/profiles/near_retirement.yaml`

```yaml
age: 60
retirement_age: 67
investable_wealth: 1000000
after_tax_income: 150000
risk_tolerance: 3

income_model:
  type: flat
```

**Results:**

| Metric | Value |
|---|---|
| Human capital (H) | ~$840,000 |
| H/W ratio | ~0.8x |
| alpha* (baseline) | 14.4% |
| Unconstrained allocation | ~26% |
| Recommended allocation | **~24%** |

**Interpretation:** With only 7 years of income remaining, human capital is less than financial wealth for the first time. Combined with conservative risk preferences (gamma=6.42), the model recommends only ~24% equity. This is lower than a typical 60/40 allocation or a target-date fund, reflecting the investor's stated conservatism. Adding retirement benefits (e.g., Social Security) would increase human capital and push the allocation higher.

---

## Comparison

| Archetype | Age | H/W | alpha* | Recommended | 60/40 | 100-age |
|---|---|---|---|---|---|---|
| Young saver | 25 | ~115x | 70.0% | 100% | 60% | 75% |
| Mid-career | 45 | ~4.1x | 46.3% | ~96% | 60% | 55% |
| Near-retirement | 60 | ~0.8x | 14.4% | ~24% | 60% | 40% |

The lifecycle model produces higher allocations than heuristics for younger investors (where human capital justifies more equity) and lower allocations for conservative near-retirees (where low H/W and high risk aversion both push toward bonds).
