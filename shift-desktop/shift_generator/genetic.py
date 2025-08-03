import json
import pandas as pd
import os
import sys
import random
import copy

#コンソールログ出力用
class MultiOut:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, msg):
        for s in self.streams:
            s.write(msg)
    def flush(self):
        for s in self.streams:
            s.flush()
# 全部表示（Jupyterなどでも省略されない）
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

dir_name = "output"
print("受け取ったディレクトリ名:", dir_name)

current_path = os.getcwd()
json_path = f"./new.json"

month_map = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}

os.makedirs(os.path.join(current_path, f"{dir_name}"), exist_ok=True)
os.makedirs(os.path.join(dir_name, "shifts"), exist_ok=True)
os.makedirs(os.path.join(dir_name, "summary"), exist_ok=True)
os.makedirs(os.path.join(dir_name, "work_days"), exist_ok=True)

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
            "min_max": 0, "priority": 0, "rest": 0, "fairness": 0, "dummy": 0
        }
        penalty = 0
        violation_log = {
            "min_max": [], "priority": [], "rest": [], "fairness": [], "dummy": []
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

        # フェア勤務日数（役職単位）
        pos2staff = {}
        for s in staff_list:
            pos = staff_positions[s]
            if pos == "dummy":
                continue
            pos2staff.setdefault(pos, []).append(s)
        for pos, staff_of_pos in pos2staff.items():
            if len(staff_of_pos) < 2:
                continue
            workdays = [sum([1 for d in range(days_in_month) if genome[s][d] != ""]) for s in staff_of_pos]
            diff = max(workdays) - min(workdays)
            if pos == "employee":
                if diff > 3:
                    penalty_detail["fairness"] += (diff - 1) * 10
                    penalty += (diff - 1) * 10
                    violation_log["fairness"].append({
                        "pos": pos, "max_work": max(workdays), "min_work": min(workdays), "diff": diff
                    })
            elif pos == "part_timer":
                if diff > 3:
                    penalty_detail["fairness"] += (diff - 3) * 10
                    penalty += (diff - 3) * 10
                    violation_log["fairness"].append({
                        "pos": pos, "max_work": max(workdays), "min_work": min(workdays), "diff": diff
                    })
            else:
                if diff > 1:
                    penalty_detail["fairness"] += (diff - 1) * 10
                    penalty += (diff - 1) * 10
                    violation_log["fairness"].append({
                        "pos": pos, "max_work": max(workdays), "min_work": min(workdays), "diff": diff
                    })

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
                    w_old = genome[s][d]
                    possible_ws = [w for w in work_types if w in priority_map and s in (priority_map[w].get("primary", []) + priority_map[w].get("secondary", []))]
                    if possible_ws:
                        genome[s][d] = random.choice(possible_ws)
                    else:
                        genome[s][d] = ""
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
    if month_number <= 3:
        actual_year = year + 1
    else:
        actual_year = year
    csv_suffix = f"{str(actual_year)[2:]}{month_number:02d}"

    staff_days = {}
    for s in staff_list:
        staff_days[s] = sum(1 for d in range(days_in_month) if solution[s][d] != "")

    day_records = []
    for d in range(days_in_month):
        working_staff = [s for s in staff_list if solution[s][d] != ""]
        total_work = len(working_staff)
        emp_count = sum(1 for s in working_staff if staff_positions[s] == "employee")
        pt_count = sum(1 for s in working_staff if staff_positions[s] == "part_timer")
        dm_count = sum(1 for s in working_staff if staff_positions[s] == "dummy")

        job_counts = {}
        for w in work_types:
            job_counts[w] = sum(solution[s][d] == w for s in working_staff)

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
            if v == "":
                df_shift.at[s, d + 1] = ""
            else:
                df_shift.at[s, d + 1] = work_type_initial.get(v, v[0])

    print("\n=== 1) 従業員ごとの総勤務日数 ===")
    print(df_staff_days)
    print("\n=== 2) 日毎の出勤人数・業務内訳 ===")
    print(df_day_summary)
    print("\n=== 3) シフト表(従業員×日) ===")
    print(df_shift)
    df_shift.to_csv(os.path.join(dir_name, "shifts", f"shift_result{csv_suffix}.csv"), encoding="utf-8-sig")
    df_staff_days.to_csv(os.path.join(dir_name, "summary", f"staff_workdays{csv_suffix}.csv"), encoding="utf-8-sig")
    df_day_summary.to_csv(os.path.join(dir_name, "work_days", f"day_summary{csv_suffix}.csv"), encoding="utf-8-sig")

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
    out_path = os.path.join(dir_name, "summary", f"dummy_reason_detail_{month_key}.csv")
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
            csv_path = os.path.join(dir_name, "summary", f"violation_{k}_{month_key}.csv")
            df.to_csv(csv_path, encoding="utf-8-sig", index=False)
            print(f"\n【{month_key}】制約違反 {k} 一覧 → {csv_path}")
            print(df.head(10))
    if not any_violation:
        print(f"【{month_key}】制約違反なし（すべての制約を満たしています）")

def main():
    months_to_process = [
        "April"
    ]

    console_log_path = os.path.join(dir_name, "console_log.txt")
    log_file = open(console_log_path, "w", encoding="utf-8")
    sys.stdout = MultiOut(sys.__stdout__, log_file)

    solutions_per_month = []
    staff_positions_per_month = []
    staff_list_per_month = []
    days_in_month_per_month = []
    work_types_per_month = []
    config_per_month = []
    friend_days_per_month = []
    month_key_per_month = []
    violation_logs_per_month = []

    for month_key in months_to_process:
        config = load_config(json_path)
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

        json_penalty_path = os.path.join(dir_name, "summary", f"penalty_detail_{month_key}.json")
        with open(json_penalty_path, "w", encoding="utf-8") as jf:
            json.dump(penalty_detail, jf, ensure_ascii=False, indent=2)

        dummy_used = False
        for s in staff_list:
            if staff_positions[s] == "dummy":
                for d in range(days_in_month):
                    if solution[s][d] != "":
                        dummy_used = True
                        break
            if dummy_used:
                break

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
            month_key_per_month[idx]
        )
        output_violation_log(violation_logs_per_month[idx], month_key_per_month[idx])

    print("=== 全ての月の処理が完了しました ===")
    log_file.close()

if __name__ == "__main__":
    main()
