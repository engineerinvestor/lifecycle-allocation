```markdown
# SPEC.md — `lifecycle-allocation` (Choi-Style Lifecycle Allocation + Visual Analytics)

> **Goal:** An open-source Python library that implements a *practical lifecycle portfolio choice* framework inspired by James Choi et al. (human capital as bondlike wealth + risk-aversion–aware risky share), and ships **high-signal, compelling visualizations** and **reproducible notebooks**.
>
> **Disclaimer:** This library is for education and research. It is not investment advice.

---

## 1. Product vision

Most “rules” for stock/bond allocation are single-variable heuristics:
- 60/40
- “100 minus age”
- target-date funds

This project provides a **balance-sheet** view of an investor:
- **Financial wealth (W)**: investable portfolio today
- **Human capital (H)**: present value (PV) of future after-tax earnings + retirement benefits
- **Risk preference (γ)**: risk aversion (or equivalent “risk tolerance” score)

Then it produces:
- A **recommended stock share** of the investable portfolio under constraints (no leverage by default)
- A **glide-path** through time as W and H evolve
- **Sensitivity analysis**: how recommendations move with income assumptions, risk aversion, return assumptions, mortality, retirement age, etc.
- **Comparisons** to common heuristics + target-date glide paths
- **Visual analytics** that explain *why* the recommendation is what it is

---

## 2. Scope

### 2.1 In-scope (MVP → v1.0)
1. **Core allocation engine**
   - Baseline risky share (Merton-like):
     - `alpha_star = f(mu, r, sigma, gamma)`
   - Human capital PV `H` computed from an income + benefits model, discounted with a user-selected discount curve
   - Recommended stock fraction in investable portfolio:
     - `alpha_t = clamp(alpha_star * (1 + H/W), 0, 1)` (default constraints: no leverage, no shorting)

2. **Reference strategies for comparison**
   - 60/40
   - 100-minus-age (configurable to 110/120-minus-age)
   - A simple target-date glide path model (parametric approximation)
   - Optional: load real TDF allocations from user-supplied CSV

3. **Visual analytics package**
   - “Personal balance sheet” decomposition (H vs W)
   - Allocation bar comparisons (Choi vs heuristics)
   - Glide-path chart (alpha_t over age)
   - Sensitivity “tornado” chart
   - Heatmaps of alpha_t over (W, income) or (gamma, mu)
   - Fan chart of projected W over time (optional Monte Carlo module)
   - Utility comparison (optional, but recommended)

4. **Reproducible notebooks**
   - Recreate the 3 “WSJ-style” archetypes
   - Show how changing savings and risk tolerance shifts alpha_t

5. **CLI**
   - Compute allocation from a YAML/JSON profile
   - Export charts to PNG/SVG + a short “explain” report (Markdown)

### 2.2 Non-goals (v1.0)
- Full tax optimization, account-level asset location
- Multi-asset optimization beyond a stock/risk-free split (can be extended later)
- Full housing + mortgage modeling in the default engine (planned extension)
- A hosted web app (can be a separate project)

---

## 3. User stories

### 3.1 Everyday quant-curious user
- “Given my age, income, savings, and risk tolerance, what stock % does the model suggest?”
- “Show me *why*.”
- “Show me how sensitive it is to assumptions.”

### 3.2 Researcher / educator
- “I want to change the income process, correlation assumptions, discounting, or mortality, and see how results change.”

### 3.3 Developer
- “I want a clean Python API, typed dataclasses, stable outputs, and charts I can embed in a blog.”

---

## 4. Mathematical framework (v1.0)

### 4.1 Inputs
- Age `t` (years)
- Retirement age `T_ret`
- Current investable financial wealth `W_t`
- Current after-tax income `Y_t` (optional; required for some income models)
- Income growth model parameters (or default profile)
- Retirement benefit model (e.g., Social Security proxy)
- Risk tolerance score `rt` (e.g., 1–10) **or** risk aversion `gamma`
- Capital market assumptions:
  - Expected stock return `mu` (real or nominal, consistent)
  - Risk-free rate `r`
  - Stock volatility `sigma`
  - Borrowing spread above risk-free rate `borrowing_spread` (default 0; used when leverage is enabled)
- Discounting assumptions for human capital PV:
  - Constant real discount rate
  - Term structure (piecewise curve)
  - Optional: risk-adjusted discounting for income (extension)

### 4.2 Risky share (baseline)
Default implementation is a Merton-style approximation with a **two-tier borrowing rate model**:

**Lending regime** (alpha ≤ 1 — investing own capital only):
- `alpha_unlev = (mu - r) / (gamma * sigma^2)`

**Borrowing regime** (alpha > 1 — leveraging beyond 100% equities):
- `r_b = r + borrowing_spread` (borrowing rate = risk-free rate + spread)
- `alpha_lev = (mu - r_b) / (gamma * sigma^2)`

Borrowing isn't free. The optimal allocation depends on whether the investor is lending or borrowing:

1. Compute `alpha_unlev = (mu - r) / (gamma * sigma^2)`
2. If `alpha_unlev <= 1` → no leverage needed, use `alpha_unlev`
3. If `alpha_unlev > 1` and leverage is allowed (`allow_leverage = True`):
   - Compute `alpha_lev = (mu - r_b) / (gamma * sigma^2)`
   - If `alpha_lev > 1` → leverage is optimal: use `min(alpha_lev, L_max)`
   - If `alpha_lev <= 1` → borrowing cost kills the benefit: use `1.0`
4. If `alpha_unlev > 1` and leverage is **not** allowed → clamp to `1.0`

Optional variant:
  - log-return correction / alternative definitions behind a flag

### 4.3 Human capital PV `H_t`
Human capital is PV of expected future net cashflows:
- For ages `s = t+1 ... T_ret`: labor earnings
- For ages `s = T_ret+1 ... T_max`: retirement benefits (optional)
- Multiply by survival probability `S(t→s)` if mortality modeled

General form:
- `H_t = sum_{s=t+1..T_max} E[CF_s] * S(t→s) / D(t→s)`
Where:
- `CF_s` = after-tax income (pre-retirement) or benefits (post-retirement)
- `D(t→s)` = discount factor from a chosen curve

**MVP** provides multiple income models:
1. **Flat income**: `Y_s = Y_t` until retirement
2. **Deterministic growth**: `Y_s = Y_t * (1+g)^(s-t)`
3. **Profile-based**: age-income curve (piecewise)
4. **User-supplied**: CSV of age→expected after-tax income

Benefits models:
- **None**
- **Flat real benefit** from retirement age onward
- **User-supplied** benefit schedule

Mortality models:
- **None** (assume survival to `T_max`)
- **Simple survival curve** (parametric)
- **User-supplied survival probabilities** by age

### 4.4 Recommended investable stock share `alpha_t`
Core practical rule, incorporating the two-tier risky share from §4.2:

1. Compute `alpha_star_adj` using the two-tier algorithm (§4.2)
2. Apply human capital adjustment: `alpha_raw = alpha_star_adj * (1 + H_t / W_t)`
3. Clamp to allowed range:
   - Leverage enabled: `alpha_t = clamp(alpha_raw, 0, L_max)`
   - Leverage disabled (default): `alpha_t = clamp(alpha_raw, 0, 1)`

Edge cases:
- If `W_t <= 0`: define behavior
  - default: raise error with guidance
  - optional: treat as `alpha_t = 1` if user allows (but document)
- If `H_t` is 0: reduces to `alpha_star_adj`
- If leverage enabled but `mu <= r_b`: leverage is never beneficial, fall back to `alpha_t <= 1.0`

### 4.5 Optional module: Utility comparison
Provide a lightweight metric to compare heuristics:
- simulate lifecycle consumption/wealth under strategies
- compute CRRA lifetime utility with discounting
- report “utility loss vs benchmark” (for education)

This module is optional (heavy assumptions) but valuable for demos.

### 4.6 Leverage risk disclosures
When leverage is enabled, the `explain` output and report must include the following caveats:

1. **Borrowing spread reduces effective risk premium** — The leveraged allocation uses `mu - r_b` rather than `mu - r`, so the optimal leveraged equity share is always lower than the frictionless (zero-spread) theory would suggest.
2. **Margin calls and forced deleveraging** — Real-world margin lending can force liquidation at the worst times (market troughs), creating procyclical risk not captured by the static model.
3. **Amplified volatility and tail risk** — Leverage scales both returns and losses. Under non-normal return distributions (fat tails, skewness), the realized downside can be substantially worse than the Gaussian model implies.
4. **Tax treatment of margin interest** — Deductibility of margin interest varies by jurisdiction and investor situation; the model does not account for this.
5. **Volatility drag under discrete rebalancing** — The model assumes continuous rebalancing. In practice, discrete rebalancing under leverage introduces volatility drag that reduces compound returns.

These disclosures should appear in `explain.py` output whenever `allow_leverage=True` and the computed allocation exceeds 1.0.

---

## 5. Package structure

```

