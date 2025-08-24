import json
import pandas as pd
import os
import sys
import random
import copy
import atexit
import re


# コンソールログ出力用（安全版）
class MultiOut:
    def __init__(self, *streams):
        self.streams = list(streams)
    def write(self, msg):
        for s in list(self.streams):
            try:
                s.write(msg)
            except Exception:
                try:
                    self.streams.remove(s)
                except:
                    pass
    def flush(self):
        for s in list(self.streams):
            try:
                s.flush()
            except Exception:
                try:
                    self.streams.remove(s)
                except:
                    pass

# 全部表示（Jupyterなどでも省略されない）
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# ====== 引数パース ======
# argv[1]: 生成ディレクトリ名 (必須)
# argv[2]: new.json のパス (省略可: カレントディレクトリ/new.json)
# argv[3]: 出力ルートディレクトリ (省略可: カレントディレクトリ)
if len(sys.argv) < 2:
    print("Usage: python <this_file>.py <dir_name> [json_path] [output_root]")
    sys.exit(1)

dir_name = sys.argv[1]
json_path = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(os.getcwd(), "new.json")
output_root = sys.argv[3] if len(sys.argv) >= 4 else os.getcwd()

print("[ga_shift] dir_name   :", dir_name)
print("[ga_shift] json_path  :", json_path)
print("[ga_shift] output_root:", output_root)

# 出力先ディレクトリ（絶対パス）— ここに全成果物をまとめる
out_dir = os.path.join(output_root, dir_name)
os.makedirs(out_dir, exist_ok=True)
os.makedirs(os.path.join(out_dir, "shifts"), exist_ok=True)
#os.makedirs(os.path.join(out_dir, "summary"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "work_days"), exist_ok=True)

month_map = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}
# 逆引き用
num_to_name = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# ===== 旧コード（無効）：固定パスや current_path, dir_name 直下に出す実装は廃止 =====
# dir_name = "output"
# print("受け取ったディレクトリ名:", dir_name)
# current_path = os.getcwd()
# json_path = f"./new.json"
# os.makedirs(os.path.join(current_path, f"{dir_name}"), exist_ok=True)
# os.makedirs(os.path.join(dir_name, "shifts"), exist_ok=True)
# os.makedirs(os.path.join(dir_name, "summary"), exist_ok=True)
# os.makedirs(os.path.join(dir_name, "work_days"), exist_ok=True)
# ※ 以降は out_dir 配下に集約します。

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def get_recent_consecutive(genome, s, d):
    cnt = 0
    for back in range(1, min(d+1, 7)):
        if genome[s][d-back] != "":
            cnt += 1
        else:
            break
    return cnt

