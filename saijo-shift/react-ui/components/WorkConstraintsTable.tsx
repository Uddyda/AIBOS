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
        background: "#fff",
        borderRadius: 16,
        boxShadow: "0 4px 16px #0002",
        padding: "18px 24px",
        margin: "12px 0",
        maxWidth: 600,
        overflow: "auto"
    }}
    >
    <h2 style={{ marginTop: 0, fontSize: 17, fontWeight: 700, letterSpacing: 1 }}>就業規則</h2>
    <table
        border={0}
        cellPadding={0}
        cellSpacing={0}
        style={{
        width: "100%",
        borderRadius: 10,
        overflow: "hidden",
        borderCollapse: "separate",
        borderSpacing: 0,
        boxShadow: "0 0 0 1px #ddd",
        background: "#fcfcfe"
        }}
    >
        <thead>
        <tr style={{ background: "#f7f8fa" }}>
            <th style={{ minWidth: 90, fontWeight: 600, fontSize: 14, border: 0, padding: "8px 8px" }}></th>
            <th style={{ fontWeight: 600, fontSize: 14, border: 0, padding: "8px 8px" }}>１週間の休み</th>
            <th style={{ fontWeight: 600, fontSize: 14, border: 0, padding: "8px 8px" }}>最大連続勤務日数</th>
            <th style={{ fontWeight: 600, fontSize: 14, border: 0, padding: "8px 8px" }}>１か月の最低就業日数</th>
        </tr>
        </thead>
        <tbody>
        {Object.entries(workConstraints).map(([typeKey, constValue]) => (
            <tr key={typeKey}>
            <td style={{ minWidth: 90, fontWeight: 500, padding: "8px 8px", background: "#f7f8fa" }}>{TYPE_LABELS[typeKey] ?? typeKey}</td>
            {(["weekly_days_off", "max_consecutive_days", "min_monthly_workdays"] as (keyof WorkConstraint)[]).map(field => (
                <td key={field} style={{ padding: "6px 8px", background: "#fff" }}>
                <input
                    type="number"
                    value={constValue[field]}
                    style={{
                    width: 38,
                    minWidth: 0,
                    maxWidth: 48,
                    boxSizing: "border-box",
                    padding: "3px 4px",
                    fontSize: "13px",
                    textAlign: "center",
                    border: "1px solid #bbb",
                    borderRadius: 6,        // ← 丸み
                    background: "#fafbfc"
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
