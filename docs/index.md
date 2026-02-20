# lifecycle-allocation

A Python library implementing a practical lifecycle portfolio choice framework inspired by [Choi et al.](https://www.nber.org/papers/w34166)

## Overview

Most portfolio allocation "rules" are single-variable heuristics: 60/40, 100-minus-age, target-date funds. They ignore the biggest asset most people own -- their future earning power.

This library takes a **balance-sheet** view of your finances. Future earnings (human capital) act like a bond-like asset, and accounting for them changes how much stock risk you should take.

## Getting Started

```bash
pip install lifecycle-allocation
```

See the [Quick Start](quickstart.md) guide for usage examples.

## How It Works

1. Compute a **baseline risky share** (Merton-style): `alpha* = (mu - r) / (gamma * sigma^2)`
2. Estimate **human capital** H as the present value of future earnings
3. Adjust: `alpha = alpha* x (1 + H/W)`, clamped to [0, 1]

For the full mathematical framework, see [Methodology](methodology.md).
