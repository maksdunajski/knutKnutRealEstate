#!/usr/bin/env python3
"""
plot.py

Leser data/houses_cleaned.jsonl og lager en scatter-plot mellom to valgte features.
Bruk:
    python plot.py --x size --y price         # viser interaktiv plot i standard viewer (browser/jupyter)
    python plot.py --list                     # viser tilgjengelige features og hvilke som er numeriske

Skriptet prøver å konvertere valgte features til tall. Rader som ikke kan konverteres blir hoppet over.
"""

import argparse
import json
import os
from typing import List, Dict, Any, Tuple

import plotly.express as px


DATA_PATH = os.path.join(os.path.dirname(__file__), ".." , "data", "houses_clean.jsonl")


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Finner ikke filen: {path}")
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                data.append(obj)
            except json.JSONDecodeError:
                # Hopp over dårlige linjer
                continue
    return data


def infer_features(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Gjør en enkel inferering av hvilke keys som finnes og om de ser numeriske ut.
    Returnerer dict: {feature: {"numeric": bool, "sample": sample_value}}
    """
    features = {}
    for row in data:
        for k, v in row.items():
            if k not in features:
                features[k] = {"numeric": True, "sample": None}
            if features[k]["sample"] is None and v is not None:
                features[k]["sample"] = v
            # prøv å konvertere til float for å sjekke om numerisk
            if v is None:
                continue
            try:
                float(v)
            except Exception:
                features[k]["numeric"] = False
    return features


def collect_numeric(data: List[Dict[str, Any]], key: str) -> List[float]:
    vals = []
    for row in data:
        if key not in row:
            continue
        v = row[key]
        if v is None:
            continue
        # noen felter kan være tekst som '4 rooms' eller liknende -> prøv ekstra rensing
        if isinstance(v, str):
            # fjern ord, behold kun sifre, komma og punktum
            cleaned = v.replace(",", ".")
            # fjern ikke-numeriske tegn i starten/slutt
            try:
                # forsøk direkte float
                num = float(cleaned)
                vals.append(num)
                continue
            except Exception:
                # forsøk ekstra: fjern ikke-sifre
                import re

                m = re.search(r"[-+]?[0-9]*\.?[0-9]+", cleaned)
                if m:
                    try:
                        num = float(m.group(0))
                        vals.append(num)
                        continue
                    except Exception:
                        continue
                else:
                    continue
        else:
            try:
                num = float(v)
                vals.append(num)
            except Exception:
                continue
    return vals


def prepare_xy(data: List[Dict[str, Any]], x_key: str, y_key: str) -> Tuple[List[float], List[float]]:
    x_vals = []
    y_vals = []
    for row in data:
        if x_key not in row or y_key not in row:
            continue
        vx = row[x_key]
        vy = row[y_key]
        if vx is None or vy is None:
            continue
        # try convert to float using same logic as collect_numeric
        def to_num(v):
            if isinstance(v, str):
                v2 = v.replace(",", ".")
                try:
                    return float(v2)
                except Exception:
                    import re

                    m = re.search(r"[-+]?[0-9]*\.?[0-9]+", v2)
                    if m:
                        return float(m.group(0))
                    return None
            else:
                try:
                    return float(v)
                except Exception:
                    return None

        nx = to_num(vx)
        ny = to_num(vy)
        if nx is None or ny is None:
            continue
        x_vals.append(nx)
        y_vals.append(ny)
    return x_vals, y_vals


def plot_xy(x: List[float], y: List[float], x_label: str, y_label: str) -> None:
    """Create an interactive scatter using plotly.express.

    This function only displays the interactive figure via fig.show(). It does not save files.
    """
    if len(x) == 0 or len(y) == 0:
        raise ValueError("Ingen datapunkter å plotte etter filtrering.")

    # Build interactive figure
    fig = px.scatter(x=x, y=y, labels={"x": x_label, "y": y_label}, title=f"Scatter: {y_label} vs {x_label} (n={len(x)})")
    fig.update_traces(marker=dict(opacity=0.6, size=8))
    fig.update_layout(template="simple_white")

    # Only show the interactive figure (no saving)
    try:
        fig.show()
    except Exception:
        # In headless or non-supported env, .show() may fail silently
        pass


def main():
    p = argparse.ArgumentParser(description="Plot two features from houses_cleaned.jsonl")
    p.add_argument("--x", help="feature for x-aksen", default="price")
    p.add_argument("--y", help="feature for y-aksen", default="price")
    p.add_argument("--list", help="list available features and indicate numeric ones", action="store_true")
    p.add_argument("--limit", help="limit number of rows to read (for raskere kjøring)", type=int, default=0)
    args = p.parse_args()

    try:
        data = read_jsonl(DATA_PATH)
    except FileNotFoundError as e:
        print(str(e))
        return

    if args.limit and args.limit > 0:
        data = data[: args.limit]

    features = infer_features(data)

    if args.list:
        print("Tilgjengelige features (eksempelverdi, numerisk?):")
        for k in sorted(features.keys()):
            sample = features[k]["sample"]
            numeric = features[k]["numeric"]
            print(f"  {k} -> sample={sample!r}, numeric={numeric}")
        return

    x_key = args.x
    y_key = args.y

    if x_key not in features:
        print(f"Feature '{x_key}' finnes ikke i data. Kjør med --list for å se tilgjengelige features.")
        return
    if y_key not in features:
        print(f"Feature '{y_key}' finnes ikke i data. Kjør med --list for å se tilgjengelige features.")
        return

    x_vals, y_vals = prepare_xy(data, x_key, y_key)
    print(f"Antall punkter etter filtrering: {len(x_vals)}")
    if len(x_vals) == 0:
        print("Ingen gyldige datapunkter etter konvertering til tall. Sjekk at valgte features er numeriske eller kan tolkes som tall.")
        return

    try:
        plot_xy(x_vals, y_vals, x_key, y_key)
    except Exception as e:
        print(f"Feil under plotting: {e}")


if __name__ == "__main__":
    main()
