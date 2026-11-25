#!/usr/bin/env python3
"""LOINC lookup helper for curated/scale_identifiers.csv (HUMAN INPUT aid).

Reads the official LOINC download (data/raw/loinc/LoincTable/Loinc.csv,
see https://loinc.org/downloads) and prints candidate LOINC codes for each
scale in curated/scale_identifiers.csv. Writes deliverables/
loinc_suggestions.csv — a REVIEW FILE ONLY.

This script NEVER writes to curated/scale_identifiers.csv. Every candidate
is an unreviewed suggestion; a human must confirm each code against the
LOINC term's component/property/system before copying it into the register
(and set review_status/reviewed_by there). Do not infer codes from memory.

Usage:
    python3 scripts/lookup_loinc.py
    python3 scripts/lookup_loinc.py --loinc path/to/Loinc.csv --top 5
"""
import argparse
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "curated" / "scale_identifiers.csv"
DEFAULT_LOINC = REPO / "data" / "raw" / "loinc" / "LoincTable" / "Loinc.csv"
OUT = REPO / "deliverables" / "loinc_suggestions.csv"

# Instrument-generic words that carry no identity when matching scale names
# to LOINC terms. Clinical modifiers (Modified, Pediatric, ...) are kept.
STOPWORDS = {
    "scale", "scales", "test", "tests", "index", "indexes", "score", "scores",
    "measure", "measures", "assessment", "questionnaire", "inventory",
    "of", "in", "for", "and", "the", "a", "an", "on", "to", "with",
}
# Small words skipped when building an acronym from a scale name.
ACRONYM_SKIP = {"of", "in", "on", "and", "the", "for", "to", "a", "an", "at"}
# Short function words dropped from overlap tokens beyond STOPWORDS.
ACRONYM_NAME_CAP = 6  # names this short AND uppercase are treated as acronyms
ACRONYM_MIN_LEN = 3    # 2-letter acronyms ("CS") collide with lab tests

# Digits written as words in one corpus, digits in the other ("9-Hole Pegboard"
# vs "Nine Hole Peg Test"). Normalized on BOTH sides before tokenizing.
NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
                "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
                "ten": "10"}

# Obvious non-instrument matches demoted one tier (still visible, ranked
# below real candidates): molecular-genetics terms matched via acronyms
# like BBS/FGA, and deprecated/retired terms.
GENETICS_RE = re.compile(r"\bgene\b|\bmutation|\bdna\b|\brna\b|\ballele", re.I)
DEPRECATED_RE = re.compile(r"^(deprecated|retired)\b", re.I)


def norm(text):
    """Lowercase, punctuation → spaces, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()


def _stem(token):
    """Light stemmer for overlap only: walking→walk, tests→test."""
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(text):
    out = set()
    for t in norm(text).split():
        if not t or t in STOPWORDS:
            continue
        t = NUMBER_WORDS.get(t, t)
        out.add(_stem(t))
    return out


def acronym(name):
    """NIHSS from 'National Institutes of Health Stroke Scale'; TUG from
    'Timed Up and Go'. Returns '' when no useful acronym exists."""
    parts = [p for p in name.split() if p.strip()]
    letters = [p[0] for p in parts if p.lower() not in ACRONYM_SKIP and p[0].isalpha()]
    acr = "".join(letters)
    if 2 <= len(acr) <= 8 and acr.isalpha():
        return acr.upper()
    return ""


def load_loinc(path):
    """Load LOINC terms with pre-normalized search fields."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            fields = {
                "long_common_name": r.get("LONG_COMMON_NAME", ""),
                "shortname": r.get("SHORTNAME", ""),
                "consumer_name": r.get("CONSUMER_NAME", ""),
                "component": r.get("COMPONENT", ""),
                "relatednames2": r.get("RELATEDNAMES2", ""),
                "system": r.get("SYSTEM", ""),
            }
            desc = r.get("DefinitionDescription", "") or ""
            status = r.get("STATUS", "") or ""
            rows.append({
                "loinc_num": r.get("LOINC_NUM", ""),
                "status": status,
                "class": r.get("CLASS", ""),
                **fields,
                "_search": {k: norm(v) for k, v in fields.items()},
                "_rawtok": {k: set(norm(v).split()) - STOPWORDS
                            for k, v in fields.items()},   # acronym literal match
                "_overlap": {k: tokens(v) for k, v in fields.items()},
                "_defn_tokens": tokens(desc),          # overlap-only field
                "_status_ok": status.upper() == "ACTIVE" and not DEPRECATED_RE.match(
                    fields["long_common_name"] or ""),
                "_genetics": bool(GENETICS_RE.search(
                    fields["component"] + " " + fields["long_common_name"])),
            })
    return rows


