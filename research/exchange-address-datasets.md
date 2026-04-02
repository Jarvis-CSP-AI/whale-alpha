# Exchange Wallet Address Datasets — Research

Open-source and publicly available datasets of known cryptocurrency exchange wallet addresses,
for cross-referencing against the Whale Alert historical archive (98K transactions, 2018-2026).

Last updated: 2026-04-02 (revised after validation)

---

## Status: External Datasets Unavailable — Self-Labeling Approach Used

**EVEREST and Labelbase repos are both offline** (removed or made private as of April 2026).
The planned approach of downloading external exchange address datasets was not viable.

Instead, we built a **self-labeling pipeline** that leverages Whale Alert's own exchange labels
already embedded in the archive. The key insight: ~85% of records already have exchange names
in the `from`/`to` fields. We extracted all (blockchain, address) → exchange mappings from those
labeled records, then used the resulting lookup table to identify exchanges in the remaining
unlabeled transactions.

**Results:** 92.7% of transactions have at least one side labeled, 82.5% have both sides labeled.
See `src/enrich_with_exchanges.py` and `data/exchange-lookup.json.gz`.

---

## Tier 1: High-Quality (DEAD LINKS — Archived for Reference)

### 1. EVEREST (by Vacuumlabs) — OFFLINE
- **URL:** https://github.com/vacuumlabs/everest-research / https://everest.research/
- **Was:** Best academic-quality dataset. Hierarchical entity clustering. MIT license.
  Covered BTC, ETH, LTC, BCH, DOGE, Dash, Zcash, Bitcoin SV.
- **Status:** Repo removed or made private as of April 2026. No archive mirror found.

### 2. Labelbase (by ZeroxAnalytics) — OFFLINE
- **URL:** https://github.com/zeroxanalytics/labels / https://labelbase.info/
- **Was:** Etherscan label scraper + community contributions. MIT license. ~50K+ labeled addresses.
- **Status:** Repo and website both inaccessible as of April 2026.

### 3. Etherscan Labeled Accounts — Available but Restricted
- **URL:** https://etherscan.io/accounts (labeled accounts section)
- **Chains:** Ethereum only (PolygonScan, BSCScan variants exist for other EVM chains)
- **Address count:** ~100,000+ labeled addresses total; exchange subset ~10,000-20,000
- **Last updated:** Continuously
- **License:** Proprietary — Etherscan ToS restricts bulk scraping, individual lookups allowed
- **Assessment:** Most comprehensive for Ethereum, but licensing is a gray area for bulk use.
  **Use for spot-checking, not bulk ingestion.**

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

## Chain Coverage Matrix (Self-Labeling Results)

Coverage achieved using the built-in enrichment pipeline (no external datasets needed):

| Chain | Total Txns | Both Labeled | From Only | To Only | Neither |
|---|---|---|---|---|---|
| **Ethereum** | 54,898 | 88.4% | 1.4% | 5.1% | 5.1% |
| **Bitcoin** | 24,151 | 82.7% | 1.5% | 4.2% | 11.6% |
| **Tron** | 11,248 | 90.4% | 1.0% | 3.2% | 5.4% |
| **Ripple** | 5,751 | 27.9% | 28.6% | 24.1% | 19.4% |
| **Solana** | 1,520 | 45.1% | 18.2% | 22.8% | 13.9% |
| **Dogecoin** | 663 | 79.8% | 2.7% | 7.5% | 10.0% |
| **Litecoin** | 121 | 78.5% | 3.3% | 5.0% | 13.2% |
| **Bitcoin Cash** | 65 | 73.8% | 4.6% | 7.7% | 13.9% |
| **Cardano** | 42 | 40.5% | 21.4% | 16.7% | 21.4% |
| **Algorand** | 40 | 42.5% | 20.0% | 17.5% | 20.0% |
| **Polygon** | 12 | 75.0% | 8.3% | 8.3% | 8.4% |

**Overall: 92.7% have at least one side labeled, 82.5% have both sides labeled.**

The lookup table contains **279,411 unique (chain, address) pairs** across **65 identified exchanges**.

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
