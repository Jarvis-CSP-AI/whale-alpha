#!/usr/bin/env python3
"""
Exchange Address Enrichment Pipeline — Phase 1

Enriches the Whale Alert transaction archive with exchange labels for from/to addresses.

Strategy:
1. Load the whale archive (98K transactions)
2. Build an address-to-exchange lookup table by:
   a. Mining existing from/to labels from the Whale Alert data itself
   b. Extracting blockchain addresses from sub_transactions of labeled transactions
   c. Loading any external datasets (EVEREST, Labelbase) if available in data/exchange-datasets/
3. Cross-reference every transaction's addresses against the lookup table
4. Output enriched data with exchange_from and exchange_to fields
5. Print coverage statistics

No external dependencies — uses only Python stdlib.
"""

import gzip
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_PATH = os.path.join(PROJECT_ROOT, "data", "whale-alerts-archive.json.gzip")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "enriched-archive.json.gz")
LOOKUP_PATH = os.path.join(PROJECT_ROOT, "data", "exchange-lookup.json.gz")
DATASETS_DIR = os.path.join(PROJECT_ROOT, "data", "exchange-datasets")

# Exchange label classification
# Labels that represent exchanges (CEX) — used for the address lookup table
EXCHANGE_LABELS = {
    # Major CEXes
    "binance", "coinbase", "kraken", "bitfinex", "huobi", "okex", "okx", "bybit",
    "bitmex", "gemini", "cryptocom", "ftx", "kucoin", "gateio", "bitstamp",
    "bittrex", "poloniex", "xapo", "bithumb", "htx", "bitso", "robinhood",
    "cumberland", "nexo", "binanceus", "binance beacon deposit",
    # DeFi / protocol labels
    "aave", "uniswap", "wrapped ether", "makerdao", "lido", "curve",
    "compound", "sushiswap", "pancakeswap", "balancer", "beacon depositor",
    # Stablecoin issuers
    "usdc treasury", "tether treasury", "pax treasury", "husd treasury",
    "paxos treasury", "usdc incinerator", "husd incinerator",
    # Notable entities
    "ripple", "bitfinex hack 2016", "kucoin hack 2020", "ftx estate account",
    "binance hack may 2019", "binance safu", "binance charity wallet",
    "binance recovery fund", "binance cmc supply fix",
}

# Labels that are clearly NOT exchanges (mining pools, protocol events, etc.)
NON_EXCHANGE_LABELS = {
    "unknown wallet", "", "f2pool", "poolin", "antpool", "btc.com",
    "viabtc", "slush pool", "ethermine", "f2pool mining pool",
}


def classify_label(label):
    """Classify a Whale Alert label as exchange name or None.

    Returns the normalized exchange name, or None if not an exchange.
    """
    label_lower = label.lower().strip()
    if not label_lower or label_lower in NON_EXCHANGE_LABELS:
        return None

    # Direct match
    if label_lower in EXCHANGE_LABELS:
        return label.strip()

    # Fuzzy match — check if any known exchange name is contained
    for ex_name in EXCHANGE_LABELS:
        if ex_name in label_lower:
            return label.strip()

    # Check for common exchange-like patterns
    exchange_keywords = [
        "exchange", "binance", "coinbase", "kraken", "bitfinex", "huobi",
        "okx", "okex", "bybit", "bitmex", "gemini", "crypto.com", "ftx",
        "kucoin", "gate.io", "gateio", "bitstamp", "bittrex", "poloniex",
        "bitgo", "anchor", "cex.io", "bitflyer", "upbit", "zaif",
    ]
    for kw in exchange_keywords:
        if kw in label_lower:
            return label.strip()

    return None


def extract_addresses(tx: dict) -> list[str]:
    """Extract all unique blockchain addresses from a transaction's sub_transactions.

    Returns list of (normalized) addresses.
    """
    addresses = []
    txn = tx.get("transaction", {})
    subs = txn.get("sub_transactions") or []
    blockchain = tx.get("blockchain", "")

    for sub in subs:
        for io_field in ("inputs", "outputs"):
            for io in (sub.get(io_field) or []):
                addr = io.get("address", "")
                if addr:
                    # Normalize: lowercase for EVM chains, as-is for BTC-like
                    if blockchain in ("ethereum", "polygon", "plasma"):
                        addr = addr.lower()
                    if addr not in addresses:
                        addresses.append(addr)

    return addresses