practicalfinance/
**init**.py
core/
models.py            # dataclasses: InvestorProfile, MarketAssumptions, etc.
allocation.py        # alpha_star, alpha_t, constraints
human_capital.py     # income + benefits + discounting + mortality PV
income_models.py     # pluggable income processes
mortality.py         # survival models + interfaces
discounting.py       # discount curve abstractions
strategies.py        # rule-of-thumb strategies for comparison
explain.py           # explanation text builder ("why this allocation")
viz/
charts.py            # chart functions
themes.py            # consistent style defaults
report.py            # export multi-figure report to folder / md
sim/
monte_carlo.py       # optional wealth path simulation
utility.py           # optional lifetime utility evaluation
io/
loaders.py           # CSV/YAML/JSON load/save
schema.py            # pydantic schemas (optional)
cli/
main.py              # entry point
examples/
notebooks/           # Jupyter notebooks (kept lightweight)
profiles/            # example YAML profiles
tests/
test_allocation.py
test_human_capital.py
test_income_models.py
test_viz_smoke.py
docs/
index.md
methodology.md
pyproject.toml
README.md
LICENSE

````

---

## 6. Public API (Python)

### 6.1 Data models
- `InvestorProfile(...)`
  - `age: int`
  - `retirement_age: int`
  - `investable_wealth: float`
  - `after_tax_income: float | None`
  - `risk_tolerance: int | None` (1–10)
  - `risk_aversion: float | None` (gamma)
  - `income_model: IncomeModelSpec`
  - `benefit_model: BenefitModelSpec`
  - `mortality_model: MortalitySpec`
