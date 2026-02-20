# Configuration

Complete reference for YAML/JSON investor profiles. Profiles can be loaded via the CLI (`--profile`) or the Python API (`load_profile()`).

## Full Annotated Example

```yaml
# === Investor Demographics ===
age: 35                          # Current age (required)
retirement_age: 67               # Expected retirement age (default: 67)
investable_wealth: 200000        # Current investable portfolio in $ (required, must be > 0)
after_tax_income: 90000          # Annual after-tax income in $ (required for most income models)
risk_tolerance: 5                # 1-10 scale (provide this OR risk_aversion)
# risk_aversion: 4.0            # Gamma directly (alternative to risk_tolerance)

# === Income Projection ===
income_model:
  type: growth                   # "flat", "growth", "profile", or "csv"
  g: 0.01                        # Annual real growth rate (growth model only)
  # education: college           # "no_hs", "hs", "college" (profile model only)
  # coefficients: [-4.3, 5.4, -0.17, -0.03]  # Custom polynomial (profile model)
  # path: income_schedule.csv    # CSV with age,income columns (csv model only)

# === Retirement Benefits ===
benefit_model:
  type: none                     # "none", "flat", or "schedule"
  # annual_benefit: 30000        # Fixed annual benefit in $ (flat model)
  # replacement_rate: 0.40       # Fraction of income as benefit (flat model)

# === Mortality / Survival ===
mortality_model:
  type: none                     # "none", "parametric", or "table"
  # mode: 85                     # Modal age of death (parametric model)
  # dispersion: 10               # Dispersion parameter (parametric model)
  # path: survival.csv           # CSV with survival probabilities (table model)

# === Discount Curve ===
discount_curve:
  type: constant                 # "constant" or "term_structure"
  rate: 0.02                     # Annual real discount rate

# === Capital Market Assumptions ===
market:
  mu: 0.05                       # Expected annual stock return (decimal)
  r: 0.02                        # Risk-free rate (decimal)
  sigma: 0.18                    # Annual stock volatility (decimal)
  real: true                     # true = real terms, false = nominal
  borrowing_spread: 0.015        # Spread above r for margin borrowing

# === Allocation Constraints ===
constraints:
  allow_leverage: false           # Allow allocations above 100%
  max_leverage: 1.0               # Maximum leverage ratio (>= 1.0)
  allow_short: false              # Allow negative equity allocations
  min_allocation: 0.0             # Minimum equity floor
```

## Section Reference

### Investor (Top-Level Fields)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `age` | int | Yes | -- | Current age in years |
| `retirement_age` | int | No | 67 | Expected retirement age |
| `investable_wealth` | float | Yes | -- | Current investable portfolio ($). Must be > 0 |
| `after_tax_income` | float | No | None | Annual after-tax income ($) |
| `risk_tolerance` | int | * | -- | Risk tolerance (1-10 scale) |
| `risk_aversion` | float | * | -- | Gamma coefficient directly |

\* Provide either `risk_tolerance` or `risk_aversion`, not both.

### income_model

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | str | `"flat"` | Model type: `"flat"`, `"growth"`, `"profile"`, `"csv"` |
| `g` | float | 0.0 | Annual real growth rate. Used with `type: growth` |
| `education` | str | None | CGM education level. Used with `type: profile` |
| `coefficients` | list | None | Custom polynomial [a0, a1, a2, a3]. Overrides `education` |
| `path` | str | None | Path to CSV file. Required for `type: csv` |

### benefit_model

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | str | `"none"` | Model type: `"none"`, `"flat"`, `"schedule"` |
| `annual_benefit` | float | 0.0 | Fixed annual benefit ($). Takes priority over `replacement_rate` |
| `replacement_rate` | float | 0.0 | Fraction of pre-retirement income as benefit |

### mortality_model

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | str | `"none"` | Model type: `"none"`, `"parametric"`, `"table"` |
| `mode` | float | 0.0 | Modal age of death (parametric) |
| `dispersion` | float | 0.0 | Dispersion parameter (parametric) |
| `path` | str | None | Path to survival CSV (table) |

### discount_curve

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | str | `"constant"` | Curve type: `"constant"`, `"term_structure"` |
| `rate` | float | 0.02 | Annual discount rate (constant model) |

### market

| Field | Type | Default | Description |
|---|---|---|---|
| `mu` | float | 0.05 | Expected annual stock return (decimal) |
| `r` | float | 0.02 | Risk-free rate (decimal) |
| `sigma` | float | 0.18 | Annual stock volatility (decimal). Must be > 0 |
| `real` | bool | true | Whether returns are in real terms |
| `borrowing_spread` | float | 0.0 | Spread above `r` for borrowing. Must be >= 0 |

### constraints

| Field | Type | Default | Description |
|---|---|---|---|
| `allow_leverage` | bool | false | Allow equity allocation above 100% |
| `max_leverage` | float | 1.0 | Maximum leverage multiple. Must be >= 1.0 |
| `allow_short` | bool | false | Allow negative equity allocations |
| `min_allocation` | float | 0.0 | Minimum equity allocation floor |

## Notes

- **Required fields:** Only `age` and `investable_wealth` are strictly required at the top level, plus one of `risk_tolerance` or `risk_aversion`. All other fields have sensible defaults.
- **Consistency:** All return assumptions (`mu`, `r`, discount `rate`) should be either all real or all nominal. Set `market.real` accordingly.
- **Borrowing spread:** Only affects results when `constraints.allow_leverage` is true and the optimal allocation exceeds 100%. A typical value is 0.01-0.03 (100-300 bps).
- **File paths:** CSV paths in `income_model.path` and `mortality_model.path` are resolved relative to the working directory, not the YAML file location.
