# Methodology

This page describes the mathematical framework underlying lifecycle-allocation.

For the full theoretical background, see:

- [Choi & Markov (2024), "Popular Personal Financial Advice versus the Professors"](https://www.nber.org/papers/w34166)
- The project [specification](https://github.com/engineerinvestor/lifecycle-allocation/blob/main/SPEC_DRAFT.md)

## Core Formulas

### Baseline Risky Share (Merton-style)

The optimal allocation to risky assets without human capital:

```
alpha* = (mu - r) / (gamma * sigma^2)
```

Where:

- `mu` = expected stock return
- `r` = risk-free rate
- `gamma` = risk aversion coefficient
- `sigma` = stock volatility

### Human Capital

The present value of future earnings:

```
H_t = sum_{s=t+1..T} E[CF_s] * S(t, s) / D(t, s)
```

Where:

- `E[CF_s]` = expected cash flow at age s
- `S(t, s)` = survival probability from age t to s
- `D(t, s)` = discount factor from t to s

### Recommended Allocation

Combining financial wealth and human capital:

```
alpha_t = clamp(alpha* x (1 + H_t / W_t), 0, 1)
```

With leverage enabled, the upper bound extends to `L_max`.

## Two-Tier Borrowing Rate

When leverage is allowed, the model uses a higher borrowing rate:

- **Lending regime** (alpha <= 1): uses risk-free rate `r`
- **Borrowing regime** (alpha > 1): uses `r_b = r + borrowing_spread`

*Full documentation of all parameters and edge cases is forthcoming.*
