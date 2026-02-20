# lifecycle-allocation

**lifecycle-allocation** is a Python library for computing data-driven stock/bond allocation recommendations based on lifecycle portfolio theory. Instead of relying on rules of thumb like "100 minus your age," it treats your future earning power as an asset, your human capital, and uses it alongside your financial wealth to derive a personalized equity allocation grounded in economic theory.

The framework is inspired by [Choi et al. (2024)](https://www.nber.org/papers/w34166) and implements a Merton-style optimal risky share adjusted for human capital, with support for multiple income models, mortality adjustment, leverage constraints, and visual analytics.

## What You'll Find

| Page | Description |
|---|---|
| [Quick Start](quickstart.md) | Step-by-step tutorial: create a profile, compute an allocation, generate charts |
| [Configuration](configuration.md) | Complete YAML/JSON profile reference with every field documented |
| [Methodology](methodology.md) | Mathematical framework: formulas, income models, discounting, edge cases |
| [API Reference](api.md) | Full Python API: all dataclasses, functions, signatures, and examples |
| [Examples](examples.md) | Three archetype profiles with computed results and interpretation |

## Quick Links

- **Install:** `pip install lifecycle-allocation`
- **Source:** [github.com/engineerinvestor/lifecycle-allocation](https://github.com/engineerinvestor/lifecycle-allocation)
- **PyPI:** [pypi.org/project/lifecycle-allocation](https://pypi.org/project/lifecycle-allocation/)
- **Tutorial notebook:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/lifecycle-allocation/blob/main/examples/notebooks/tutorial.ipynb)

!!! warning "Disclaimer"
    This library is for education and research purposes only. It is not investment advice.
