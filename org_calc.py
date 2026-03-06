from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import pandas as pd

@dataclass
class StaffNode:
    staff_id: str
    staff_type: str  # 'staff' or 'baito'
    parent_id: str | None

def build_staff_nodes(staff_df: pd.DataFrame) -> Dict[str, StaffNode]:
    nodes: Dict[str, StaffNode] = {}
    for _, r in staff_df.iterrows():
        nodes[str(r["staff_id"])] = StaffNode(
            staff_id=str(r["staff_id"]),
            staff_type=str(r["type"]),
            parent_id=(None if pd.isna(r.get("parent_id")) else str(r.get("parent_id"))),
        )
    return nodes

def build_children_map(nodes: Dict[str, StaffNode]) -> Dict[str, List[str]]:
    children: Dict[str, List[str]] = {sid: [] for sid in nodes.keys()}
    for sid, n in nodes.items():
        if n.parent_id and n.parent_id in children:
            children[n.parent_id].append(sid)
    return children

def detect_cycle(nodes: Dict[str, StaffNode]) -> List[List[str]]:
    # simple DFS cycle detection
    cycles = []
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def dfs(u: str, stack: List[str]):
        if u in visiting:
            # cycle found
            if u in stack:
                idx = stack.index(u)
                cycles.append(stack[idx:] + [u])
            return
        if u in visited:
            return
        visiting.add(u)
        stack.append(u)
        for v in children_map.get(u, []):
            dfs(v, stack)
        stack.pop()
        visiting.remove(u)
        visited.add(u)

    children_map = build_children_map(nodes)
    for sid in nodes.keys():
        dfs(sid, [])
    return cycles

def descendants(children_map: Dict[str, List[str]], root: str) -> Set[str]:
    out: Set[str] = set()
    stack = [root]
    while stack:
        u = stack.pop()
        for v in children_map.get(u, []):
            if v not in out:
                out.add(v)
                stack.append(v)
    return out

