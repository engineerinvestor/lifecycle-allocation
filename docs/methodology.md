# Methodology

This page describes the mathematical framework underlying lifecycle-allocation.

For the full theoretical background, see:

- [Choi, Liu & Liu (2024), "Practical Finance: An Approximate Solution to Lifecycle Portfolio Choice"](https://www.nber.org/papers/w34166)
- The project [specification](https://github.com/engineerinvestor/lifecycle-allocation/blob/main/SPEC.md)

## Overview

The model treats the investor as having two assets:

1. **Financial wealth (W)** -- the investable portfolio
2. **Human capital (H)** -- the present value of future earnings and benefits

Since human capital produces stable, bond-like cash flows, it acts as an implicit bond holding. The model accounts for this by recommending a higher equity allocation in the investable portfolio when H/W is large (young workers) and a lower allocation when H/W is small (near retirement).

## Core Formulas

### 1. Baseline Risky Share (Merton-style)

The optimal allocation to risky assets without human capital:

```
alpha* = (mu - r) / (gamma * sigma^2)
```

Where:

- `mu` = expected annual stock return (decimal)
- `r` = risk-free rate (decimal)
- `gamma` = risk aversion coefficient (higher = more conservative)
- `sigma` = annual stock return volatility (decimal)

### 2. Human Capital PV

The present value of future cash flows:

```
H_t = sum_{s=t+1..T_max} E[CF_s] * S(t, s) / D(t, s)
```

Where:

- `E[CF_s]` = expected cash flow at age s (income or benefits)
- `S(t, s)` = survival probability from age t to s
- `D(t, s)` = discount factor from t to s

### 3. Recommended Allocation

Combining financial wealth and human capital:

```
alpha_t = clamp(alpha* x (1 + H_t / W_t), 0, upper)
```

Where `upper` is 1.0 by default, or `max_leverage` when leverage is enabled.

## Two-Tier Borrowing Rate Model

When leverage is allowed, borrowing to invest is not free. The model uses a higher rate for the borrowing regime:

- **Lending regime** (alpha <= 1): uses risk-free rate `r`
- **Borrowing regime** (alpha > 1): uses `r_b = r + borrowing_spread`

### Algorithm

1. Compute `alpha_unlev = (mu - r) / (gamma * sigma^2)`
2. If `alpha_unlev <= 1` or leverage is disabled: clamp to [0, 1], done
3. If `alpha_unlev > 1` and leverage is allowed:
    - Compute `alpha_lev = (mu - r_b) / (gamma * sigma^2)`
    - If `alpha_lev > 1`: leverage is optimal, use `min(alpha_lev, max_leverage)`
    - If `alpha_lev <= 1`: borrowing cost kills the benefit, use 1.0

### Worked Example

Suppose: mu=0.07, r=0.02, sigma=0.18, gamma=3, borrowing_spread=0.015

```
sigma^2 = 0.0324
alpha_unlev = (0.07 - 0.02) / (3 * 0.0324) = 0.05 / 0.0972 = 0.514
```

Since `alpha_unlev < 1`, no leverage is needed. The result is 0.514 (51.4% equity).

Now with gamma=1.5 (more aggressive):

```
alpha_unlev = 0.05 / (1.5 * 0.0324) = 0.05 / 0.0486 = 1.029
```

Since `alpha_unlev > 1`, switch to borrowing rate:

```
r_b = 0.02 + 0.015 = 0.035
alpha_lev = (0.07 - 0.035) / (1.5 * 0.0324) = 0.035 / 0.0486 = 0.720
```

Since `alpha_lev < 1`, borrowing cost kills the leverage benefit. Result: 1.0 (100% equity, no leverage).

## Income Models

The library provides four income projection models:

### Flat Income

```
Y_s = Y_t  (constant for all s < T_ret)
```

Use when income is expected to keep pace with inflation (in real terms).

### Constant Growth

```
Y_s = Y_t * (1 + g)^(s - t)
```

Where `g` is the annual real growth rate. A typical value is 0.01-0.03.

### Profile-Based (CGM)

Uses education-level polynomial coefficients from Cocco, Gomes & Maenhout (2005):

```
log(Y_s) = a0 + a1*(s/10) + a2*(s/10)^2 + a3*(s/10)^3
```

The profile is scaled so that the model matches the user's stated income at their current age. Available education levels: `no_hs`, `hs`, `college`.

### CSV-Based

Loads an age-income schedule from a CSV file with `age` and `income` columns. Ages not present in the CSV are linearly interpolated; ages outside the CSV range return 0.

## Benefit Models

### None

No retirement benefits. Human capital is zero after retirement.

### Flat Benefit

A constant annual benefit starting at retirement age. Can be specified as:

- `annual_benefit`: fixed dollar amount (e.g., $30,000/year)
- `replacement_rate`: fraction of pre-retirement income (e.g., 0.40 = 40%)

If `annual_benefit > 0`, it takes priority over `replacement_rate`.

## Mortality / Survival Probability

### None (Default)

Assumes the investor survives to T_max (age 100) with certainty. `S(t, s) = 1.0` for all s.

### Parametric

Gompertz-style survival curve parameterized by modal age of death and dispersion. (Planned for v0.5.)

### Table

User-supplied survival probabilities by age via CSV. (Planned for v0.5.)

## Discount Curve

### Constant

A flat annual discount rate applied to all future cash flows:

```
D(t, s) = (1 + rate)^(s - t)
```

### Term Structure

Piecewise term structure with different rates for different maturities. (Planned for v0.5.)

## Risk Tolerance to Gamma Mapping

Risk tolerance on a 1-10 scale is converted to the risk aversion coefficient gamma via a log-linear mapping:

```
gamma = 10 * 0.2^((rt - 1) / 9)
```

| Risk Tolerance | Gamma | Description |
|---|---|---|
| 1 | 10.00 | Very conservative |
| 2 | 8.01 | Conservative |
| 3 | 6.42 | Moderately conservative |
| 4 | 5.14 | Moderate-conservative |
| 5 | 4.12 | Moderate |
| 6 | 3.30 | Moderate-aggressive |
| 7 | 2.64 | Moderately aggressive |
| 8 | 2.12 | Aggressive |
| 9 | 1.70 | Very aggressive |
| 10 | 1.36 | Maximum aggressive |

Alternatively, users can provide `risk_aversion` (gamma) directly, bypassing the scale.

## Edge Cases

### W <= 0 (Zero or Negative Wealth)

The model raises a `ValueError`. The framework requires positive financial wealth because the H/W ratio is central to the allocation. Users with zero or negative net worth should address debt before applying this model.

### H = 0 (No Human Capital)

When there are no future cash flows (e.g., a fully retired investor with no benefits), the allocation reduces to `alpha*` -- the pure Merton result based on risk preferences and market assumptions alone.

### mu <= r_b (No Positive Risk Premium After Borrowing)

When the expected stock return does not exceed the borrowing rate, leverage is never beneficial. The model returns at most 1.0 (100% equity) in this case.

## Leverage Risk Disclosures

When leverage is enabled and the computed allocation exceeds 1.0, the explanation text includes these caveats:

1. **Borrowing spread reduces effective risk premium** -- the leveraged allocation uses `mu - r_b` rather than `mu - r`, so the optimal leveraged equity share is always lower than frictionless theory suggests.
2. **Margin calls and forced deleveraging** -- real-world margin lending can force liquidation at market troughs, creating procyclical risk not captured by this static model.
3. **Amplified volatility and tail risk** -- leverage scales both returns and losses. Under non-normal return distributions, the realized downside can be substantially worse than the Gaussian model implies.
4. **Tax treatment of margin interest** -- deductibility of margin interest varies by jurisdiction and investor situation; the model does not account for this.
5. **Volatility drag under discrete rebalancing** -- the model assumes continuous rebalancing. In practice, discrete rebalancing under leverage introduces volatility drag that reduces compound returns.

## Limitations and Assumptions

- **Single-asset risky class:** The model considers only a stock/bond split, not multi-asset allocation.
- **Deterministic income:** Human capital is computed from expected (mean) income paths. Income volatility and correlation with stock returns are not modeled.
- **No taxes:** All computations are pre-tax or assume a single effective tax rate embedded in the income figures.
- **No housing:** Home equity and mortgage obligations are excluded from the balance sheet.
- **Static optimization:** The model computes a single-period allocation, not a dynamic strategy with rebalancing.
- **Continuous rebalancing assumed:** The Merton formula assumes continuous trading. Discrete rebalancing introduces tracking error.
- **Normal returns:** The baseline model assumes log-normal stock returns. Fat tails and skewness are not captured.

These limitations are typical of analytical lifecycle models and are discussed in detail in [Choi et al. (2024)](https://www.nber.org/papers/w34166).
