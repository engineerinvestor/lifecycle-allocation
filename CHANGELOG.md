# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-02-19

### Added

- Core allocation engine implementing Merton-style optimal risky share (`alpha_star`) with a two-tier borrowing rate model that uses separate lending and borrowing rates for leverage decisions
- Human capital present value calculation (`human_capital_pv`) combining future income, retirement benefits, survival probability, and discount curves into a single PV estimate
- Four pluggable income models: flat (constant real income), constant-growth, CGM education-based polynomial profile, and user-supplied CSV schedules
- Flat retirement benefit model with support for fixed annual amounts or income replacement rates
- Strategy comparison module (`compare_strategies`) benchmarking the lifecycle allocation against 60/40, 100-minus-age, and parametric target-date fund heuristics
- Visualization suite with balance sheet waterfall charts and strategy comparison bar charts, using a consistent theme system
- CLI interface (`lifecycle-allocation alloc`) that loads YAML profiles, computes allocations, and writes JSON results, Markdown summaries, and optional charts to an output directory
- YAML/JSON profile loader with support for all configuration sections (investor, income, benefits, mortality, discounting, market, constraints)
- Human-readable explanation text generator with leverage risk disclosures when applicable
- Three example YAML profiles spanning the lifecycle: young saver (age 25), mid-career (age 45), and near-retirement (age 60)
- Interactive tutorial notebook with Colab support covering the full library API
- Full test suite with >90% code coverage

[Unreleased]: https://github.com/engineerinvestor/lifecycle-allocation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/engineerinvestor/lifecycle-allocation/releases/tag/v0.1.0
