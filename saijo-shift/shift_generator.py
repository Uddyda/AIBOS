import json
import pandas as pd
from ortools.sat.python import cp_model

json_path = "./config.json"

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_variables(model, staff_list, days_in_month, work_types):
    x = {}
    for s in staff_list:
        x[s] = {}
        for d in range(days_in_month):
            x[s][d] = {}
            for w in work_types:
                x[s][d][w] = model.NewBoolVar(f"x_{s}_{d}_{w}")
    return x

def add_priority_constraints(model, x, config, staff_list, days_in_month):
    """
    priority_assignmentsの各業務(w)に対し、
    primary/secondary/thirdの三段階で人数を満たす
    Minimize用に secondary_list, third_list を収集
    """
    friend_days = set(config["friend_days"])
    daily_req   = config["daily_requirements"]
    priority_map= config["priority_assignments"]

    all_secondary_vars = []
    all_third_vars = []

    for w, pinfo in priority_map.items():
        # 3層に分ける
        primary_staff   = pinfo.get("primary", [])
        secondary_staff = pinfo.get("secondary", [])
        third_staff     = pinfo.get("third", [])

        for d in range(days_in_month):
            day_num = d + 1
            is_friend = (day_num in friend_days)

            # 必要人数 min_req ~ max_req
            if "normal_min" in daily_req[w] and "normal_max" in daily_req[w]:
                if is_friend:
                    min_req = daily_req[w].get("friend_min", daily_req[w]["normal_min"])
                    max_req = daily_req[w].get("friend_max", daily_req[w]["normal_max"])
                else:
                    min_req = daily_req[w]["normal_min"]
                    max_req = daily_req[w]["normal_max"]
            else:
                # single value
                normal_val = daily_req[w].get("normal", 0)
                friend_val = daily_req[w].get("friend", normal_val)
                val = friend_val if is_friend else normal_val
                min_req = val
                max_req = val

            sum_primary = sum(x[s][d][w] for s in primary_staff if s in staff_list)
            secondary_list = [x[s][d][w] for s in secondary_staff if s in staff_list]
            third_list_    = [x[s][d][w] for s in third_staff if s in staff_list]

            sum_secondary = sum(secondary_list)
            sum_third     = sum(third_list_)

            # constraint
            model.Add(sum_primary + sum_secondary + sum_third >= min_req)
            model.Add(sum_primary + sum_secondary + sum_third <= max_req)
            # second <= max_req - primary
            model.Add(sum_secondary <= max_req - sum_primary)
            # third <= max_req - (primary+secondary)
            model.Add(sum_third <= max_req - (sum_primary + sum_secondary))

            # 目的関数用に回収
            all_secondary_vars.extend(secondary_list)
            all_third_vars.extend(third_list_)

    return all_secondary_vars, all_third_vars

def add_daily_constraints_for_nonpriority(model, x, config, staff_list, days_in_month):
    """
    priority_assignments に定義していない業務があれば、こちらで min/maxを処理
    (もし全業務をpriority_assignmentsに書くなら不要)
    """
    friend_days = set(config["friend_days"])
    daily_req   = config["daily_requirements"]
    priority_map= config["priority_assignments"]
    work_types  = list(daily_req.keys())

    for w in work_types:
        if w in priority_map:
            continue  # priority扱いにスキップ
        # 非priority業務 => これまでの add_basic_daily_constraints と同様
        for d in range(days_in_month):
            day_num = d+1
            is_friend = (day_num in friend_days)
            if "normal_min" in daily_req[w] and "normal_max" in daily_req[w]:
                nm_min = daily_req[w]["normal_min"]
                nm_max = daily_req[w]["normal_max"]
                fm_min = daily_req[w].get("friend_min", nm_min)
                fm_max = daily_req[w].get("friend_max", nm_max)
                min_req = fm_min if is_friend else nm_min
                max_req = fm_max if is_friend else nm_max
            else:
                normal_val = daily_req[w].get("normal", 0)
                friend_val = daily_req[w].get("friend", normal_val)
                val = friend_val if is_friend else normal_val
                min_req = val
                max_req = val

            assign_vars = [x[s][d][w] for s in staff_list]  # すべて? or if s is in staff_list
            model.Add(sum(assign_vars) >= min_req)
            model.Add(sum(assign_vars) <= max_req)

def add_one_person_one_job_per_day(model, x, staff_list, days_in_month, work_types):
    for s in staff_list:
        for d in range(days_in_month):
            model.Add(sum(x[s][d][w] for w in work_types) <= 1)

def add_rest_constraints(model, x, config, staff_positions, staff_list, days_in_month, work_types):
    # employee, part_timer, dummy
    wcon_emp = config["work_constraints"]["employee"]
    wcon_pt  = config["work_constraints"]["part_timer"]

    required_days_off_7 = wcon_emp["days_off_per_7days"]
    max_work_in_7 = 7 - required_days_off_7
    max_consec_emp = wcon_emp["max_consecutive_days"]
    min_month_emp  = wcon_emp["min_monthly_workdays"]
    max_consec_pt  = wcon_pt["max_consecutive_days"]

    for s in staff_list:
        pos = staff_positions[s]
        if pos == "employee":
            # 7日中 (required_days_off_7)休み => max_work_in_7日勤務
            for start_day in range(days_in_month - 6):
                model.Add(
                    sum(x[s][d][w] for d in range(start_day, start_day+7) for w in work_types)
                    <= max_work_in_7
                )
            # 連続勤務
            if max_consec_emp < days_in_month:
                for d in range(days_in_month - max_consec_emp):
                    model.Add(
                        sum(x[s][dd][w] for dd in range(d, d+max_consec_emp+1) for w in work_types)
                        <= max_consec_emp
                    )
            # 月最低勤務
            if min_month_emp > 0:
                model.Add(
                    sum(x[s][d][w] for d in range(days_in_month) for w in work_types)
                    >= min_month_emp
                )

        elif pos == "part_timer":
            for d in range(days_in_month - max_consec_pt):
                model.Add(
                    sum(x[s][dd][w] for dd in range(d, d+max_consec_pt+1) for w in work_types)
                    <= max_consec_pt
                )
        elif pos == "dummy":
            # ダミーは制約なし => 何もしない
            pass