def build_address_lookup(transactions: list[dict]) -> dict:
    """Build address-to-exchange lookup table from labeled transactions.

    For each transaction where from/to has an exchange label, map the
    blockchain addresses to that exchange. This creates a reverse index
    we can use to label future unknown transactions.

    Returns dict: {(blockchain, address): exchange_name}
    """
    lookup = {}  # (blockchain, address) -> exchange_name
    label_sources = Counter()  # exchange_name -> count of addresses

    for tx in transactions:
        blockchain = tx.get("blockchain", "")
        addresses = extract_addresses(tx)

        # For 'from' field
        from_label = classify_label(tx.get("from", ""))
        if from_label and addresses:
            for addr in addresses:
                key = (blockchain, addr)
                if key not in lookup:
                    lookup[key] = from_label
                    label_sources[from_label] += 1

        # For 'to' field
        to_label = classify_label(tx.get("to", ""))
        if to_label and addresses:
            for addr in addresses:
                key = (blockchain, addr)
                if key not in lookup:
                    lookup[key] = to_label
                    label_sources[to_label] += 1

    return lookup, label_sources


def load_external_datasets(datasets_dir: str) -> dict:
    """Load external exchange address datasets if available.

    Looks for EVEREST and Labelbase data in the datasets directory.
    Returns dict: {(blockchain, address): exchange_name}
    """
    external = {}

    if not os.path.isdir(datasets_dir):
        print(f"  No external datasets directory: {datasets_dir}")
        return external

    # EVEREST dataset
    everest_dir = os.path.join(datasets_dir, "everest-research")
    if os.path.isdir(everest_dir):
        loaded = load_everest_dataset(everest_dir)
        external.update(loaded)
        print(f"  EVEREST: {len(loaded)} addresses loaded")
    else:
        print(f"  EVEREST: dataset not found at {everest_dir}")

    # Labelbase dataset
    labelbase_dir = os.path.join(datasets_dir, "labels")
    if os.path.isdir(labelbase_dir):
        loaded = load_labelbase_dataset(labelbase_dir)
        external.update(loaded)
        print(f"  Labelbase: {len(loaded)} addresses loaded")
    else:
        print(f"  Labelbase: dataset not found at {labelbase_dir}")

    return external


