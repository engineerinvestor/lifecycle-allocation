# API Reference

Complete reference for the public Python API. All items listed here are available from the top-level `lifecycle_allocation` package.

```python
from lifecycle_allocation import (
    # Data models
    AllocationResult,
    BenefitModelSpec,
    ConstraintsSpec,
    DiscountCurveSpec,
    IncomeModelSpec,
    InvestorProfile,
    MarketAssumptions,
    MortalitySpec,
    # Functions
    alpha_star,
    compare_strategies,
    human_capital_pv,
    recommended_stock_share,
    risk_tolerance_to_gamma,
)
```

---

## Data Models

### `InvestorProfile`

Complete investor profile combining demographics, income, and preferences.

```python
InvestorProfile(
    age: int,
    retirement_age: int,
    investable_wealth: float,
    after_tax_income: float | None = None,
    risk_tolerance: int | None = None,
    risk_aversion: float | None = None,
    income_model: IncomeModelSpec = IncomeModelSpec(),
    benefit_model: BenefitModelSpec = BenefitModelSpec(),
    mortality_model: MortalitySpec = MortalitySpec(),
)
```

| Parameter | Type | Description |
|---|---|---|
| `age` | `int` | Current age in years |
| `retirement_age` | `int` | Expected retirement age |
| `investable_wealth` | `float` | Current investable financial wealth ($). Must be > 0 |
| `after_tax_income` | `float \| None` | Current annual after-tax income ($) |
| `risk_tolerance` | `int \| None` | Risk tolerance on 1-10 scale. Provide this or `risk_aversion` |
| `risk_aversion` | `float \| None` | Gamma coefficient directly. Provide this or `risk_tolerance` |
| `income_model` | `IncomeModelSpec` | Income projection model |
| `benefit_model` | `BenefitModelSpec` | Retirement benefit model |
| `mortality_model` | `MortalitySpec` | Survival probability model |

**Property:** `profile.gamma` resolves the risk aversion coefficient from either field.

```python
profile = InvestorProfile(
    age=30, retirement_age=67,
    investable_wealth=100_000,
    after_tax_income=70_000,
    risk_tolerance=5,
)
print(profile.gamma)  # ~4.47
```

### `MarketAssumptions`

Capital market assumptions for the stock/bond universe.

