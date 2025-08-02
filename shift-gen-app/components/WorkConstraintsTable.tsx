import React from "react";
import type { WorkConstraints, WorkConstraint } from "../types/shift";

type Props = {
  workConstraints: WorkConstraints;
  onChange: (typeKey: keyof WorkConstraints, field: keyof WorkConstraint, value: number) => void;
};

const TYPE_LABELS: { [key: string]: string } = {
  employee: "正社員",
  part_timer: "パート",
  dummy: "ダミー"
};

const WorkConstraintsTable: React.FC<Props> = ({ workConstraints, onChange }) => (
  <div
    style={{
      background: "#f6fafd",        // 淡色背景で統一
      borderRadius: 18,             // 大きめ角丸
      boxShadow: "0 4px 20px 0 rgba(90,100,140,0.04)",
      border: "1.5px solid #e0e6ea",
      padding: "24px 20px 18px 20px",
      margin: "18px 0",
      maxWidth: 680,
      fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
    }}
  >
    <h2 style={{
      marginTop: 0,
      fontSize: 19,
      fontWeight: 700,
      letterSpacing: 1,
      marginBottom: 12,
    }}>就業規則</h2>
    <table
      border={0}
      cellPadding={0}
      cellSpacing={0}
      style={{
        width: "100%",
        borderRadius: 14,
        overflow: "hidden",
        borderCollapse: "separate",
        borderSpacing: 0,
        boxShadow: "0 0 0 1.5px #e0e6ea",
        background: "#fafdff",
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
      }}
    >
      <thead>
        <tr style={{ background: "#f1f6ff" }}>
          <th style={{ minWidth: 90, fontWeight: 600, fontSize: 15, border: 0, padding: "8px 10px" }}></th>
          <th style={{ fontWeight: 600, fontSize: 15, border: 0, padding: "8px 10px" }}>１週間の休み</th>
          <th style={{ fontWeight: 600, fontSize: 15, border: 0, padding: "8px 10px" }}>最大連続勤務日数</th>
          <th style={{ fontWeight: 600, fontSize: 15, border: 0, padding: "8px 10px" }}>１か月の最低就業日数</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(workConstraints).map(([typeKey, constValue]) => (
          <tr key={typeKey}>
            <td style={{
              minWidth: 90,
              fontWeight: 500,
              padding: "8px 10px",
              background: "#f7f8fa",
              borderRadius: "10px 0 0 10px",
              fontSize: 15,
              letterSpacing: 0.2,
            }}>{TYPE_LABELS[typeKey] ?? typeKey}</td>
            {(["weekly_days_off", "max_consecutive_days", "min_monthly_workdays"] as (keyof WorkConstraint)[]).map(field => (
              <td key={field} style={{
                padding: "6px 10px",
                background: "#fff",
                borderRadius: field === "min_monthly_workdays" ? "0 10px 10px 0" : "",
              }}>
                <input
                  type="number"
                  value={constValue[field]}
                  style={{
                    width: "100%",
                    minWidth: 0,
                    maxWidth: 52,
                    boxSizing: "border-box",
                    padding: "3px 4px",
                    fontSize: "14px",
                    textAlign: "center",
                    border: "1.2px solid #bbb",
                    borderRadius: 6,
                    background: "#fafbfc",
                    fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
                  }}
                  onChange={e =>
                    onChange(typeKey as keyof WorkConstraints, field, Number(e.target.value))
                  }
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default WorkConstraintsTable;
