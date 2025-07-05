import React from "react";

type DailyRequirement = {
  normal_min: number;
  normal_max: number;
  friend_min: number;
  friend_max: number;
};

type DailyRequirementsTableProps = {
  dailyRequirements: { [key: string]: DailyRequirement };
  onChange: (key: string, field: keyof DailyRequirement, value: number) => void;
};

const FIELDS: (keyof DailyRequirement)[] = [
  "normal_min",
  "normal_max",
  "friend_min",
  "friend_max"
];

const FIELD_LABELS: { [K in keyof DailyRequirement]: string } = {
  normal_min: "通常最小",
  normal_max: "通常最大",
  friend_min: "友引最小",
  friend_max: "友引最大"
};

const DailyRequirementsTable: React.FC<DailyRequirementsTableProps> = ({
  dailyRequirements,
  onChange,
}) => {
  const keys = Object.keys(dailyRequirements);

  return (
    <div>
      <h2>一日に必要な人数</h2>
        <table border={1} cellPadding={5} style={{ marginTop: 10, fontSize: "95%" }}>
        <thead>
            <tr>
            <th style={{ minWidth: 80 }}></th>
            <th style={{ minWidth: 90 }}>normal_min</th>
            <th style={{ minWidth: 90 }}>normal_max</th>
            <th style={{ minWidth: 90 }}>friend_min</th>
            <th style={{ minWidth: 90 }}>friend_max</th>
            </tr>
        </thead>
        <tbody>
            {Object.entries(dailyRequirements).map(([key, value]) => (
            <tr key={key}>
                <td style={{ fontWeight: "bold", minWidth: 80 }}>{key}</td>
                <td><input type="number" value={value.normal_min} style={{ width: 50 }} onChange={e => onChange(key, "normal_min", Number(e.target.value))} /></td>
                <td><input type="number" value={value.normal_max} style={{ width: 50 }} onChange={e => onChange(key, "normal_max", Number(e.target.value))} /></td>
                <td><input type="number" value={value.friend_min} style={{ width: 50 }} onChange={e => onChange(key, "friend_min", Number(e.target.value))} /></td>
                <td><input type="number" value={value.friend_max} style={{ width: 50 }} onChange={e => onChange(key, "friend_max", Number(e.target.value))} /></td>
            </tr>
            ))}
        </tbody>
        </table>
    </div>
  );
};

export default DailyRequirementsTable;
