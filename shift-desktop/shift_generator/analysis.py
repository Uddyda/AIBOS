import json
import subprocess
import os
from copy import deepcopy
from itertools import product

CONFIG_PATH = "./new.json"
TMP_CONFIG_PATH = "./tmp_test.json"
OUTPUT_DIR = "fit_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# work_constraints候補値
min_monthly_workdays_list = [0, 3, 5, 7]
max_consecutive_days_list = [5, 6, 7, 8]

def run_shift_calc(config):
    with open(TMP_CONFIG_PATH, "w", encoding="utf-8") as fw:
        json.dump(config, fw, ensure_ascii=False, indent=2)
    cmd = ["python", "shift_generator.py", OUTPUT_DIR]
    env = os.environ.copy()
    env["SHIFT_CONFIG_PATH"] = TMP_CONFIG_PATH
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    stdout = result.stdout
    dummy_found = ("ダミー" in stdout or "dummy" in stdout)
    unsat = ("解が見つかりませんでした" in stdout or result.returncode != 0)
    status = "UNSAT" if unsat else ("DUMMY" if dummy_found else "FEASIBLE")
    return status

def calc_min_required_staff(config):
    name2role = config["positions"]
    role_need = {}
    for work, pa in config["priority_assignments"].items():
        req = config["daily_requirements"][work]["normal_min"]
        assigned = []
        for l in ["primary", "secondary"]:
            assigned += pa.get(l, [])
        assigned_roles = set(name2role[n] for n in assigned if n in name2role and name2role[n] != "dummy")
        for role in assigned_roles:
            role_need[role] = max(role_need.get(role, 0), req)
    return role_need

def find_lacking_roles(config, role_need):
    name2role = config["positions"]
    role2names = {}
    for n, r in name2role.items():
        role2names.setdefault(r, []).append(n)
    lacking = []
    for role, req in role_need.items():
        n_staff = len(role2names.get(role, []))
        if n_staff < req:
            lacking.append((role, req, n_staff))
    return lacking

# --- 本体 ---
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    base_config = json.load(f)

name2role = base_config["positions"]
role_need = calc_min_required_staff(base_config)

print("\n==== work_constraintsだけでフィッティング開始 ====")
results = []
first_feasible = None

for wc_min_days in min_monthly_workdays_list:
    for wc_max_consec in max_consecutive_days_list:
        config = deepcopy(base_config)
        for k in config["work_constraints"]:
            config["work_constraints"][k]["min_monthly_workdays"] = wc_min_days
            config["work_constraints"][k]["max_consecutive_days"] = wc_max_consec
        status = run_shift_calc(config)
        print(f"  work_constraints: min_days={wc_min_days}, max_consec={wc_max_consec} → {status}")
        results.append({
            "min_monthly_workdays": wc_min_days,
            "max_consecutive_days": wc_max_consec,
            "status": status
        })
        if status == "FEASIBLE" and first_feasible is None:
            first_feasible = {
                "min_monthly_workdays": wc_min_days,
                "max_consecutive_days": wc_max_consec
            }
    if first_feasible:
        break

# もし解なしなら、人数追加に進む
added_roles = []
if not first_feasible:
    print("\n==== work_constraintsをどこまで緩和しても解が出ないので人数追加 ====")
    # 不足役職自動検出
    lacking = find_lacking_roles(base_config, role_need)
    if lacking:
        for role, req, now in lacking:
            print(f"  人数不足: {role}（必要: {req}, 現在: {now}）→ {role}を1人ずつ増やしつつ再探索")
            added_roles.append(role)
        # 1人ずつ増やしながら探索
        for added_num in range(1, 5):  # +4人まで増やす
            config = deepcopy(base_config)
            for role in added_roles:
                # 追加用ダミー名
                new_name = f"{role}_add{added_num}"
                config["positions"][new_name] = role
                # priority_assignmentsへの追加もここで自動化できるが、主にprimary/secondaryの枠がある役職のみ対応
                # ここでは現場実態に応じて必要な場合追加
            for k in config["work_constraints"]:
                config["work_constraints"][k]["min_monthly_workdays"] = min_monthly_workdays_list[0]
                config["work_constraints"][k]["max_consecutive_days"] = max_consecutive_days_list[-1]
            status = run_shift_calc(config)
            print(f"  人数追加: {role} +{added_num}人, min_days={min_monthly_workdays_list[0]}, max_consec={max_consecutive_days_list[-1]} → {status}")
            results.append({
                "roles": {r: f"+{added_num}" for r in added_roles},
                "min_monthly_workdays": min_monthly_workdays_list[0],
                "max_consecutive_days": max_consecutive_days_list[-1],
                "status": status
            })
            if status == "FEASIBLE" and first_feasible is None:
                first_feasible = {
                    "roles": {r: f"+{added_num}" for r in added_roles},
                    "min_monthly_workdays": min_monthly_workdays_list[0],
                    "max_consecutive_days": max_consecutive_days_list[-1]
                }
            if first_feasible:
                break
    else:
        print("  人数不足の役職は自動判定できませんでした。")

with open(f"{OUTPUT_DIR}/fit_summary.json", "w", encoding="utf-8") as fw:
    json.dump(results, fw, ensure_ascii=False, indent=2)

print("\n【最終的なおすすめ条件】")
if first_feasible:
    print("◎ 解が得られた最適な組み合わせ:")
    print(first_feasible)
else:
    print("◎ どのパターンでも解なし→ 制約やスタッフをさらに見直してください")