- `MarketAssumptions(mu, r, sigma, real=True, borrowing_spread=0.0)`
  - `borrowing_spread`: decimal spread above risk-free rate for margin borrowing (e.g., 0.015 = 150 bps)
- `DiscountCurveSpec(...)`
- `ConstraintsSpec(allow_leverage=False, max_leverage=1.0, allow_short=False, min_allocation=0.0)`
  - `min_allocation`: minimum equity allocation floor (default 0.0; only meaningful if `allow_short=True`)

### 6.2 Core functions
- `alpha_star(market: MarketAssumptions, gamma: float, constraints: ConstraintsSpec = ..., *, variant="merton") -> float`
  - Implements the two-tier borrowing rate model (§4.2): computes `alpha_unlev` first, then conditionally computes `alpha_lev` using `r_b = r + borrowing_spread` when leverage is allowed and `alpha_unlev > 1`
- `human_capital_pv(profile: InvestorProfile, curve: DiscountCurveSpec, *, t_max=100) -> float`
- `recommended_stock_share(profile, market, curve, constraints=...) -> AllocationResult`

`AllocationResult` includes:
- `alpha_star: float` — the two-tier risky share from §4.2 (after borrowing-rate adjustment, before human capital)
- `alpha_unconstrained: float` — the raw Merton result before any clamping (`alpha_star * (1 + H/W)`)
- `human_capital: float`
- `alpha_recommended: float` — the final clamped allocation
- `leverage_applied: bool` — whether the result uses the borrowing-rate formula (`r_b` instead of `r`)
- `borrowing_cost_drag: float` — reduction in alpha due to borrowing spread: `(alpha_unlev - alpha_lev) / gamma*sigma^2` equivalent, for educational display
- `explain: str`
- `components: dict` (intermediate values for debugging/education)

### 6.3 Strategy comparison
- `compare_strategies(profile, market, curve, strategies=[...]) -> pandas.DataFrame`

### 6.4 Visualization helpers
- `plot_balance_sheet(result, ...)`
- `plot_strategy_bars(comparison_df, ...)`
- `plot_glidepath(profiles_over_time, ...)`
- `plot_sensitivity_tornado(sensitivity_df, ...)`
- `plot_heatmap(grid_df, x, y, value="alpha", ...)`
- `export_report(out_dir, figures=[...], summary_md=...)`

---

## 7. Visualization requirements

### 7.1 Design principles
- **Explainability-by-visuals**: show H vs W; show what drives alpha
- Minimal chart junk; consistent typography; readable on mobile
- Export to PNG + SVG
- No hard-coded colors in core logic; allow user theming

### 7.2 Must-have charts (v1.0)
1. **Balance Sheet Waterfall**
   - Bars: `W`, `H`, and total `W+H`
   - Annotate `H/W` ratio prominently

2. **Strategy Comparison Bars**
   - Choi allocation vs 60/40 vs 100-age vs parametric TDF
   - Optionally include “recommended band” if sensitivity added
   - When leverage is enabled, show the leveraged Choi allocation alongside the capped-at-1.0 version so users can see the effect of the leverage decision

3. **Glide Path**
   - alpha_t vs age, with overlays for rules of thumb
   - When leverage is enabled: draw a horizontal line or shaded region at alpha=1.0 marking the “leverage zone” boundary above it
   - Optional: show W growth + H decline on secondary panel (future)

