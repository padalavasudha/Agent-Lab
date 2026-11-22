"""Build results/comparison.md from results/baseline.json and results/defended.json."""
import json
from collections import defaultdict, Counter

def load(label):
    return json.load(open(f"results/{label}.json"))

def by_category(d):
    c = defaultdict(lambda: [0, 0])
    for r in d["records"]:
        c[r["category"]][0] += r["success"]; c[r["category"]][1] += 1
    return c

def main():
    b, d = load("baseline"), load("defended")
    cb, cd = by_category(b), by_category(d)
    lines = ["# Baseline vs defended", "",
             f"Model: `{b['model']}` | Runs per case: {b['runs']} | Same attack suite for both", "",
             "| Category | Baseline | Defended |", "|---|---|---|"]
    for cat in cb:
        if cat == "Utility":
            continue
        (sb, nb), (sd, nd) = cb[cat], cd.get(cat, [0, 0])
        lines.append(f"| {cat} | {sb / nb:.0%} ({sb}/{nb}) | {sd / nd:.0%} ({sd}/{nd}) |")
    ab = [sum(v[0] for k, v in cb.items() if k != "Utility"), sum(v[1] for k, v in cb.items() if k != "Utility")]
    ad = [sum(v[0] for k, v in cd.items() if k != "Utility"), sum(v[1] for k, v in cd.items() if k != "Utility")]
    lines.append(f"| **All attacks (attack success rate, lower is better)** | **{ab[0] / ab[1]:.0%}** ({ab[0]}/{ab[1]}) | **{ad[0] / ad[1]:.0%}** ({ad[0]}/{ad[1]}) |")
    ub, ud = cb["Utility"], cd["Utility"]
    lines.append(f"| **Utility (normal requests succeed, higher is better)** | {ub[0] / ub[1]:.0%} ({ub[0]}/{ub[1]}) | {ud[0] / ud[1]:.0%} ({ud[0]}/{ud[1]}) |")

    # per-attack baseline effectiveness (which attacks actually worked before defenses)
    never = sorted({r["id"] for r in b["records"] if r["category"] != "Utility"}
                   - {r["id"] for r in b["records"] if r["success"]})
    lines += ["", f"Attacks that never succeeded even at baseline (inconclusive for this model): {', '.join(never) or 'none'}"]

    # defended audit signals
    queued = Counter(r["id"] for r in d["records"] if r["category"] != "Utility" for _ in range(r.get("queued_for_approval", 0)))
    decisions = Counter(c.get("decision") for r in d["records"] for c in r["calls"])
    sanitized = Counter(r["id"] for r in d["records"] for c in r["calls"] if c.get("decision") == "sanitized")
    lines += ["", "## Defended agent: what the harness did", "",
              "| Harness decision | Count |", "|---|---|"]
    for k in ("allow", "deny", "pending", "sanitized", "error"):
        lines.append(f"| {k} | {decisions.get(k, 0)} |")
    lines += ["", f"Refund requests queued for human approval during attacks: {sum(queued.values())} "
              f"({', '.join(f'{k} x{v}' for k, v in sorted(queued.items())) or 'none'})",
              f"Tool calls where the model supplied arguments the tool does not accept (dropped and logged): "
              f"{sum(sanitized.values())} ({', '.join(f'{k} x{v}' for k, v in sorted(sanitized.items())) or 'none'})"]
    open("results/comparison.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()