def solve_with_or_tools(config):
    days_in_month = config["days_in_month"]
    staff_positions = dict(config["positions"])

    # staff_list
    staff_list = list(staff_positions.keys())
    work_types = list(config["daily_requirements"].keys())

    # モデル
    model = cp_model.CpModel()
    x = create_variables(model, staff_list, days_in_month, work_types)

    # primary+secondary+third constraints
    all_secondary_vars, all_third_vars = add_priority_constraints(model, x, config, staff_list, days_in_month)

    # non-priority業務 (もしもpriority_assignments にない業務があるなら)
    add_daily_constraints_for_nonpriority(model, x, config, staff_list, days_in_month)

    # 1日1人1業務
    add_one_person_one_job_per_day(model, x, staff_list, days_in_month, work_types)

    # rest constraints
    add_rest_constraints(model, x, config, staff_positions, staff_list, days_in_month, work_types)

    # Minimize: sum(secondary) + 10000 * sum(third)
    # thirdの重みを大きくしてさらに優先度下げる
    COST_FACTOR_THIRD = 10000
    model.Minimize(sum(all_secondary_vars) + COST_FACTOR_THIRD * sum(all_third_vars))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return status, None, staff_list, staff_positions, work_types

    # 解取り出し
    solution = {}
    for s in staff_list:
        solution[s] = []
        for d in range(days_in_month):
            assigned = ""
            for w in work_types:
                if solver.Value(x[s][d][w]) == 1:
                    assigned = w
                    break
            solution[s].append(assigned)
    return status, solution, staff_list, staff_positions, work_types

def summarize_solution(solution, staff_positions, staff_list, days_in_month, work_types, config):
    staff_days = {}
    for s in staff_list:
        staff_days[s] = sum(1 for d in range(days_in_month) if solution[s][d] != "")

    day_records = []
    for d in range(days_in_month):
        working_staff = [s for s in staff_list if solution[s][d] != ""]
        total_work = len(working_staff)
        emp_count = sum(1 for s in working_staff if staff_positions[s] == "employee")
        pt_count  = sum(1 for s in working_staff if staff_positions[s] == "part_timer")
        dm_count  = sum(1 for s in working_staff if staff_positions[s] == "dummy")

        job_counts = {}
        for w in work_types:
            job_counts[w] = sum(solution[s][d] == w for s in working_staff)

        day_records.append({
            "day": d+1,
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

    # シフト表
    df_shift = pd.DataFrame(index=staff_list, columns=range(1, days_in_month+1))
    for s in staff_list:
        for d in range(days_in_month):
            df_shift.at[s, d+1] = solution[s][d]

    print("\n=== 1) 従業員ごとの総勤務日数 ===")
    print(df_staff_days)
    print("\n=== 2) 日毎の出勤人数・業務内訳 ===")
    print(df_day_summary)
    print("\n=== 3) シフト表(従業員×日) ===")
    print(df_shift)
    # ▼ CSVファイル出力
    df_shift.to_csv("shift_result.csv", encoding="utf-8-sig")
    df_staff_days.to_csv("staff_workdays.csv", encoding="utf-8-sig")
    df_day_summary.to_csv("day_summary.csv", encoding="utf-8-sig")

    return df_staff_days, df_day_summary, df_shift

def main():
    config = load_config(f"{json_path}")  # あなたのJSONパス
    status, solution, staff_list, staff_positions, work_types = solve_with_or_tools(config)

    if solution is None:
        print("解が見つかりませんでした。")
        return

    # 解が見つかった。ダミーの割当をチェック
    # ダミーかどうかは positions で "dummy" と定義している想定
    dummy_used = False
    for s in staff_list:
        if staff_positions[s] == "dummy":
            # このスタッフが1日でも勤務していれば dummy_used=True
            for d in range(config["days_in_month"]):
                if solution[s][d] != "":
                    dummy_used = True
                    break
        if dummy_used:
            break

    if dummy_used:
        print("=== ダミーが割り当てられました。以下のシフトに警告があります ===")
    else:
        print("=== シフトが見つかりました (ダミーなし) ===")

    # つづいて集計を表示
    summarize_solution(solution, staff_positions, staff_list,
                       config["days_in_month"], work_types, config)

    # もし具体的にダミーが入った日付を列挙したいなら
    if dummy_used:
        shortage_list = []
        for d in range(config["days_in_month"]):
            for s in staff_list:
                if staff_positions[s] == "dummy" and solution[s][d] != "":
                    shortage_list.append((d+1, s, solution[s][d]))
        if shortage_list:
            print("\n--- 警告: ダミー勤務箇所 ---")
            for (day_num, dummy_name, job) in shortage_list:
                print(f"  Day {day_num}, Job '{job}' → {dummy_name}")

if __name__ == "__main__":
    main()
