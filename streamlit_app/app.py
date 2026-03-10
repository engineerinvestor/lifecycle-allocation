"""Lifecycle Portfolio Allocation Explorer — interactive Streamlit app."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lifecycle_allocation import (
    INDUSTRY_BETAS,
    AllocationResult,
    HumanCapitalSpec,
    IncomeModelSpec,
    InvestorProfile,
    MarketAssumptions,
    compare_strategies,
    recommended_stock_share,
    suggested_beta,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLORS = {
    "blue": "#2166ac",
    "orange": "#d6604d",
    "green": "#4dac26",
    "purple": "#7b3294",
    "grey": "#878787",
    "light_blue": "#92c5de",
    "light_orange": "#f4a582",
}

RISK_LABELS = {
    1: "Very Conservative",
    2: "Conservative",
    3: "Moderately Conservative",
    4: "Moderate-",
    5: "Moderate",
    6: "Moderate+",
    7: "Moderately Aggressive",
    8: "Aggressive",
    9: "Very Aggressive",
    10: "Maximum Growth",
}

PRESETS = {
    "Custom": None,
    "Young Tech Worker": {
        "age": 28,
        "retirement_age": 67,
        "income": 150_000,
        "wealth": 50_000,
        "risk_tolerance": 7,
        "industry": "tech_with_rsus",
    },
    "Mid-Career Government": {
        "age": 42,
        "retirement_age": 62,
        "income": 85_000,
        "wealth": 400_000,
        "risk_tolerance": 5,
        "industry": "government",
    },
    "Pre-Retirement Professional": {
        "age": 58,
        "retirement_age": 65,
        "income": 120_000,
        "wealth": 1_200_000,
        "risk_tolerance": 4,
        "industry": "professional_services",
    },
}


def _fmt_industry(key: str) -> str:
    """Convert industry key to display name."""
    return key.replace("_", " ").title()


def _industry_key(display: str) -> str:
    """Convert display name back to industry key."""
    return display.lower().replace(" ", "_")


INDUSTRY_OPTIONS = [_fmt_industry(k) for k in INDUSTRY_BETAS] + ["Custom"]


# ---------------------------------------------------------------------------
# Cached computation helpers
# ---------------------------------------------------------------------------


@st.cache_data
def _compute_allocation(
    age: int,
    retirement_age: int,
    income: float,
    wealth: float,
    risk_tolerance: int,
    beta: float,
    mu: float,
    r: float,
    sigma: float,
    income_growth: float,
) -> AllocationResult:
    profile = InvestorProfile(
        age=age,
        retirement_age=retirement_age,
        investable_wealth=wealth,
        after_tax_income=income,
        risk_tolerance=risk_tolerance,
        income_model=IncomeModelSpec(type="growth", g=income_growth),
        human_capital_model=HumanCapitalSpec(beta=beta),
    )
    market = MarketAssumptions(mu=mu, r=r, sigma=sigma)
    return recommended_stock_share(profile, market)


@st.cache_data
def _compute_strategies(
    age: int,
    retirement_age: int,
    income: float,
    wealth: float,
    risk_tolerance: int,
    beta: float,
    mu: float,
    r: float,
    sigma: float,
    income_growth: float,
) -> pd.DataFrame:
    profile = InvestorProfile(
        age=age,
        retirement_age=retirement_age,
        investable_wealth=wealth,
        after_tax_income=income,
        risk_tolerance=risk_tolerance,
        income_model=IncomeModelSpec(type="growth", g=income_growth),
        human_capital_model=HumanCapitalSpec(beta=beta),
    )
    market = MarketAssumptions(mu=mu, r=r, sigma=sigma)
    return compare_strategies(profile, market)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Lifecycle Allocation Explorer",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

with st.sidebar:
    st.title("Inputs")

    # --- Quick presets ---
    preset_name = st.radio("Quick Presets", list(PRESETS.keys()), horizontal=True)
    preset = PRESETS[preset_name]

    st.divider()

    # --- Your Profile ---
    st.subheader("Your Profile")

    age = st.slider(
        "Age",
        min_value=22,
        max_value=80,
        value=preset["age"] if preset else 30,
    )
    retirement_age = st.slider(
        "Retirement age",
        min_value=55,
        max_value=75,
        value=preset["retirement_age"] if preset else 67,
    )
    income = st.number_input(
        "Annual after-tax income ($)",
        min_value=0,
        max_value=500_000,
        value=preset["income"] if preset else 80_000,
        step=5_000,
    )
    wealth = st.number_input(
        "Investable wealth ($)",
        min_value=1_000,
        max_value=5_000_000,
        value=preset["wealth"] if preset else 100_000,
        step=10_000,
    )
    risk_tolerance = st.slider(
        "Risk tolerance",
        min_value=1,
        max_value=10,
        value=preset["risk_tolerance"] if preset else 5,
        help="1 = Very Conservative, 10 = Maximum Growth",
    )
    st.caption(f"_{RISK_LABELS[risk_tolerance]}_")

    st.divider()

    # --- Your Job & Human Capital ---
    st.subheader("Your Job & Human Capital")

    default_industry_display = (
        _fmt_industry(preset["industry"]) if preset else "General Private Sector"
    )
    industry_display = st.selectbox(
        "Industry",
        INDUSTRY_OPTIONS,
        index=INDUSTRY_OPTIONS.index(default_industry_display),
        help=(
            "Your industry affects how closely your future earnings move with the "
            "stock market. Government and tenured education jobs are very stable "
            "(beta near 0), while startup and commission roles are highly correlated "
            "with the market (beta near 1)."
        ),
    )

    if industry_display == "Custom":
        beta = st.slider(
            "Human capital beta",
            min_value=0.0,
            max_value=1.0,
            value=0.30,
            step=0.05,
            help="0 = income is bond-like (very stable), 1 = income is stock-like (volatile)",
        )
    else:
        beta = suggested_beta(_industry_key(industry_display))
        st.caption(f"Beta = {beta:.2f}")

    st.divider()

    # --- Market Assumptions ---
    with st.expander("Market Assumptions"):
        mu = st.slider(
            "Expected stock return",
            min_value=0.02,
            max_value=0.12,
            value=0.05,
            step=0.005,
            format="%.1f%%",
            help="Real (inflation-adjusted) expected annual return",
        )
        r = st.slider(
            "Risk-free rate",
            min_value=0.00,
            max_value=0.06,
            value=0.02,
            step=0.005,
            format="%.1f%%",
            help="Real risk-free rate (e.g., TIPS yield)",
        )
        sigma = st.slider(
            "Stock volatility",
            min_value=0.10,
            max_value=0.30,
            value=0.18,
            step=0.01,
            format="%.0f%%",
            help="Annualized standard deviation of stock returns",
        )
        income_growth = st.slider(
            "Income growth rate",
            min_value=0.00,
            max_value=0.05,
            value=0.02,
            step=0.005,
            format="%.1f%%",
            help="Real annual income growth rate",
        )


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

result = _compute_allocation(
    age, retirement_age, income, wealth, risk_tolerance, beta, mu, r, sigma, income_growth
)
strategies_df = _compute_strategies(
    age, retirement_age, income, wealth, risk_tolerance, beta, mu, r, sigma, income_growth
)

h = result.human_capital
w = wealth
hw_ratio = h / w if w > 0 else 0.0
h_bond = (1.0 - beta) * h
h_equity = beta * h


# ---------------------------------------------------------------------------
# Hero Section
# ---------------------------------------------------------------------------

st.title("Lifecycle Portfolio Allocation Explorer")
st.markdown(
    "Discover your personalized stock/bond allocation based on your age, income, "
    "wealth, job stability, and risk tolerance."
)

col1, col2, col3 = st.columns(3)
col1.metric("Recommended Equity", f"{result.alpha_recommended:.0%}")
col2.metric("Human Capital", f"${h:,.0f}")
col3.metric("H/W Ratio", f"{hw_ratio:.1f}x")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    ["Your Allocation", "How Your Job Matters", "Lifecycle Glide Path", "Learn More"]
)

# ---- Tab 1: Your Allocation ------------------------------------------------
with tab1:
    # Balance sheet waterfall
    st.subheader("Your Total Wealth Balance Sheet")

    waterfall_fig = go.Figure(
        go.Waterfall(
            x=["Financial Wealth", "Bond-like HC", "Equity-like HC", "Total Wealth"],
            y=[w, h_bond, h_equity, 0],
            measure=["absolute", "relative", "relative", "total"],
            text=[f"${w:,.0f}", f"${h_bond:,.0f}", f"${h_equity:,.0f}", f"${w + h:,.0f}"],
            textposition="outside",
            connector_line_color="rgba(0,0,0,0)",
            decreasing_marker_color=COLORS["orange"],
            increasing_marker_color=COLORS["green"],
            totals_marker_color=COLORS["blue"],
        )
    )
    waterfall_fig.update_layout(
        yaxis_title="Dollars",
        showlegend=False,
        margin=dict(t=20, b=40),
        height=380,
    )
    st.plotly_chart(waterfall_fig, use_container_width=True)

    st.markdown(
        "**Financial wealth** is what you have invested today. "
        "**Human capital** is the present value of your future earnings. "
        "The bond-like portion is the stable part of your income; "
        "the equity-like portion moves with the market."
    )

    # Strategy comparison
    st.subheader("Strategy Comparison")

    display_df = strategies_df.copy()
    display_df["Equity %"] = display_df["allocation"].apply(lambda x: f"{x:.0%}")
    display_df["Bond %"] = display_df["allocation"].apply(lambda x: f"{1 - x:.0%}")
    display_df = display_df.rename(columns={"strategy": "Strategy", "description": "Description"})
    st.dataframe(
        display_df[["Strategy", "Equity %", "Bond %", "Description"]],
        hide_index=True,
        use_container_width=True,
    )

    # Horizontal bar chart
    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(
            y=strategies_df["strategy"],
            x=strategies_df["allocation"],
            orientation="h",
            marker_color=[COLORS["blue"], COLORS["grey"], COLORS["orange"], COLORS["purple"]],
            text=strategies_df["allocation"].apply(lambda x: f"{x:.0%}"),
            textposition="outside",
        )
    )
    bar_fig.update_layout(
        xaxis_title="Equity Allocation",
        xaxis_tickformat=".0%",
        xaxis_range=[0, 1.05],
        margin=dict(t=20, b=40),
        height=280,
        showlegend=False,
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    # Explanation
    with st.expander("Detailed Explanation"):
        st.text(result.explain)


# ---- Tab 2: How Your Job Matters --------------------------------------------
with tab2:
    st.subheader("How Your Job Affects Your Allocation")

    st.markdown(
        "Your income is part of your total wealth. If your job is very stable "
        "(like government work), your future earnings act like a bond, letting you "
        "invest more aggressively. If your income moves with the stock market "
        "(like a startup with equity compensation), you already have significant "
        "market exposure through your job, so you should invest more conservatively."
    )

    # Concentration risk callout for high-beta industries
    HIGH_BETA_INDUSTRIES = {
        "tech_with_rsus",
        "tech_startup",
        "startup_equity_heavy",
        "commission_sales",
        "finance_trading",
    }
    selected_industry_key = (
        _industry_key(industry_display) if industry_display != "Custom" else None
    )
    if selected_industry_key in HIGH_BETA_INDUSTRIES or (
        industry_display == "Custom" and beta >= 0.55
    ):
        st.warning(
            "**Single-stock concentration risk.** Beta captures how closely your "
            "income tracks the *broad stock market*, not the risk of holding a "
            "single company's stock. RSUs and startup equity concentrate your "
            "wealth in one firm, which carries uncompensated idiosyncratic risk: "
            "higher volatility, potential for total loss, and correlated downside "
            "(a stock crash can coincide with layoffs and RSU forfeiture). "
            "The allocation shown is a **floor**, not a ceiling, on how much to "
            "reduce equity. If you hold significant unvested RSUs or startup "
            "equity, consider the combined risk of those holdings plus your "
            "investment portfolio.",
            icon="\u26a0\ufe0f",
        )

    # Beta sensitivity chart
    st.subheader("Allocation vs. Human Capital Beta")

    betas = np.linspace(0.0, 1.0, 21)
    allocs_for_beta = []
    for b in betas:
        r_b = _compute_allocation(
            age,
            retirement_age,
            income,
            wealth,
            risk_tolerance,
            float(b),
            mu,
            r,
            sigma,
            income_growth,
        )
        allocs_for_beta.append(r_b.alpha_recommended)

    beta_fig = go.Figure()
    beta_fig.add_trace(
        go.Scatter(
            x=betas,
            y=allocs_for_beta,
            mode="lines",
            line=dict(color=COLORS["blue"], width=3),
            name="Allocation",
        )
    )
    # Marker for selected beta
    beta_fig.add_trace(
        go.Scatter(
            x=[beta],
            y=[result.alpha_recommended],
            mode="markers",
            marker=dict(color=COLORS["orange"], size=14, symbol="diamond"),
            name="Your beta",
        )
    )
    beta_fig.update_layout(
        xaxis_title="Human Capital Beta",
        yaxis_title="Recommended Equity Allocation",
        yaxis_tickformat=".0%",
        height=380,
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(beta_fig, use_container_width=True)

    # Industry comparison table
    st.subheader("Industry Comparison")

    industry_rows = []
    for ind_key, ind_beta in sorted(INDUSTRY_BETAS.items(), key=lambda x: x[1]):
        ind_result = _compute_allocation(
            age,
            retirement_age,
            income,
            wealth,
            risk_tolerance,
            ind_beta,
            mu,
            r,
            sigma,
            income_growth,
        )
        industry_rows.append(
            {
                "Industry": _fmt_industry(ind_key),
                "Beta": f"{ind_beta:.2f}",
                "Equity Allocation": f"{ind_result.alpha_recommended:.0%}",
            }
        )

    ind_df = pd.DataFrame(industry_rows)
    st.dataframe(ind_df, hide_index=True, use_container_width=True, height=500)


# ---- Tab 3: Lifecycle Glide Path -------------------------------------------
with tab3:
    st.subheader("How Allocation Changes Over Your Lifetime")

    st.markdown(
        "When you are young, your future earnings (human capital) dwarf your savings. "
        "This large bond-like asset lets you take more stock market risk. As you age, "
        "human capital shrinks and financial wealth grows, so the optimal stock "
        "allocation naturally decreases. Your job's market sensitivity (beta) shifts "
        "the entire curve downward; the more equity-like your income, the less stock "
        "exposure you need in your portfolio."
    )

    ages = list(range(25, 71))
    betas_to_plot = [0.0, beta, 1.0] if beta not in (0.0, 1.0) else [0.0, 1.0]
    beta_labels = {0.0: "Beta = 0 (stable)", 1.0: "Beta = 1 (volatile)"}
    if beta not in (0.0, 1.0):
        beta_labels[beta] = f"Your beta ({beta:.2f})"

    glide_fig = go.Figure()
    beta_colors = {0.0: COLORS["green"], 1.0: COLORS["orange"]}
    if beta not in (0.0, 1.0):
        beta_colors[beta] = COLORS["blue"]

    for b in betas_to_plot:
        allocs = []
        for a in ages:
            ra = min(retirement_age, 75)
            r_a = _compute_allocation(
                a,
                ra,
                income,
                wealth,
                risk_tolerance,
                float(b),
                mu,
                r,
                sigma,
                income_growth,
            )
            allocs.append(r_a.alpha_recommended)
        glide_fig.add_trace(
            go.Scatter(
                x=ages,
                y=allocs,
                mode="lines",
                name=beta_labels[b],
                line=dict(color=beta_colors[b], width=3),
            )
        )

    # Overlay 100-minus-age
    nma = [(100 - a) / 100 for a in ages]
    glide_fig.add_trace(
        go.Scatter(
            x=ages,
            y=nma,
            mode="lines",
            name="100 minus age",
            line=dict(color=COLORS["grey"], width=2, dash="dash"),
        )
    )

    # Overlay TDF
    from lifecycle_allocation.core.strategies import strategy_parametric_tdf

    tdf = [strategy_parametric_tdf(a, retirement_age) for a in ages]
    glide_fig.add_trace(
        go.Scatter(
            x=ages,
            y=tdf,
            mode="lines",
            name="Target-Date Fund",
            line=dict(color=COLORS["purple"], width=2, dash="dot"),
        )
    )

    glide_fig.update_layout(
        xaxis_title="Age",
        yaxis_title="Equity Allocation",
        yaxis_tickformat=".0%",
        height=450,
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(glide_fig, use_container_width=True)


# ---- Tab 4: Learn More -----------------------------------------------------
with tab4:
    st.subheader("How It Works")

    st.markdown(
        """