def _demote(row, tier, score, reason):
    """Push junk classes below real candidates but keep them visible."""
    if row["_genetics"]:
        tier, score = tier + 1, score * 0.5
        reason = reason + "+genetics"
    if not row["_status_ok"]:
        tier, score = tier + 1, score * 0.5
        reason = reason + "+not_active"
    return tier, score, reason


def build_generic_tokens(rows, frac=0.02):
    """Tokens appearing in >frac of terms are too generic to evidence a
    match ('test', 'score', 'walk', 'patient'…). Removed from overlap on
    BOTH sides; acronym/exact/contains tiers are unaffected."""
    df = {}
    n = len(rows)
    for row in rows:
        for ftok in list(row["_overlap"].values()) + [row["_defn_tokens"]]:
            for t in ftok:
                df[t] = df.get(t, 0) + 1
    limit = max(20, int(n * frac))
    return {t for t, c in df.items() if c > limit}


def candidates_for(name, loinc_rows, top, generic=None):
    """Best candidates for one scale: exact > acronym > contains > overlap."""
    generic = generic or set()
    n_name = norm(name)
    t_name = tokens(name) - generic
    acr = acronym(name)
    # Names that already ARE an acronym (DASH, KOOS, HOOS): use as-is.
    if len(name) <= 8 and name.isupper():
        acr = name
    if acr and len(acr) < ACRONYM_MIN_LEN:
        acr = ""
    best = {}  # loinc_num -> (tier, -score, reason, row)
    for row in loinc_rows:
        if row["_genetics"]:
            continue  # gene-symbol acronym collisions can never be right here
        tier, score, reason = 3, 0.0, None
        for fld, nval in row["_search"].items():
            if not nval:
                continue
            if nval == n_name:
                tier, score, reason = 0, 1.0, f"exact:{fld}"
                break
            if acr and re.search(
                    r"(?<![a-z0-9])" + re.escape(acr.lower()) + r"(?![a-z0-9])",
                    " " + nval + " " + row["_search"]["relatednames2"] + " "):
                if tier > 1:
                    tier, score, reason = 1, 0.9, f"acronym:{acr}"
        if reason is None:
            # Acronym as a literal (UNstemmed) token in shortname/aliases,
            # so "pedis" cannot masquerade as "pedi".
            if acr and any(acr.lower() in row["_rawtok"][f]
                           for f in ("shortname", "relatednames2")):
                tier, score, reason = 1, 0.85, f"acronym:{acr}"
        if reason is None:
            for fld, nval in row["_search"].items():
                if not n_name or len(n_name) < 6:
                    continue
                # nval-in-name only for distinctive phrases, else single
                # generic component words ("assessment") match everything.
                distinctive = nval.count(" ") >= 2 or len(nval) >= 15
                if n_name in nval:
                    tier, score, reason = 2, 0.7, f"contains:{fld}"
                elif distinctive and nval in n_name:
                    tier, score, reason = 2, 0.65, f"contains_rev:{fld}"
        if reason is None and t_name:
            for fld, ftok in row["_overlap"].items():
                overlap = t_name & (ftok - generic)
                if len(overlap) >= 2:
                    cov = len(overlap) / len(t_name)
                    if cov >= 0.6 and cov > score:
                        tier, score, reason = 3, cov, f"overlap:{fld}({len(overlap)}/{len(t_name)})"
            # Definition text: overlap-only, half weight (catches scales
            # only mentioned in prose, e.g. Lawton IADL panels).
            if row["_defn_tokens"]:
                overlap = t_name & (row["_defn_tokens"] - generic)
                if len(overlap) >= 2:
                    cov = 0.5 * len(overlap) / len(t_name)
                    if cov > score:
                        tier, score, reason = 3, cov, f"overlap:definition({len(overlap)}/{len(t_name)})"
        if reason is not None:
            tier, score, reason = _demote(row, tier, score, reason)
            key = row["loinc_num"]
            cand = (tier, -score, reason, row)  # sort: tier asc, -score asc
            if key not in best or cand[:2] < best[key][:2]:
                best[key] = cand
    ranked = sorted(best.values(), key=lambda c: (c[0], c[1]))[:top]
    return ranked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loinc", type=Path, default=DEFAULT_LOINC,
                    help="Path to LOINC.csv from the official download")
    ap.add_argument("--top", type=int, default=5,
                    help="Candidates per scale (default 5)")
    ap.add_argument("--out", type=Path, default=OUT,
                    help="Suggestions CSV (review file, never the register)")
    args = ap.parse_args()

    if not args.loinc.exists():
        raise SystemExit(
            f"LOINC table not found: {args.loinc}\n"
            "Download https://loinc.org/downloads (free account), unzip to "
            "data/raw/loinc/, or pass --loinc.")
    if not REGISTER.exists():
        raise SystemExit(f"Register not found: {REGISTER}")

    loinc_rows = load_loinc(args.loinc)
    generic = build_generic_tokens(loinc_rows)
    with open(REGISTER, newline="", encoding="utf-8") as f:
        scales = list(csv.DictReader(f))
    print(f"LOINC terms: {len(loinc_rows):,}  scales: {len(scales)}  "
          f"generic overlap tokens dropped: {len(generic)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_fields = ["scale_id", "scale_name", "candidate_rank", "match_reason",
                  "loinc_num", "long_common_name", "shortname", "class",
                  "status", "review_status"]
    n_with = n_top1_exactish = 0
    zero = []
    summary = []
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, lineterminator="\n")
        w.writeheader()
        for s in sorted(scales, key=lambda x: x["scale_id"]):
            cands = candidates_for(s["name"], loinc_rows, args.top, generic)
            if cands:
                n_with += 1
            else:
                zero.append((s["scale_id"], s["name"]))
            if cands and cands[0][0] <= 1:
                n_top1_exactish += 1
            for i, (tier, neg, reason, row) in enumerate(cands, 1):
                w.writerow({
                    "scale_id": s["scale_id"], "scale_name": s["name"],
                    "candidate_rank": i, "match_reason": reason,
                    "loinc_num": row["loinc_num"],
                    "long_common_name": row["long_common_name"],
                    "shortname": row["shortname"], "class": row["class"],
                    "status": row["status"],
                    "review_status": "suggestion_unreviewed",
                })
            top1 = (cands[0][3] if cands else None)
            summary.append((s["scale_id"], s["name"], cands[0][2] if cands else "",
                            top1["loinc_num"] if top1 else "-",
                            top1["long_common_name"][:60] if top1 else "NO CANDIDATES",
                            cands[0][0] if cands else 9))

    print(f"scales with >=1 candidate: {n_with}/{len(scales)} "
          f"(top-1 exact/acronym: {n_top1_exactish})")
    print(f"writes: {args.out.relative_to(REPO)}  "
          f"(review file — the register is untouched)\n")
    print(f"{'id':8} {'tier':4} {'reason':18} {'loinc':10} candidate")
    for sid, name, reason, num, ln, tier in summary:
        print(f"{sid:8} {tier:<4} {reason[:18]:18} {num:10} {ln}")
    if zero:
        print("\nNO candidates (search LOINC.org manually):")
        for sid, name in zero:
            print(f"  {sid}  {name}")
    # Anchor cross-check: the NIHSS panel we already know from the ontology.
    nih = [num for _, _, _, num, _, _ in summary if num == "70182-1"]
    print("\nCross-check ASM-110: 70182-1 (NIH stroke scale panel) "
          + ("found as top-1 ✓" if nih else "NOT top-1 — inspect manually"))


if __name__ == "__main__":
    main()