def solve_with_ga(config, days_in_month, friend_days, generations=150, population_size=60):
    staff_positions = dict(config["positions"])
    staff_list = list(staff_positions.keys())
    work_types = list(config["daily_requirements"].keys())
    priority_map = config["priority_assignments"]
    daily_req = config["daily_requirements"]
    friend_days_set = set(friend_days)

    # create_random_genome: priority→secondary→dummy
    def create_random_genome():
        genome = {s: [""] * days_in_month for s in staff_list}
        for d in range(days_in_month):
            # 各業務ごと必要人数カウント
            req_left = {}
            for w in work_types:
                req = daily_req[w]
                day_num = d + 1
                is_friend = (day_num in friend_days_set)
                if "normal_min" in req and "normal_max" in req:
                    min_req = req["friend_min"] if is_friend and "friend_min" in req else req["normal_min"]
                else:
                    min_req = req.get("friend", req.get("normal", 0))
                req_left[w] = min_req

            # スタッフ順をランダムにする（シフトのランダム性担保）
            shuffled_staff = staff_list.copy()
            random.shuffle(shuffled_staff)
            for s in shuffled_staff:
                # その日すでに連勤maxかどうか判定
                pos = staff_positions[s]
                max_consec = config["work_constraints"][pos]["max_consecutive_days"]
                if get_recent_consecutive(genome, s, d) >= max_consec:
                    continue  # これ以上割当不可
                # 割当可能な業務をpriority→secondaryの順で選択
                candidates = []
                for level in ["primary", "secondary"]:
                    for w in work_types:
                        pinfo = priority_map.get(w, {})
                        if s in pinfo.get(level, []) and req_left[w] > 0:
                            candidates.append((level, w))
                    if candidates:
                        break  # primary候補があればsecondaryを見ない
                if candidates:
                    # どれかランダムに1つ選んで割当
                    _, w_selected = random.choice(candidates)
                    genome[s][d] = w_selected
                    req_left[w_selected] -= 1

            # まだ埋まっていない業務はダミーで埋める
            for w in work_types:
                if req_left[w] > 0:
                    dummy_candidates = [s for s in staff_list if staff_positions[s] == "dummy" and genome[s][d] == ""]
                    n = min(len(dummy_candidates), req_left[w])
                    selected = random.sample(dummy_candidates, n)
                    for s in selected:
                        genome[s][d] = w
        return genome

    # 評価関数（ペナルティ詳細＋違反箇所も記録）
    def calc_penalty(genome):
        penalty_detail = {
            "min_max": 0, "priority": 0, "rest": 0, "fairness": 0, "role_headcount": 0, "dummy": 0
        }
        penalty = 0
        violation_log = {
            "min_max": [], "priority": [], "rest": [], "fairness": [], "role_headcount": [], "dummy": []
        }

        for d in range(days_in_month):
            day_num = d + 1
            is_friend = (day_num in friend_days_set)
            for w in work_types:
                assigned_staff = [s for s in staff_list if genome[s][d] == w]
                req = daily_req[w]
                if "normal_min" in req and "normal_max" in req:
                    min_req = req["friend_min"] if is_friend and "friend_min" in req else req["normal_min"]
                    max_req = req["friend_max"] if is_friend and "friend_max" in req else req["normal_max"]
                else:
                    val = req.get("friend", req.get("normal", 0))
                    min_req = max_req = val

                n = len(assigned_staff)
                if n < min_req:
                    penalty_detail["min_max"] += (min_req - n) * 10
                    penalty += (min_req - n) * 10
                    violation_log["min_max"].append({
                        "day": day_num, "work": w, "type": "under", "min_req": min_req, "assigned": n
                    })
                if n > max_req:
                    penalty_detail["min_max"] += (n - max_req) * 10
                    penalty += (n - max_req) * 10
                    violation_log["min_max"].append({
                        "day": day_num, "work": w, "type": "over", "max_req": max_req, "assigned": n
                    })
                # priority_assignments違反チェック
                pinfo = priority_map.get(w, {})
                allowed_staff = set(pinfo.get("primary", []) + pinfo.get("secondary", []) + pinfo.get("third", [])) if w in priority_map else set(staff_list)
                for s in assigned_staff:
                    if s not in allowed_staff:
                        penalty_detail["priority"] += 100
                        penalty += 100
                        violation_log["priority"].append({
                            "day": day_num, "work": w, "staff": s
                        })

        for w, pinfo in priority_map.items():
            allowed = set(pinfo.get("primary", []) + pinfo.get("secondary", []) + pinfo.get("third", []))
            for s in staff_list:
                for d in range(days_in_month):
                    if genome[s][d] == w and s not in allowed:
                        penalty_detail["priority"] += 100
                        penalty += 100
                        violation_log["priority"].append({
                            "day": d+1, "work": w, "staff": s
                        })

        for s in staff_list:
            pos = staff_positions[s]
            wcon = config["work_constraints"][pos]
            required_days_off_7 = wcon["days_off_per_7days"]
            max_work_in_7 = 7 - required_days_off_7
            max_consec = wcon["max_consecutive_days"]
            min_month = wcon["min_monthly_workdays"]
            # 7日ごと勤務日数
            for start in range(days_in_month - 6):
                works = sum([1 for d in range(start, start + 7) if genome[s][d] != ""])
                if works > max_work_in_7:
                    penalty_detail["rest"] += (works - max_work_in_7) * 5
                    penalty += (works - max_work_in_7) * 5
                    violation_log["rest"].append({
                        "staff": s, "type": "over_7days", "start_day": start+1, "works": works, "max": max_work_in_7
                    })
            # max連勤
            if max_consec < days_in_month:
                for start in range(days_in_month - max_consec):
                    works = sum([1 for d in range(start, start + max_consec + 1) if genome[s][d] != ""])
                    if works > max_consec:
                        penalty_detail["rest"] += (works - max_consec) * 5
                        penalty += (works - max_consec) * 5
                        violation_log["rest"].append({
                            "staff": s, "type": "over_consecutive", "start_day": start+1, "works": works, "max": max_consec
                        })
            # 月最低勤務
            works = sum([1 for d in range(days_in_month) if genome[s][d] != ""])
            if works < min_month:
                penalty_detail["rest"] += (min_month - works) * 5
                penalty += (min_month - works) * 5
                violation_log["rest"].append({
                    "staff": s, "type": "under_min_month", "min": min_month, "works": works
                })

        # === フェア勤務日数（役職ラベル単位）===
        # 重み（なければ10）。今回は許容差(しきい値)は 0 とし、差があればペナルティ
        fairness_weight = int(config.get("fairness_weight", 50))

        # 役職ラベルごとにグループ化（ダミー除外）
        role2staff = {}
        for s in staff_list:
            if staff_positions[s] == "dummy":
                continue
            role = staff_to_role_label(s)
            role2staff.setdefault(role, []).append(s)

        for role, members in role2staff.items():
            if len(members) < 2:
                continue  # 1人しかいない役職は公平性の対象外

            # 役職内の各スタッフの勤務日数
            workdays_per_staff = {
                s: sum(1 for d in range(days_in_month) if genome[s][d] != "")
                for s in members
            }
            max_w = max(workdays_per_staff.values())
            min_w = min(workdays_per_staff.values())
            diff = max_w - min_w

            if diff > 0 and fairness_weight > 0:
                add = diff * diff * fairness_weight
                penalty_detail["fairness"] += add
                penalty += add
                # 代表のpos（employee/part_timer）も添えると後で読みやすい
                pos_rep = staff_positions[members[0]]
                violation_log["fairness"].append({
                    "role": role,
                    "pos": pos_rep,
                    "max_work": max_w,
                    "min_work": min_w,
                    "diff": diff,
                })

        
        # === 役職ごとの「使用人数 × 点数」ペナルティ（JSON変更なし） ===
        ROLE_USAGE_UNIT_PENALTY = 50  # 1人あたりのペナルティ（0で無効化）
        if ROLE_USAGE_UNIT_PENALTY > 0:
            # 役職ラベル -> メンバー（dummyは除外）
            role_members = {}
            for s in staff_list:
                if staff_positions[s] == "dummy":
                    continue
                role = staff_to_role_label(s)  # 例: 火葬員A → 火葬員
                role_members.setdefault(role, []).append(s)

            # 各役職の「その月に1日でも勤務したユニーク人数」を数える
            total_usage_penalty = 0
            for role, members in role_members.items():
                used = 0
                for s in members:
                    # 1日でも入っていればカウント
                    for d in range(days_in_month):
                        if genome[s][d] != "":
                            used += 1
                            break
                # 役職ごとの人数 × 点数 を合算
                if used > 0:
                    total_usage_penalty += used * used * ROLE_USAGE_UNIT_PENALTY

            if total_usage_penalty > 0:
                penalty_detail.setdefault("role_headcount", 0)
                penalty_detail["role_headcount"] += total_usage_penalty
                penalty += total_usage_penalty




        for s in staff_list:
            if staff_positions[s] == "dummy":
                for d in range(days_in_month):
                    if genome[s][d] != "":
                        penalty_detail["dummy"] += 1000
                        penalty += 1000
                        violation_log["dummy"].append({
                            "staff": s, "day": d+1, "job": genome[s][d]
                        })

        return penalty, penalty_detail, violation_log

    def crossover(parent1, parent2):
        child = {}
        for s in staff_list:
            pivot = random.randint(0, days_in_month - 1)
            child[s] = parent1[s][:pivot] + parent2[s][pivot:]
        return child

    def mutate(genome, mutation_rate=0.05):
        genome = copy.deepcopy(genome)
        for s in staff_list:
            for d in range(days_in_month):
                if random.random() < mutation_rate:
                    # 必ずprimary→secondary→dummyの優先順で再割り当てする
                    possible_ws = [w for w in work_types if w in priority_map and s in (priority_map[w].get("primary", []) + priority_map[w].get("secondary", []))]
                    genome[s][d] = random.choice(possible_ws) if possible_ws else ""
        return genome

    population = [create_random_genome() for _ in range(population_size)]
    best_penalty = float('inf')
    best_solution = None
    best_detail = None
    best_violation_log = None

    for gen in range(generations):
        scored_population = [(genome, *calc_penalty(genome)) for genome in population]
        scored_population.sort(key=lambda x: x[1])
        if scored_population[0][1] < best_penalty:
            best_penalty = scored_population[0][1]
            best_solution = scored_population[0][0]
            best_detail = scored_population[0][2]
            best_violation_log = scored_population[0][3]
        if best_penalty == 0:
            break
        survivors = [g for g, _, _, _ in scored_population[:population_size // 2]]
        next_population = []
        while len(next_population) < population_size:
            p1, p2 = random.sample(survivors, 2)
            child = crossover(p1, p2)
            child = mutate(child)
            next_population.append(child)
        population = next_population
        if gen % 50 == 0:
            print(f"[gen={gen}] best_penalty={best_penalty}")

    return 0 if best_penalty == 0 else 1, best_solution, staff_list, staff_positions, work_types, best_detail, best_violation_log

def summarize_solution(solution, staff_positions, staff_list, days_in_month, work_types, month_key, config):
    year = config["year"]
    month_number = month_map[month_key]
    work_type_initial = {w: w[0] for w in work_types}
    # 1〜3月は翌年、4〜12月はそのまま
    actual_year = year + 1 if month_number <= 3 else year
    csv_suffix = f"{str(actual_year)[2:]}{month_number:02d}"

    staff_days = {s: sum(1 for d in range(days_in_month) if solution[s][d] != "") for s in staff_list}

    day_records = []
    for d in range(days_in_month):
        working_staff = [s for s in staff_list if solution[s][d] != ""]
        total_work = len(working_staff)
        emp_count = sum(1 for s in working_staff if staff_positions[s] == "employee")
        pt_count = sum(1 for s in working_staff if staff_positions[s] == "part_timer")
        dm_count = sum(1 for s in working_staff if staff_positions[s] == "dummy")

        job_counts = {w: sum(solution[s][d] == w for s in working_staff) for w in work_types}

        day_records.append({
            "day": d + 1,
            "total_working": total_work,
            "employee_count": emp_count,
            "part_timer_count": pt_count,
            "dummy_count": dm_count,
            **{f"job_{w}": job_counts[w] for w in work_types}
        })

    df_staff_days = pd.DataFrame({
        "staff": staff_list,
        "total_workdays": [staff_days[s] for s in staff_list]
    }).set_index("staff")

    df_day_summary = pd.DataFrame(day_records).set_index("day")

    df_shift = pd.DataFrame(index=staff_list, columns=range(1, days_in_month + 1))
    for s in staff_list:
        for d in range(days_in_month):
            v = solution[s][d]
            df_shift.at[s, d + 1] = "" if v == "" else work_type_initial.get(v, v[0])

    print("\n=== 1) 従業員ごとの総勤務日数 ===")
    print(df_staff_days)
    print("\n=== 2) 日毎の出勤人数・業務内訳 ===")
    print(df_day_summary)
    print("\n=== 3) シフト表(従業員×日) ===")
    print(df_shift)

    # ▼ CSVファイル出力（※ 出力は out_dir 配下に統一）
    df_shift.to_csv(os.path.join(out_dir, "shifts",  f"shift_result{csv_suffix}.csv"),  encoding="utf-8-sig")
    #df_staff_days.to_csv(os.path.join(out_dir, "summary", f"staff_workdays{csv_suffix}.csv"), encoding="utf-8-sig")
    df_day_summary.to_csv(os.path.join(out_dir, "work_days", f"day_summary{csv_suffix}.csv"),   encoding="utf-8-sig")

    return df_staff_days, df_day_summary, df_shift

def analyze_dummy_reason(solution, staff_positions, staff_list, days_in_month, work_types, config, friend_days, month_key):
    daily_req = config["daily_requirements"]
    friend_days_set = set(friend_days)
    result = []

    for d in range(days_in_month):
        day_num = d + 1
        is_friend = (day_num in friend_days_set)
        for w in work_types:
            req = daily_req[w]
            if "normal_min" in req and "normal_max" in req:
                min_req = req["friend_min"] if is_friend and "friend_min" in req else req["normal_min"]
            else:
                min_req = req.get("friend", req.get("normal", req.get("normal_min", 0)))
            assigned_staff = [s for s in staff_list if solution[s][d] == w]
            num_dummy = sum(1 for s in assigned_staff if staff_positions[s] == "dummy")
            num_real = sum(1 for s in assigned_staff if staff_positions[s] != "dummy")
            if num_dummy > 0:
                result.append({
                    "day": day_num,
                    "work": w,
                    "min_req": min_req,
                    "real_assigned": num_real,
                    "dummy_assigned": num_dummy,
                    "real_deficit": max(0, min_req - num_real)
                })
    df = pd.DataFrame(result)
    if df.empty:
        print(f"ダミー補充発生なし（{month_key}）")
        return
    out_path = os.path.join(out_dir, "summary", f"dummy_reason_detail_{month_key}.csv")
    df.to_csv(out_path, encoding="utf-8-sig", index=False)
    print(f"\n=== ダミー補充内訳（{month_key}）CSV: {out_path} ===")
    print(df.head(10))
    print("\n--- 業務別ダミー割当合計 ---")
    print(df.groupby("work")["dummy_assigned"].sum())
    print("\n--- 日別ダミー割当合計 ---")
    print(df.groupby("day")["dummy_assigned"].sum())

def output_violation_log(violation_log, month_key):
    any_violation = False
    for k, vlist in violation_log.items():
        if vlist:
            any_violation = True
            df = pd.DataFrame(vlist)
            csv_path = os.path.join(out_dir, "summary", f"violation_{k}_{month_key}.csv")
            df.to_csv(csv_path, encoding="utf-8-sig", index=False)
            print(f"\n【{month_key}】制約違反 {k} 一覧 → {csv_path}")
            print(df.head(10))
    if not any_violation:
        print(f"【{month_key}】制約違反なし（すべての制約を満たしています）")

# 追加：1人あたりの月最大勤務可能日数を概算
def monthly_capacity_by_constraints(wcon, days_in_month):
    """
    就業規則から1人あたりの月最大勤務可能日数を概算する。
    - 7日間の最大勤務日数: (7 - days_off_per_7days)
    - 月単位の上限: full_weeks * max_in_7 + min(rem, max_in_7)
    - 連続勤務上限も考慮し安全側で min を取る
    """
    max_in_7 = 7 - int(wcon.get("days_off_per_7days", 0))
    max_in_7 = max(0, min(7, max_in_7))
    full_weeks = days_in_month // 7
    rem = days_in_month % 7
    by_week_cap = full_weeks * max_in_7 + min(rem, max_in_7)

    max_consec = int(wcon.get("max_consecutive_days", days_in_month))
    cap = min(by_week_cap, days_in_month, max_consec if max_consec > 0 else days_in_month)
    return max(0, cap)

# --- 役職名をスタッフ名から復元（末尾の英字 'A','B',... を落とす）---
ROLE_SUFFIX_RE = re.compile(r"[A-Za-z]$")

def staff_to_role_label(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return name
    return name[:-1] if ROLE_SUFFIX_RE.search(name) else name

def compute_total_required_workdays_by_worktype(config, days_in_month, friend_days, work_types):
    """各業務wについて、月内の必要延べ稼働日数(最小値)を集計して dict で返す。"""
    friend_days_set = set(friend_days)
    req_map = {w: 0 for w in work_types}
    for d in range(days_in_month):
        day_num = d + 1
        is_friend = (day_num in friend_days_set)
        for w in work_types:
            req = config["daily_requirements"][w]
            if "normal_min" in req and "normal_max" in req:
                min_req = req["friend_min"] if is_friend and "friend_min" in req else req["normal_min"]
            else:
                min_req = req.get("friend", req.get("normal", req.get("normal_min", 0)))
            req_map[w] += int(min_req)
    return req_map

def estimate_required_headcount_by_role(config, days_in_month, friend_days, work_types, month_key):
    """
    役職ごとの必要人数（絶対値）を推定してコンソール出力する。
    手順:
      1) 業務ごとの月必要人日(最小)を算出
      2) primary だけで貪欲に埋める（各役職を1人ずつ追加し、最もカバーできる役職を選ぶ）
      3) 残った分を secondary で貪欲に埋める
      4) 全役職について人数を出力（0人でも出力）
    """
    positions = config["positions"]  # {staff_name: "employee"|"part_timer"|"dummy"}
    priority_map = config["priority_assignments"]  # {work: {primary:[staff], secondary:[staff], ...}}

    # 役職ラベル -> ポジション種別
    role_pos = {}
    for s, pos in positions.items():
        if pos == "dummy":
            continue
        role = staff_to_role_label(s)
        role_pos.setdefault(role, pos)

    # 業務ごとの「この役職なら入れる」集合（primary / secondary）
    work_primary_roles = {w: set() for w in work_types}
    work_secondary_roles = {w: set() for w in work_types}
    for w in work_types:
        pinfo = priority_map.get(w, {}) or {}
        for s in pinfo.get("primary", []) or []:
            r = staff_to_role_label(s)
            if r in role_pos:
                work_primary_roles[w].add(r)
        for s in pinfo.get("secondary", []) or []:
            r = staff_to_role_label(s)
            if r in role_pos and r not in work_primary_roles[w]:
                work_secondary_roles[w].add(r)

    # 各役職の1人あたり月上限cap
    caps = {}
    for r, pos in role_pos.items():
        caps[r] = monthly_capacity_by_constraints(config["work_constraints"].get(pos, {}), days_in_month)

    # 役職ごとの primary / secondary 対応業務リスト
    primary_w_by_role = {r: [w for w in work_types if r in work_primary_roles[w]] for r in role_pos}
    secondary_w_by_role = {r: [w for w in work_types if r in work_secondary_roles[w]] for r in role_pos}

    # 業務ごとの月合計必要人日
    remaining = compute_total_required_workdays_by_worktype(config, days_in_month, friend_days, work_types)

    # 必要人数（役職ごと）— 全役職を0で初期化（0でも最終出力するため）
    headcount = {r: 0 for r in role_pos}

    # 1) primary だけで貪欲に埋める
    def simulate_cover(r, tasks):
        """役職rを1名追加したとき、tasks(=業務リスト)でどれだけ埋められるか"""
        cap = caps.get(r, 0)
        if cap <= 0 or not tasks:
            return 0, {}
        alloc = {}
        cover = 0
        # 残需要の大きい業務から埋める
        for w in sorted(tasks, key=lambda x: remaining.get(x, 0), reverse=True):
            if cap == 0:
                break
            need = remaining.get(w, 0)
            if need <= 0:
                continue
            take = min(need, cap)
            alloc[w] = take
            cover += take
            cap -= take
        return cover, alloc

    # stage1: primary
    while True:
        total_need = sum(remaining.values())
        if total_need == 0:
            break
        best_r, best_cover, best_alloc = None, 0, {}
        for r in role_pos:
            cover, alloc = simulate_cover(r, primary_w_by_role[r])
            # primary優先: cover が同じなら primary対応数が多い役職を優先
            score = (cover, len(primary_w_by_role[r]))
            if score > (best_cover, len(primary_w_by_role.get(best_r, [])) if best_r else 0):
                best_r, best_cover, best_alloc = r, cover, alloc
        if best_cover == 0:
            break  # primary ではこれ以上埋められない
        headcount[best_r] += 1
        for w, t in best_alloc.items():
            remaining[w] -= t

    # 2) secondary で残りを貪欲に埋める
    while True:
        total_need = sum(remaining.values())
        if total_need == 0:
            break
        best_r, best_cover, best_alloc = None, 0, {}
        for r in role_pos:
            cover, alloc = simulate_cover(r, secondary_w_by_role[r])
            # tie-break: secondary対応数が多いほう
            score = (cover, len(secondary_w_by_role[r]))
            if score > (best_cover, len(secondary_w_by_role.get(best_r, [])) if best_r else 0):
                best_r, best_cover, best_alloc = r, cover, alloc
        if best_cover == 0:
            break  # これ以上埋められない
        headcount[best_r] += 1
        for w, t in best_alloc.items():
            remaining[w] -= t

    # 3) 結果出力（全役職を必ず出す・0人でも）
    print(f"\n=== {month_key}: 役職ごとの必要人数（絶対値・推定）===")
    for r in role_pos.keys():
        pos = role_pos[r]
        print(f"- {r}: {headcount[r]} 人 ")

    # 4) 未充足が残っていれば知らせる
    unfilled = {w: v for w, v in remaining.items() if v > 0}
    if unfilled:
        print("※ まだ埋まっていない業務があります（この役職構成では不足）:")
        for w, v in sorted(unfilled.items(), key=lambda x: -x[1]):
            print(f"  ・{w}: 残り {v} 人日")

    return headcount, remaining



# 追加：ダミー不足から追加必要人数を推定
def estimate_additional_headcount_from_dummy(solution, staff_positions, days_in_month, config, month_key):
    """
    解(solution)に含まれる 'dummy' の稼働から、不足総日数を算出。
    employee / part_timer を増やす場合の推奨追加人数を返す。
    戻り値: dict（JSON/CSV も保存）
    """
    # 月内 Dummy 稼働日数（延べ）
    dummy_days_total = 0
    for s, pos in staff_positions.items():
        if pos != "dummy":
            continue
        for d in range(days_in_month):
            if solution[s][d] != "":
                dummy_days_total += 1

    # 各ポジションの1人あたり上限
    wcs = config["work_constraints"]
    caps = {}
    for pos_key in ["employee", "part_timer"]:
        if pos_key in wcs:
            caps[pos_key] = monthly_capacity_by_constraints(wcs[pos_key], days_in_month)
        else:
            caps[pos_key] = 0

    # 追加必要人数（切上げ）
    rec = {
        "month_key": month_key,
        "days_in_month": days_in_month,
        "dummy_workdays_total": dummy_days_total,
        "per_person_capacity": caps,
        "recommendation": {}
    }
    for pos_key, cap in caps.items():
        if cap <= 0:
            rec["recommendation"][pos_key] = None
        else:
            need = (dummy_days_total + cap - 1) // cap
            rec["recommendation"][pos_key] = int(need)

    # 保存
    df = pd.DataFrame([
        {
            "month": month_key,
            "dummy_workdays_total": dummy_days_total,
            "per_person_capacity_employee": caps.get("employee", 0),
            "per_person_capacity_part_timer": caps.get("part_timer", 0),
            "add_employee_if_chosen": rec["recommendation"].get("employee"),
            "add_part_timer_if_chosen": rec["recommendation"].get("part_timer"),
        }
    ])
    csv_path = os.path.join(out_dir, "summary", f"recommended_headcount_{month_key}.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_out_path = os.path.join(out_dir, "summary", f"recommended_headcount_{month_key}.json")
    with open(json_out_path, "w", encoding="utf-8") as jf:
        json.dump(rec, jf, ensure_ascii=False, indent=2)

    print(f"\n=== {month_key}: 必要人数の推定 ===")
    print(df)
    print(f"- CSV:  {csv_path}")
    print(f"- JSON: {json_out_path}")
    return rec

def main():
    # 先に new.json を読む
    base_config = load_config(json_path)

    # new.json の months(YYYYMM) → 英語月名へ変換
    months_raw = base_config.get("months", [])
    month_nums = []
    for m in months_raw:
        s = str(m)
        if len(s) >= 2 and s[-2:].isdigit():
            month_nums.append(int(s[-2:]))
    months_to_process = [num_to_name[n] for n in month_nums if n in num_to_name]
    if not months_to_process:
        months_to_process = ["April"]  # フォールバック
    print("=== 対象月 ===", months_to_process)

    # ヘッドカウント最適化モード（UIトグル想定）
    # 互換：mode: "optimize" でも有効化
    optimize_headcount = bool(base_config.get("optimize_headcount", False)) or base_config.get("mode") == "optimize"
    if optimize_headcount:
        print("※ optimize_headcount: ON（不足から追加必要人数を推定します）")
    else:
        print("※ optimize_headcount: OFF（従来どおり人数固定でGA）")

    # ログは out_dir に出す
    console_log_path = os.path.join(out_dir, "console_log.txt")
    log_file = open(console_log_path, "w", encoding="utf-8")
    tee = MultiOut(sys.__stdout__, log_file)
    sys.stdout = tee

    def _restore_stdout():
        # stdout を元に戻してからファイルを閉じる
        try:
            sys.stdout = sys.__stdout__
        except Exception:
            pass
        try:
            log_file.close()
        except Exception:
            pass
    atexit.register(_restore_stdout)

    solutions_per_month = []
    staff_positions_per_month = []
    staff_list_per_month = []
    days_in_month_per_month = []
    work_types_per_month = []
    config_per_month = []
    friend_days_per_month = []
    month_key_per_month = []
    violation_logs_per_month = []
    recommendations_per_month = []

    for month_key in months_to_process:
        config = load_config(json_path)
        if "calendar" not in config or month_key not in config["calendar"]:
            print(f"!!! {month_key} のカレンダー定義が new.json にありません。スキップします。")
            continue

        days_in_month = config["calendar"][month_key]["days_in_month"]
        friend_days = config["calendar"][month_key]["friend_days"]
        print(f"=== {month_key} (days_in_month={days_in_month}) ===")

        status, solution, staff_list, staff_positions, work_types, penalty_detail, violation_log = solve_with_ga(
            config,
            days_in_month,
            friend_days
        )

        if solution is None:
            print("解が見つかりませんでした。")
            continue
        else:
            summarize_solution(
                solution,
                staff_positions,
                staff_list,
                days_in_month,
                work_types,
                month_key,
                config
            )

        # ペナルティ詳細JSONも out_dir に保存
        json_penalty_path = os.path.join(out_dir, "summary", f"penalty_detail_{month_key}.json")
        with open(json_penalty_path, "w", encoding="utf-8") as jf:
            json.dump(penalty_detail, jf, ensure_ascii=False, indent=2)

        # ダミー割当の有無チェック
        dummy_used = any(
            staff_positions[s] == "dummy" and any(solution[s][d] != "" for d in range(days_in_month))
            for s in staff_list
        )

        if dummy_used:
            print("=== ダミーが割り当てられました。以下のシフトに警告があります ===")
        else:
            print("=== シフトが見つかりました (ダミーなし) ===")

        if dummy_used:
            shortage_list = []
            for d in range(days_in_month):
                for s in staff_list:
                    if staff_positions[s] == "dummy" and solution[s][d] != "":
                        job_initial = solution[s][d][0]
                        shortage_list.append((d + 1, s, job_initial))
            if shortage_list:
                print("\n--- 警告: ダミー勤務箇所 ---")
                for (day_num, dummy_name, job) in shortage_list:
                    print(f"  Day {day_num}, Job '{job}' → {dummy_name}")

        print("\n=== 最良個体のペナルティ内訳 ===")
        for k, v in penalty_detail.items():
            print(f"  {k}: {v}")



        # 集計して後から分析
        solutions_per_month.append(solution)
        staff_positions_per_month.append(staff_positions)
        staff_list_per_month.append(staff_list)
        days_in_month_per_month.append(days_in_month)
        work_types_per_month.append(work_types)
        config_per_month.append(config)
        friend_days_per_month.append(friend_days)
        month_key_per_month.append(month_key)
        violation_logs_per_month.append(violation_log)

    for idx in range(len(solutions_per_month)):
        analyze_dummy_reason(
            solutions_per_month[idx],
            staff_positions_per_month[idx],
            staff_list_per_month[idx],
            days_in_month_per_month[idx],
            work_types_per_month[idx],
            config_per_month[idx],
            friend_days_per_month[idx],
            month_key_per_month[idx], 
        )
        output_violation_log(violation_logs_per_month[idx], month_key_per_month[idx])


        # 人数最適化モード：不足から追加必要人数を推定
        if optimize_headcount:
            # 業務リストは solve_with_ga の戻り値で変数 work_types が定義済み
            estimate_required_headcount_by_role(
                config, days_in_month, friend_days, work_types, month_key
            )

    print("=== 全ての月の処理が完了しました ===")
    # 明示クローズ（atexitも設定済みだが二重クローズでも安全）
    try:
        log_file.close()
    except Exception:
        pass

if __name__ == "__main__":
    main()