def compute_payroll(
    year_month: str,
    staff_df: pd.DataFrame,
    gross_df: pd.DataFrame,
    drink_df: pd.DataFrame,
    hours_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, dict], List[str]]:
    """
    Returns:
      - payroll_df: staff+baito monthly payroll table
      - breakdown_by_staff: dict staff_id -> breakdown json
      - errors: list of blocking errors (cycle, missing rate, etc.)
    """
    nodes = build_staff_nodes(staff_df)
    children_map = build_children_map(nodes)

    errors: List[str] = []
    cyc = detect_cycle(nodes)
    if cyc:
        errors.append(f"組織ツリーに循環参照があります: {cyc[:3]}{'...' if len(cyc)>3 else ''}")

    # --- maps ---
    gross_map = {str(r["staff_id"]): float(r["gross_reward"]) for _, r in gross_df.iterrows()}
    org_sales_map = {str(r["staff_id"]): float(r["org_sales"]) for _, r in gross_df.iterrows()}
    rate_map = {str(r["staff_id"]): float(r["rate"]) for _, r in gross_df.iterrows()}

    drink_map = {str(r["staff_id"]): float(r["drinkback_total"]) for _, r in drink_df.iterrows()} if drink_df is not None else {}
    hours_map = {str(r["staff_id"]): float(r["total_hours"]) for _, r in hours_df.iterrows()} if hours_df is not None else {}

    # Missing gross for staff members means rate did not apply or no org_sales
    for sid, n in nodes.items():
        if n.staff_type == "staff":
            if sid not in gross_map:
                # if they have no sales at all, gross is treated as 0 (ok)
                gross_map[sid] = 0.0
                org_sales_map[sid] = 0.0
                rate_map[sid] = 0.0

    # --- compute baito pay first ---
    # Need hourly_wage / transport in staff_df
    staff_df2 = staff_df.copy()
    staff_df2["hourly_wage"] = pd.to_numeric(staff_df2.get("hourly_wage", 0), errors="coerce").fillna(0)
    staff_df2["transportation_allowance"] = pd.to_numeric(staff_df2.get("transportation_allowance", 0), errors="coerce").fillna(0)

    baito_pay_map: Dict[str, float] = {}
    for _, r in staff_df2.iterrows():
        sid = str(r["staff_id"])
        if str(r["type"]) != "baito":
            continue
        hours = float(hours_map.get(sid, 0.0))
        drink = float(drink_map.get(sid, 0.0))
        wage = float(r["hourly_wage"])
        trans = float(r["transportation_allowance"])
        baito_pay_map[sid] = wage * hours + trans + drink

    # --- staff payroll with deductions ---
    breakdown_by_staff: Dict[str, dict] = {}

    def direct_child_staff(sid: str) -> List[str]:
        return [c for c in children_map.get(sid, []) if nodes[c].staff_type == "staff"]

    def descendant_baito(sid: str) -> Set[str]:
        desc = descendants(children_map, sid)
        return {d for d in desc if nodes[d].staff_type == "baito"}

    rows = []
    for _, r in staff_df2.iterrows():
        sid = str(r["staff_id"])
        name = str(r.get("name", sid))
        stype = str(r["type"])

        drink = float(drink_map.get(sid, 0.0))

        if stype == "baito":
            hours = float(hours_map.get(sid, 0.0))
            wage = float(r["hourly_wage"])
            trans = float(r["transportation_allowance"])
            total = baito_pay_map.get(sid, wage * hours + trans + drink)

            breakdown_by_staff[sid] = {
                "target_month": year_month,
                "type": "baito",
                "hourly_wage": wage,
                "total_hours": hours,
                "transportation_allowance": trans,
                "drinkback_total": drink,
                "baito_pay": total,
            }

            rows.append({
                "staff_id": sid,
                "name": name,
                "type": "baito",
                "personal_sales": 0,
                "org_sales": 0,
                "rate": 0,
                "gross_reward": 0,
                "child_staff_deduction": 0,
                "child_baito_deduction": 0,
                "staff_f_pay": 0,
                "hours": hours,
                "hourly_wage": wage,
                "transportation_allowance": trans,
                "drinkback_total": drink,
                "total_pay": int(round(total)),
            })
            continue

        # staff
        gross = float(gross_map.get(sid, 0.0))
        org_sales = float(org_sales_map.get(sid, 0.0))
        rate = float(rate_map.get(sid, 0.0))

        # direct child staff deduction: sum gross_reward(child)
        child_staff = direct_child_staff(sid)
        child_staff_ded = sum(float(gross_map.get(c, 0.0)) for c in child_staff)

        # descendant baito deduction: sum baito_pay(descendant)
        baito_desc = descendant_baito(sid)
        child_baito_ded = sum(float(baito_pay_map.get(b, 0.0)) for b in baito_desc)

        staff_f_pay = max(0.0, gross - child_staff_ded - child_baito_ded)
        total = staff_f_pay + drink

        breakdown_by_staff[sid] = {
            "target_month": year_month,
            "type": "staff",
            "org_sales": org_sales,
            "rate": rate,
            "gross_reward": gross,
            "child_staff_ids": child_staff,
            "child_staff_deduction": child_staff_ded,
            "descendant_baito_ids": sorted(list(baito_desc)),
            "child_baito_deduction": child_baito_ded,
            "staff_f_pay": staff_f_pay,
            "drinkback_total": drink,
            "total_pay": total,
        }

        rows.append({
            "staff_id": sid,
            "name": name,
            "type": "staff",
            "personal_sales": 0,
            "org_sales": org_sales,
            "rate": rate,
            "gross_reward": gross,
            "child_staff_deduction": child_staff_ded,
            "child_baito_deduction": child_baito_ded,
            "staff_f_pay": staff_f_pay,
            "hours": 0,
            "hourly_wage": 0,
            "transportation_allowance": 0,
            "drinkback_total": drink,
            "total_pay": int(round(total)),
        })

    payroll_df = pd.DataFrame(rows)
    payroll_df = payroll_df.sort_values(["type", "staff_id"]).reset_index(drop=True)
    return payroll_df, breakdown_by_staff, errors