def load_everest_dataset(everest_dir: str) -> dict:
    """Parse EVEREST dataset CSV/JSON files for exchange entity addresses.

    EVEREST format: entity data with addresses grouped by entity.
    We look for files matching patterns like entities.csv, addresses.csv, etc.
    """
    addresses = {}

    for root, dirs, files in os.walk(everest_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = fname.lower().split(".")[-1]

            if ext == "csv":
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        header = f.readline().strip().lower()
                        # Check if this looks like an addresses file
                        if any(kw in header for kw in ["address", "entity"]):
                            for line in f:
                                parts = line.strip().split(",")
                                if len(parts) >= 2:
                                    addr = parts[0].strip()
                                    entity = parts[1].strip()
                                    if addr and entity:
                                        # Determine blockchain from file path
                                        chain = guess_chain_from_path(fpath)
                                        if chain:
                                            key = (chain, addr.lower() if chain == "ethereum" else addr)
                                            addresses[key] = entity
                except Exception as e:
                    print(f"    Warning: error reading {fpath}: {e}")

            elif ext == "json":
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    addr = item.get("address", "")
                                    entity = item.get("name") or item.get("entity", "")
                                    chain = item.get("blockchain", "")
                                    if addr and entity:
                                        chain = chain or guess_chain_from_path(fpath)
                                        if chain:
                                            key = (chain, addr.lower() if chain == "ethereum" else addr)
                                            addresses[key] = entity
                except Exception as e:
                    print(f"    Warning: error reading {fpath}: {e}")

    return addresses


def load_labelbase_dataset(labelbase_dir: str) -> dict:
    """Parse Labelbase dataset for exchange address labels.

    Labelbase format: typically CSV/JSON with address, label, category fields.
    """
    addresses = {}

    for root, dirs, files in os.walk(labelbase_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = fname.lower().split(".")[-1]

            if ext == "csv":
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        header = f.readline().strip().lower()
                        for line in f:
                            parts = line.strip().split(",")
                            if len(parts) >= 2:
                                addr = parts[0].strip()
                                label = parts[1].strip()
                                category = parts[2].strip() if len(parts) >= 3 else ""
                                if addr and label:
                                    # Filter for exchange-related labels
                                    if any(kw in label.lower() for kw in
                                           ["exchange", "binance", "coinbase", "kraken",
                                            "binance", "huobi", "okx", "bybit", "ftx"]):
                                        chain = guess_chain_from_path(fpath)
                                        if chain:
                                            key = (chain, addr.lower() if chain == "ethereum" else addr)
                                            addresses[key] = label
                except Exception as e:
                    print(f"    Warning: error reading {fpath}: {e}")

            elif ext == "json":
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    addr = item.get("address", "")
                                    label = item.get("label") or item.get("name", "")
                                    category = item.get("category", "")
                                    if addr and label and "exchange" in str(category).lower():
                                        chain = guess_chain_from_path(fpath)
                                        if chain:
                                            key = (chain, addr.lower() if chain == "ethereum" else addr)
                                            addresses[key] = label
                except Exception as e:
                    print(f"    Warning: error reading {fpath}: {e}")

    return addresses


def guess_chain_from_path(fpath: str) -> str:
    """Guess blockchain from file path."""
    path_lower = fpath.lower()
    if "ethereum" in path_lower or "eth" in path_lower:
        return "ethereum"
    elif "bitcoin" in path_lower or "btc" in path_lower:
        return "bitcoin"
    elif "litecoin" in path_lower or "ltc" in path_lower:
        return "litecoin"
    elif "bitcoin_cash" in path_lower or "bch" in path_lower:
        return "bitcoin cash"
    elif "dogecoin" in path_lower or "doge" in path_lower:
        return "dogecoin"
    elif "tron" in path_lower or "trx" in path_lower:
        return "tron"
    elif "ripple" in path_lower or "xrp" in path_lower:
        return "ripple"
    elif "solana" in path_lower or "sol" in path_lower:
        return "solana"
    return ""


def enrich_transactions(transactions: list[dict], lookup: dict) -> list[dict]:
    """Enrich transactions with exchange_from and exchange_to fields.

    Strategy (per transaction):
    1. If from/to already has an exchange label, use it directly
    2. Otherwise, extract addresses from sub_transactions and check the lookup table
    3. For the 'from' side, prioritize input addresses; for 'to', prioritize output addresses
    """
    enriched = []
    stats = Counter()

    for tx in transactions:
        blockchain = tx.get("blockchain", "")

        # Determine exchange_from
        from_label = classify_label(tx.get("from", ""))
        if from_label:
            tx["exchange_from"] = from_label
            stats["from_whale_alert"] += 1
        else:
            # Try address lookup from inputs
            txn = tx.get("transaction", {})
            subs = txn.get("sub_transactions") or []
            found = None
            for sub in subs:
                for inp in (sub.get("inputs") or []):
                    addr = inp.get("address", "")
                    if addr:
                        key = (blockchain, addr.lower() if blockchain in ("ethereum", "polygon", "plasma") else addr)
                        if key in lookup:
                            found = lookup[key]
                            break
                if found:
                    break
            tx["exchange_from"] = found
            if found:
                stats["from_address_lookup"] += 1
            else:
                stats["from_unknown"] += 1

        # Determine exchange_to
        to_label = classify_label(tx.get("to", ""))
        if to_label:
            tx["exchange_to"] = to_label
            stats["to_whale_alert"] += 1
        else:
            # Try address lookup from outputs
            txn = tx.get("transaction", {})
            subs = txn.get("sub_transactions") or []
            found = None
            for sub in subs:
                for out in (sub.get("outputs") or []):
                    addr = out.get("address", "")
                    if addr:
                        key = (blockchain, addr.lower() if blockchain in ("ethereum", "polygon", "plasma") else addr)
                        if key in lookup:
                            found = lookup[key]
                            break
                if found:
                    break
            tx["exchange_to"] = found
            if found:
                stats["to_address_lookup"] += 1
            else:
                stats["to_unknown"] += 1

        # Track overall coverage
        if tx.get("exchange_from") or tx.get("exchange_to"):
            stats["either_labeled"] += 1
        if tx.get("exchange_from") and tx.get("exchange_to"):
            stats["both_labeled"] += 1

        enriched.append(tx)

    return enriched, stats


def print_stats(transactions: list[dict], stats: Counter, lookup: dict,
                label_sources: Counter, external_count: int):
    """Print comprehensive coverage statistics."""
    total = len(transactions)

    print("\n" + "=" * 70)
    print("ENRICHMENT PIPELINE — COVERAGE STATISTICS")
    print("=" * 70)

    print(f"\n  Total transactions: {total:,}")
    print(f"\n  Lookup table size: {len(lookup):,} unique (chain, address) pairs")
    print(f"    - From Whale Alert self-labeling: {len(lookup) - external_count:,}")
    print(f"    - From external datasets: {external_count:,}")

    print(f"\n  Exchange labels in lookup table (top 20):")
    for name, count in label_sources.most_common(20):
        print(f"    {name}: {count:,} addresses")

    print(f"\n  FROM coverage:")
    print(f"    From Whale Alert label:     {stats['from_whale_alert']:>6,} ({100*stats['from_whale_alert']/total:.1f}%)")
    print(f"    From address lookup:        {stats['from_address_lookup']:>6,} ({100*stats['from_address_lookup']/total:.1f}%)")
    print(f"    Unknown:                    {stats['from_unknown']:>6,} ({100*stats['from_unknown']/total:.1f}%)")
    from_total = stats['from_whale_alert'] + stats['from_address_lookup']
    print(f"    Total labeled:              {from_total:>6,} ({100*from_total/total:.1f}%)")

    print(f"\n  TO coverage:")
    print(f"    From Whale Alert label:     {stats['to_whale_alert']:>6,} ({100*stats['to_whale_alert']/total:.1f}%)")
    print(f"    From address lookup:        {stats['to_address_lookup']:>6,} ({100*stats['to_address_lookup']/total:.1f}%)")
    print(f"    Unknown:                    {stats['to_unknown']:>6,} ({100*stats['to_unknown']/total:.1f}%)")
    to_total = stats['to_whale_alert'] + stats['to_address_lookup']
    print(f"    Total labeled:              {to_total:>6,} ({100*to_total/total:.1f}%)")

    print(f"\n  TRANSACTION coverage:")
    print(f"    Both sides labeled:         {stats['both_labeled']:>6,} ({100*stats['both_labeled']/total:.1f}%)")
    print(f"    Either side labeled:        {stats['either_labeled']:>6,} ({100*stats['either_labeled']/total:.1f}%)")
    print(f"    Neither side labeled:       {total - stats['either_labeled']:>6,} ({100*(total - stats['either_labeled'])/total:.1f}%)")

    # Per-chain breakdown
    print(f"\n  Per-chain coverage:")
    chain_stats = defaultdict(lambda: {"total": 0, "from": 0, "to": 0, "both": 0})
    for tx in transactions:
        chain = tx.get("blockchain", "unknown")
        chain_stats[chain]["total"] += 1
        if tx.get("exchange_from"):
            chain_stats[chain]["from"] += 1
        if tx.get("exchange_to"):
            chain_stats[chain]["to"] += 1
        if tx.get("exchange_from") and tx.get("exchange_to"):
            chain_stats[chain]["both"] += 1

    print(f"    {'Chain':<18} {'Total':>7} {'From%':>7} {'To%':>7} {'Both%':>7}")
    print(f"    {'-'*18} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for chain in sorted(chain_stats.keys(), key=lambda c: -chain_stats[c]["total"]):
        s = chain_stats[chain]
        t = s["total"]
        print(f"    {chain:<18} {t:>7,} {100*s['from']/t:>6.1f}% {100*s['to']/t:>6.1f}% {100*s['both']/t:>6.1f}%")

    print("\n" + "=" * 70)

    # Show top exchange pairs
    pair_counter = Counter()
    for tx in transactions:
        ef = tx.get("exchange_from") or "unknown"
        et = tx.get("exchange_to") or "unknown"
        if ef != "unknown" or et != "unknown":
            pair_counter[(ef, et)] += 1

    print("\n  Top exchange-to-exchange flows:")
    for (ef, et), count in pair_counter.most_common(15):
        print(f"    {ef:<30} → {et:<30} ({count:,} txns)")


def main():
    t0 = time.time()

    print("=" * 70)
    print("WHALE ALPHA — Exchange Address Enrichment Pipeline (Phase 1)")
    print("=" * 70)

    # Step 1: Load whale archive
    print(f"\n[1/4] Loading whale archive from {ARCHIVE_PATH}...")
    if not os.path.exists(ARCHIVE_PATH):
        print(f"ERROR: Archive not found at {ARCHIVE_PATH}")
        sys.exit(1)

    with gzip.open(ARCHIVE_PATH, "rt", encoding="utf-8") as f:
        transactions = json.load(f)
    print(f"  Loaded {len(transactions):,} transactions")

    # Step 2: Build address-to-exchange lookup table
    print(f"\n[2/4] Building address-to-exchange lookup table...")
    lookup, label_sources = build_address_lookup(transactions)
    print(f"  Built lookup with {len(lookup):,} unique (chain, address) pairs")
    print(f"  Exchange labels found: {len(label_sources)}")

    # Step 2b: Load external datasets
    print(f"\n[2b/4] Loading external datasets...")
    external = load_external_datasets(DATASETS_DIR)
    external_count = len(external)
    if external:
        # Merge: external data supplements but doesn't override self-labeled data
        new_entries = 0
        for key, label in external.items():
            if key not in lookup:
                lookup[key] = label
                new_entries += 1
        print(f"  Merged {new_entries:,} new entries from external datasets")
        for label, _ in Counter(external.values()).most_common(10):
            print(f"    {label}")

    # Save lookup table
    print(f"\n  Saving lookup table to {LOOKUP_PATH}...")
    os.makedirs(os.path.dirname(LOOKUP_PATH), exist_ok=True)
    with gzip.open(LOOKUP_PATH, "wt", encoding="utf-8") as f:
        # Convert tuple keys to strings for JSON serialization
        serializable = {f"{chain}|{addr}": label for (chain, addr), label in lookup.items()}
        json.dump(serializable, f)
    print(f"  Saved {len(lookup):,} entries")

    # Step 3: Enrich transactions
    print(f"\n[3/4] Enriching transactions...")
    enriched, stats = enrich_transactions(transactions, lookup)

    # Step 4: Output enriched data
    print(f"\n[4/4] Writing enriched archive to {OUTPUT_PATH}...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with gzip.open(OUTPUT_PATH, "wt", encoding="utf-8") as f:
        json.dump(enriched, f)

    elapsed = time.time() - t0
    output_size = os.path.getsize(OUTPUT_PATH)
    print(f"  Written {len(enriched):,} enriched transactions ({output_size / 1024 / 1024:.1f} MB)")
    print(f"  Pipeline completed in {elapsed:.1f}s")

    # Print stats
    print_stats(enriched, stats, lookup, label_sources, external_count)

    print(f"\nDone! Enriched data saved to: {OUTPUT_PATH}")
    print(f"Lookup table saved to: {LOOKUP_PATH}")


if __name__ == "__main__":
    main()