```python
MarketAssumptions(
    mu: float = 0.05,
    r: float = 0.02,
    sigma: float = 0.18,
    real: bool = True,
    borrowing_spread: float = 0.0,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `mu` | `float` | 0.05 | Expected annual stock return (decimal) |
| `r` | `float` | 0.02 | Risk-free rate (decimal) |
| `sigma` | `float` | 0.18 | Annual stock volatility (decimal). Must be > 0 |
| `real` | `bool` | True | Whether returns are in real (inflation-adjusted) terms |
| `borrowing_spread` | `float` | 0.0 | Spread above `r` for margin borrowing. Must be >= 0 |

### `IncomeModelSpec`

Specification for income projection model.

```python
IncomeModelSpec(
    type: str = "flat",
    g: float = 0.0,
    education: str | None = None,
    coefficients: list[float] | None = None,
    path: str | None = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `type` | `str` | `"flat"` | One of `"flat"`, `"growth"`, `"profile"`, `"csv"` |
| `g` | `float` | 0.0 | Annual real growth rate (for `type="growth"`) |
| `education` | `str \| None` | None | Education level for CGM profile: `"no_hs"`, `"hs"`, `"college"` |
| `coefficients` | `list[float] \| None` | None | Custom polynomial coefficients [a0, a1, a2, a3] |
| `path` | `str \| None` | None | Path to CSV with `age` and `income` columns |

### `BenefitModelSpec`

Specification for retirement benefit model.

```python
BenefitModelSpec(
    type: str = "none",
    annual_benefit: float = 0.0,
    replacement_rate: float = 0.0,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `type` | `str` | `"none"` | One of `"none"`, `"flat"`, `"schedule"` |
| `annual_benefit` | `float` | 0.0 | Fixed annual benefit ($). Takes priority over `replacement_rate` |
| `replacement_rate` | `float` | 0.0 | Fraction of income received as benefit |

### `MortalitySpec`

Specification for mortality/survival model.

```python
MortalitySpec(
    type: str = "none",
    mode: float = 0.0,
    dispersion: float = 0.0,
    path: str | None = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `type` | `str` | `"none"` | One of `"none"`, `"parametric"`, `"table"` |
| `mode` | `float` | 0.0 | Modal age of death (parametric model) |
| `dispersion` | `float` | 0.0 | Dispersion parameter (parametric model) |
| `path` | `str \| None` | None | Path to survival probability CSV |

### `DiscountCurveSpec`

Specification for discount curve.

```python
DiscountCurveSpec(
    type: str = "constant",
    rate: float = 0.02,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `type` | `str` | `"constant"` | One of `"constant"`, `"term_structure"` |
| `rate` | `float` | 0.02 | Annual discount rate (for `type="constant"`) |

### `ConstraintsSpec`

Allocation constraints.

```python
ConstraintsSpec(
    allow_leverage: bool = False,
    max_leverage: float = 1.0,
    allow_short: bool = False,
    min_allocation: float = 0.0,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `allow_leverage` | `bool` | False | Allow allocations above 100% |
| `max_leverage` | `float` | 1.0 | Maximum leverage ratio. Must be >= 1.0 |
| `allow_short` | `bool` | False | Allow negative equity allocations |
| `min_allocation` | `float` | 0.0 | Minimum equity allocation floor |

### `AllocationResult`

Result of an allocation computation.

| Field | Type | Description |
|---|---|---|
| `alpha_star` | `float` | Baseline risky share (before human capital) |
| `alpha_unconstrained` | `float` | Raw allocation: `alpha* x (1 + H/W)` |
| `alpha_recommended` | `float` | Final clamped allocation |
| `human_capital` | `float` | Present value of future earnings/benefits ($) |
| `leverage_applied` | `bool` | Whether the result uses leverage |
| `borrowing_cost_drag` | `float` | Alpha reduction due to borrowing spread |
| `explain` | `str` | Human-readable explanation |
| `components` | `dict` | All intermediate values |

---

## Functions

### `recommended_stock_share`

Main entry point for computing a lifecycle allocation.

```python
recommended_stock_share(
    profile: InvestorProfile,
    market: MarketAssumptions,
    curve: DiscountCurveSpec | None = None,
    constraints: ConstraintsSpec | None = None,
    *,
    t_max: int = 100,
    variant: str = "merton",
) -> AllocationResult
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `profile` | `InvestorProfile` | required | Investor profile |
| `market` | `MarketAssumptions` | required | Market assumptions |
| `curve` | `DiscountCurveSpec \| None` | None | Discount curve (defaults to constant 2%) |
| `constraints` | `ConstraintsSpec \| None` | None | Constraints (defaults to no leverage) |
| `t_max` | `int` | 100 | Maximum age for human capital computation |
| `variant` | `str` | `"merton"` | `"merton"` or `"log_return"` |

```python
result = recommended_stock_share(profile, market)
print(f"{result.alpha_recommended:.1%}")  # e.g., "100.0%"
```

### `alpha_star`

Compute the baseline risky share using the two-tier borrowing rate model.

```python
alpha_star(
    market: MarketAssumptions,
    gamma: float,
    constraints: ConstraintsSpec | None = None,
    *,
    variant: str = "merton",
) -> tuple[float, bool, float]
```

Returns a 3-tuple: `(alpha, leverage_applied, borrowing_cost_drag)`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `market` | `MarketAssumptions` | required | Market assumptions |
| `gamma` | `float` | required | Risk aversion coefficient |
| `constraints` | `ConstraintsSpec \| None` | None | Constraints (defaults to no leverage) |
| `variant` | `str` | `"merton"` | `"merton"` or `"log_return"` |

```python
a, leveraged, drag = alpha_star(market, gamma=4.0)
print(f"alpha*: {a:.1%}")  # e.g., "46.3%"
```

### `human_capital_pv`

Compute the present value of human capital.

```python
human_capital_pv(
    profile: InvestorProfile,
    curve: DiscountCurveSpec | None = None,
    *,
    t_max: int = 100,
) -> float
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `profile` | `InvestorProfile` | required | Investor profile |
| `curve` | `DiscountCurveSpec \| None` | None | Discount curve (defaults to constant 2%) |
| `t_max` | `int` | 100 | Maximum age for the summation |

```python
h = human_capital_pv(profile)
print(f"Human capital: ${h:,.0f}")
```

### `compare_strategies`

Compare the lifecycle allocation against heuristic strategies.

```python
compare_strategies(
    profile: InvestorProfile,
    market: MarketAssumptions,
    curve: DiscountCurveSpec | None = None,
    constraints: ConstraintsSpec | None = None,
    *,
    strategies: dict[str, float] | None = None,
) -> pd.DataFrame
```

Returns a DataFrame with columns: `strategy`, `allocation`, `description`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `profile` | `InvestorProfile` | required | Investor profile |
| `market` | `MarketAssumptions` | required | Market assumptions |
| `curve` | `DiscountCurveSpec \| None` | None | Discount curve |
| `constraints` | `ConstraintsSpec \| None` | None | Constraints |
| `strategies` | `dict[str, float] \| None` | None | Additional user-supplied strategies to include |

```python
df = compare_strategies(profile, market)
print(df.to_string(index=False))
```

### `risk_tolerance_to_gamma`

Convert risk tolerance (1-10 scale) to gamma.

```python
risk_tolerance_to_gamma(rt: int) -> float
```

| Parameter | Type | Description |
|---|---|---|
| `rt` | `int` | Risk tolerance, 1-10 |

```python
gamma = risk_tolerance_to_gamma(5)
print(f"gamma: {gamma:.2f}")  # ~4.47
```
