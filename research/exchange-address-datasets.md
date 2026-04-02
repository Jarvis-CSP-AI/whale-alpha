# Exchange Wallet Address Datasets — Research

Open-source and publicly available datasets of known cryptocurrency exchange wallet addresses,
for cross-referencing against the Whale Alert historical archive (98K transactions, 2018-2026).

Last updated: 2026-04-02

---

## Tier 1: High-Quality, Actively Maintained

### 1. EVEREST (by Vacuumlabs)
- **URL:** https://github.com/vacuumlabs/everest-research / https://everest.research/
- **Chains:** Bitcoin, Ethereum, Litecoin, Bitcoin Cash, Dogecoin, Dash, Zcash, Bitcoin SV
- **Address count:** ~5,000+ labeled addresses (entities including exchanges, mining pools, services)
- **Last updated:** ~2022 (paper published 2023)
- **License:** MIT (code), data under permissive terms
- **Assessment:** Best academic-quality dataset. Hierarchical entity clustering.
  Covers 5 of our 12 chains (BTC, ETH, LTC, BCH, DOGE). **Primary source for BTC/LTC/BCH/DOGE.**

### 2. Labelbase (by ZeroxAnalytics)
- **URL:** https://github.com/zeroxanalytics/labels / https://labelbase.info/
- **Chains:** Ethereum (primary), some EVM chains via Etherscan-compatible scrapers
- **Address count:** ~50,000+ labeled addresses total; exchange subset ~5,000-15,000
- **Last updated:** 2024-2025 (actively maintained)
- **License:** MIT
- **Assessment:** Etherscan label scraper + community contributions. Filterable by "exchange" category.
  **Primary supplement for ETH coverage.**

### 3. Etherscan Labeled Accounts
- **URL:** https://etherscan.io/accounts (labeled accounts section)
- **Chains:** Ethereum only (PolygonScan, BSCScan variants exist for other EVM chains)
- **Address count:** ~100,000+ labeled addresses total; exchange subset ~10,000-20,000
- **Last updated:** Continuously
- **License:** Proprietary — Etherscan ToS restricts bulk scraping, individual lookups allowed
- **Assessment:** Most comprehensive for Ethereum, but licensing is a gray area for bulk use.
  Good for validation, risky for production pipeline. **Use for spot-checking, not bulk ingestion.**

---

## Tier 2: Good Quality, Niche or Less Maintained

### 4. WalletExplorer (by Martina Kroll et al.)
- **URL:** https://www.walletexplorer.com/
- **Chains:** Bitcoin only
- **Address count:** ~500+ exchange clusters (many addresses per cluster)
- **Last updated:** ~2019-2021 (research project, not actively maintained)
- **License:** Academic use only — no public download, must contact authors
- **Assessment:** Pioneering Bitcoin address clustering work. Access restricted. **Backup for BTC if EVEREST insufficient.**

### 5. Ergo / Labeled Address Datasets
- **URL:** https://github.com/ergo-research/labeled-addresses (and similar academic repos)
- **Chains:** Ethereum primarily
- **Address count:** ~1,000-5,000
- **Last updated:** 2021-2022
- **Assessment:** Academic subset. Superseded by EVEREST and Labelbase for our purposes.

---

## Tier 3: Community / Small-Scale Lists

Various GitHub repos with exchange deposit addresses — small, incomplete, unmaintained:
- `bitcoinebook/exchange-addresses` — Bitcoin, ~100-500 addresses
- `0x7229b4b1/ethereum-exchange-addresses` — Ethereum, ~200-500 addresses
- `phahnek/crypto-exchange-addresses` — Multi-exchange collection

**Assessment:** Useful as supplementary validation data only. Not primary sources.

---

## Chain Coverage Matrix