**Step 1: Estimate your human capital.**
Your future earnings have a present value, just like a bond. We project your
income forward, adjust for the chance you might not work every year, and
discount it back to today. This is your *human capital*.

**Step 2: Compute the baseline stock allocation.**
Using the equity risk premium (expected stock return minus the risk-free rate),
stock volatility, and your risk tolerance, we compute the theoretically optimal
stock allocation. This is the Merton ratio: higher expected returns and lower
risk aversion push it up; higher volatility pulls it down.

**Step 3: Adjust for your total wealth.**
Your total wealth is your savings *plus* your human capital. Because human
capital is typically bond-like (stable income), having a lot of it means you
can afford to put a larger share of your *financial* wealth into stocks. As
you age and your human capital shrinks, the model naturally reduces your stock
allocation.
"""
    )

    st.subheader("Key Concepts")

    with st.expander("Human Capital"):
        st.markdown(
            "Human capital is the present value of all your future earnings. A 30-year-old "
            "earning $80,000/year with decades of work ahead may have over $1 million in human "
            "capital. It is the largest asset most young people own, even though it does not "
            "appear on any brokerage statement."
        )

    with st.expander("Risk Aversion"):
        st.markdown(
            "Risk aversion (gamma) measures how much you dislike uncertainty. A gamma of 2 "
            "means you are fairly aggressive; a gamma of 10 means you strongly prefer "
            "certainty. The risk tolerance slider maps to gamma: 1 (very conservative) "
            "corresponds to gamma = 10, while 10 (maximum growth) corresponds to gamma = 2."
        )

    with st.expander("The Merton Ratio"):
        st.markdown(
            "The Merton ratio is the starting point for the optimal stock allocation. "
            "It equals the equity risk premium divided by (risk aversion times the variance "
            "of stock returns). Intuitively, you invest more in stocks when the expected "
            "reward is high, volatility is low, and you are comfortable with risk."
        )

    with st.expander("Human Capital Beta"):
        st.markdown(
            "Not all human capital is bond-like. If your income rises and falls with the "
            "stock market (e.g., commission sales, startup equity), part of your human capital "
            "is already equity-like. Beta measures this fraction: 0 means purely stable income, "
            "1 means income that moves perfectly with stocks. A higher beta means you already "
            "have market exposure through your job, so you should hold fewer stocks in your "
            "portfolio."
        )

    with st.expander("Concentration Risk"):
        st.markdown(
            "Beta measures how your income correlates with the *broad stock market*, "
            "but it does not capture the additional risk of holding a single company's stock. "
            "There are several reasons why concentrated positions are riskier than diversified "
            "market exposure:\n\n"
            "- **Higher volatility.** Individual stocks typically have annualized volatility "
            "of 40\u201360%+, compared to ~18% for the broad market. Beta maps your income to "
            "market-correlated risk; the remaining firm-specific volatility is ignored.\n"
            "- **Left-tail risk.** A single company can go to zero; a diversified market "
            "cannot. The standard model assumes log-normal returns, which understates the "
            "catastrophic downside of concentrated positions.\n"
            "- **No extra reward.** Diversified market exposure earns the equity risk premium. "
            "Single-stock exposure carries idiosyncratic risk that is *not compensated* by "
            "higher expected returns.\n"
            '- **The "double whammy."** In downturns, your employer\'s stock price, layoff '
            "probability, and RSU forfeiture risk all spike simultaneously. A single beta "
            "captures average correlation but misses this regime-dependent tail dependence.\n\n"
            "**Practical guidance:** Treat the model's allocation as a floor, not a ceiling. "
            "If you hold significant RSUs or startup equity, consider diversifying vested "
            "shares, using a 10b5-1 plan, and evaluating the combined risk of your unvested "
            "equity plus your investment portfolio."
        )

    st.divider()

    st.subheader("Disclaimer")
    st.info(
        "This tool is for **educational and research purposes only**. It is not investment "
        "advice. The results depend entirely on the assumptions you provide. Consult a "
        "qualified financial advisor before making investment decisions."
    )

    st.subheader("Links")
    st.markdown(
        """
- [GitHub Repository](https://github.com/engineerinvestor/lifecycle-allocation)
- [Documentation](https://engineerinvestor.github.io/lifecycle-allocation/)
- Based on research by James Choi et al.,
  "Optimal Portfolio Choice: Lessons from Our Model" (NBER Working Paper 34166)
"""
    )
