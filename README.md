# 🐋 Whale Alpha

**Whale transaction analytics pipeline — backtesting and signal generation from on-chain whale movement data.**

## Overview

Whale Alpha ingests historical whale transaction data to build, backtest, and deploy trading signals based on large on-chain movements. The core idea is that significant transfers between wallets and exchanges carry predictive information about future price action — especially when whales move assets to or from exchange hot wallets.

This project focuses on:

- **Signal Engineering** — Transforming raw whale transfer logs into actionable alpha signals (e.g., exchange inflow/outflow velocity, whale wallet clustering, cross-chain bridge flow).
- **Backtesting Framework** — Rigorous evaluation of signals against historical price data with realistic slippage and latency assumptions.
- **Pipeline Integration** — Output signal features designed to plug into an existing crypto trading system.

## Data Source

We use the **Whale Alert Free Historical Archive**, which provides:

| Detail              | Value                                  |
|---------------------|----------------------------------------|
| Transactions        | ~98,000 whale movements                |
| Date Range          | 2018 – 2026                            |
| Blockchains         | 12 (Bitcoin, Ethereum, Ripple, Tron, etc.) |
| Format              | JSON (gzip-compressed)                 |
| License             | Free tier — [whale-alert.io](https://whale-alert.io) |

The archive is stored at `data/whale-alerts-archive.json.gzip` and includes fields such as transaction hash, blockchain, from/to addresses, amount, owner type (wallet/exchange/unknown), and timestamp.

> **Note:** The free archive covers transactions ≥ $500K USD equivalent. API keys are available for real-time streaming of smaller transactions.

## Project Structure

```
whale-alpha/
├── data/                   # Raw and processed datasets
│   └── whale-alerts-archive.json.gzip
├── notebooks/              # Jupyter notebooks for exploration & viz
├── research/               # Strategy docs, findings, backtest results
├── src/                    # Python package source
│   └── __init__.py
├── tests/                  # Unit and integration tests
│   └── __init__.py
├── .gitignore
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) or pip

### Installation

```bash
# Clone the repo
git clone https://github.com/Jarvis-CSP-AI/whale-alpha.git
cd whale-alpha

# Create virtual environment
uv venv && source .venv/bin/activate   # or: python -m venv .venv

# Install dependencies (once requirements.txt is added)
pip install -r requirements.txt
```

### Quick Start

```python
import gzip, json

with gzip.open("data/whale-alerts-archive.json.gzip", "rt") as f:
    transactions = json.load(f)

print(f"Loaded {len(transactions)} whale transactions")
print(f"Sample: {json.dumps(transactions[0], indent=2)}")
```

### Running Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