| Chain (in our data) | EVEREST | Labelbase | Etherscan | WalletExplorer | GitHub misc | Coverage |
|---|---|---|---|---|---|---|
| **Ethereum** (54K txns) | ✅ | ✅✅ | ✅✅ | ❌ | ✅ | **Excellent** |
| **Bitcoin** (24K txns) | ✅✅ | ❌ | ❌ | ✅✅ | ✅ | **Good** |
| **Tron** (11K txns) | ❌ | ❌ | ❌ | ❌ | ❌ | **None** |
| **Ripple** (5.7K txns) | ❌ | ❌ | ❌ | ❌ | ❌ | **None** |
| **Solana** (1.5K txns) | ❌ | ❌ | ❌ | ❌ | ❌ | **None** |
| **Dogecoin** (663 txns) | ✅ | ❌ | ❌ | ❌ | ✅ | **Weak** |
| **Litecoin** (121 txns) | ✅ | ❌ | ❌ | ❌ | ✅ | **Weak** |
| **Bitcoin Cash** (65 txns) | ✅ | ❌ | ❌ | ❌ | ✅ | **Weak** |
| **Cardano** (42 txns) | ❌ | ❌ | ❌ | ❌ | ❌ | **None** |
| **Algorand** (40 txns) | ❌ | ❌ | ❌ | ❌ | ❌ | **None** |
| **Polygon** (12 txns) | ❌ | ✅ (PolygonScan) | ✅ (PolygonScan) | ❌ | ❌ | **Moderate** |

~80% of our transactions (ETH + BTC) have good coverage. The remaining 20% need alternative approaches.

---

## Commercial Sources (Reference Only)

| Provider | Chains | Notes |
|---|---|---|
| **Chainalysis** | All | Gold standard, enterprise pricing |
| **Elliptic** | All | Academic partnerships sometimes available |
| **Whale Alert** (internal) | All | Used for their own alerts, not publicly available |
| **Nansen** | ETH + EVM | Paid, good for ETH DeFi/CEX labels |
| **Arkham Intelligence** | Multi-chain | Some labels public via Arkham Explore, no bulk export |

---

## Strategy for Closing the Gaps

### Phase 1 — Cover ~80% of transactions (ETH + BTC)
1. Download EVEREST dataset → primary source for BTC, ETH, LTC, BCH, DOGE
2. Supplement with Labelbase → additional ETH exchange labels
3. Use Etherscan labeled accounts for validation

### Phase 2 — EVM chains (Polygon)
4. Scrape PolygonScan labeled accounts (similar structure to Etherscan)
5. Labelbase may have some Polygon coverage via EVM compatibility

### Phase 3 — Non-EVM chains (Tron, XRP, Solana, Cardano, Algorand)
These have essentially zero open-source exchange address datasets. Options:

**a) Block explorer label scraping:**
- Tron: Tronscan.org has labeled accounts (scrapeable)
- XRP: XRPScan has some labeled accounts
- Solana: Solscan/SolanaFM have some labels
- Cardano: CardanoScan has limited labels
- Algorand: Avascan has limited labels

**b) Exchange transparency pages:**
Many exchanges publish their deposit/withdrawal addresses:
- Binance transparency page
- Coinbase proof-of-reserves (published periodically)
- Kraken (security audits)
- OKX, Bybit transparency pages
- Crypto.com proof-of-reserves

**c) Heuristic identification:**
If an address exhibits exchange-like behavior (high volume, many unique counterparties, regular sweep patterns), flag it as a probable exchange wallet. This is noisy but better than nothing.

---

## Transaction Volume by Chain (for prioritization)

```
Ethereum:    54,898 txns (55.7%) — $X avg value
Bitcoin:     24,151 txns (24.5%) — $X avg value
Tron:        11,248 txns (11.4%) — $X avg value
Ripple:       5,751 txns  (5.8%) — $X avg value
Solana:       1,520 txns  (1.5%) — $X avg value
Dogecoin:       663 txns  (0.7%)
Litecoin:       121 txns  (0.1%)
Bitcoin Cash:    65 txns  (0.1%)
Cardano:         42 txns  (0.1%)
Algorand:        40 txns  (0.1%)
Polygon:         12 txns  (0.0%)
Plasma:           5 txns  (0.0%)
```

**Priority order:** ETH > BTC > Tron > XRP > Solana > rest

ETH + BTC alone cover 80% of transactions and have good open-source label coverage.
Tron (11.4%) is the biggest gap — worth investing effort in Tronscan scraping or transparency pages.