4. **Sensitivity Tornado**
   - Vary one input at a time:
     - `mu`, `sigma`, `r`, `gamma`, income growth `g`, retirement age, `borrowing_spread`
   - Rank by impact on `alpha_t`

5. **Heatmaps**
   - alpha over `(W, income)` and/or `(gamma, mu)`
   - Great for blog posts and intuition building

### 7.3 Optional charts (v1.1+)
- Monte Carlo fan chart of W(t)
- “Utility loss vs heuristic” bar chart
- Efficient frontier of “alpha vs downside risk” under model assumptions

---

## 8. CLI spec

Command:
- `practicalfinance alloc --profile profile.yaml --out ./out --format png --report`

Outputs:
- `out/allocation.json`
- `out/summary.md`
- `out/charts/*.png` and/or `*.svg`

Flags:
- `--mu 0.05 --r 0.02 --sigma 0.18`
- `--real / --nominal`
- `--tmax 100`
- `--allow-leverage --max-leverage 1.5`
- `--borrowing-spread 0.015` (decimal; default 0.0)
- `--strategy-set basic|extended`

---

## 9. Configuration formats

### 9.1 YAML profile example
```yaml
age: 25
retirement_age: 67
investable_wealth: 25000
after_tax_income: 70000
risk_tolerance: 5

income_model:
  type: growth
  g: 0.01

benefit_model:
  type: none

mortality_model:
  type: none

discount_curve:
  type: constant
  rate: 0.02

market:
  mu: 0.05
  r: 0.02
  sigma: 0.18
  real: true
  borrowing_spread: 0.015  # 150 bps above risk-free rate (only used when leverage enabled)
````

---

## 10. Testing & quality

### 10.1 Tests

* Unit tests for:

  * clamp behavior
  * alpha_star sanity (monotonicity in gamma, sigma)
  * human capital PV with known closed forms (flat income, constant discount)
  * strategy outputs
* Leverage-specific tests:

  * `alpha_star` with leverage: verify it uses `r_b` when unleveraged result exceeds 1.0
  * Borrowing spread that exactly kills leverage benefit → result should be 1.0
  * `max_leverage` cap is respected (result ≤ `L_max`)
  * Leverage disabled (default) → result never exceeds 1.0
  * Edge case: `mu <= r_b` → leverage is never optimal (alpha_lev ≤ 0 for leveraged portion)
  * `borrowing_spread = 0` → frictionless leverage (alpha_lev = alpha_unlev)
* Golden tests:

  * archetype profiles produce stable expected ranges
* Viz smoke tests:

  * ensure chart functions run and save files

### 10.2 Engineering standards

* Type hints everywhere
* `ruff` + `black` formatting
* `pytest` + coverage
* CI: GitHub Actions
* Semantic versioning

---

## 11. Documentation

### 11.1 README must include

* 60-second intro + why human capital matters
* Install + quickstart snippet
* Example charts (static images)
* How to interpret results
* Disclaimers

### 11.2 Methodology doc

* Definitions: W, H, gamma, mu/r/sigma
* Discounting and mortality choices
* Limitations (income uncertainty, housing ignored, etc.)

---

## 12. Roadmap

### v0.1 (MVP)

* Core alpha + human capital PV (flat + growth income)
* Basic charts (bars + balance sheet)
* CLI alloc + export

### v0.5

* Profile-based income curves + survival model
* Glide path + heatmaps
* Strategy comparison module

### v1.0

* Polished docs + notebooks
* Sensitivity tornado + report exporter
* Optional Monte Carlo module (behind extra dependency)

### v1.1+

* Home equity + mortgage extension
* Multi-asset (stocks, bonds, TIPS, intl) extension
* Optional bequest motive + constraints tuning

---

## 13. Open questions (to resolve in implementation)

1. **Risk tolerance mapping**: How to map 1–10 into gamma?

   * Provide options:

     * “direct gamma” mode
     * “rt→gamma” mapping with documented defaults
2. **Discounting for income**:

   * Constant r, term structure, or risk-adjusted discount
3. **Return assumptions**:

   * Real vs nominal consistency and inflation handling
4. **Default income profile**:

   * Keep minimal + transparent, encourage user-supplied CSV
5. **Handling W ≤ 0**:

   * Default error vs defined fallback

---

## 14. Success criteria

* Produces allocations that are:

  * stable, reproducible
  * explainable with one glance at charts
* Users can:

  * plug in a profile and get a report in < 60 seconds
  * reproduce the archetype examples in notebooks
  * explore sensitivity without writing custom code

---
