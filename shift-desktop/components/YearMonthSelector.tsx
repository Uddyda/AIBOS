import React from "react";

interface YearMonthSelectorProps {
  onYearChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onMonthChange: (month: string, isChecked: boolean) => void;
  months: string[];          // ★YYYYMM（6桁）で受け取ることを想定
  isAllSelected: boolean;
  toggleSelectAll: () => void;
  year: number; // 親コンポーネントから渡された年度（西暦）
}

const YearMonthSelector: React.FC<YearMonthSelectorProps> = ({
  onYearChange,
  onMonthChange,
  months,
  isAllSelected,
  toggleSelectAll,
  year,
}) => {
  // 年度のバリデーション（表示制御）
  const [isYearValid, setIsYearValid] = React.useState<boolean>(() => {
    return /^\d{4}$/.test(String(year));
  });

  React.useEffect(() => {
    setIsYearValid(/^\d{4}$/.test(String(year)));
  }, [year]);

  // 年度入力変更時
  const handleYearChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputYear = e.target.value;
    onYearChange(e); // 親へ通知（親がyearを更新）

    setIsYearValid(/^\d{4}$/.test(inputYear));
  };

  // ラベル「YYYY年M月」→ 値「YYYYMM」へ変換
  const labelToYYYYMM = (label: string): string | null => {
    const m = label.match(/^(\d{4})年(\d{1,2})月$/);
    if (!m) return null;
    const y = parseInt(m[1], 10);
    const mo = parseInt(m[2], 10);
    if (mo < 1 || mo > 12) return null;
    return `${y}${String(mo).padStart(2, "0")}`;
  };

  // 表示用のラベル配列を作成（当該年度 4〜12月、翌年度 1〜3月）
  const currentYear = year;
  const nextYear = currentYear + 1;

  const currentYearLabels = Array.from({ length: 9 }, (_, i) => `${currentYear}年${i + 4}月`);
  const nextYearLabels = Array.from({ length: 3 }, (_, i) => `${nextYear}年${i + 1}月`);

  // チェック状態の算出：months は YYYYMM（6桁）想定
  const isCheckedByLabel = (label: string): boolean => {
    const val = labelToYYYYMM(label);
    if (!val) return false;
    return months.includes(val);
    // ※ months は「YYYYMM」の配列を前提にしています（親側で保持）
  };

  // チェック変更時のハンドラ：親には YYYYMM を渡す
  const handleCheckByLabel = (label: string, checked: boolean) => {
    const val = labelToYYYYMM(label);
    if (!val) return;
    onMonthChange(val, checked);
  };

  return (
    <div
      style={{
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        background: "#fff9e6",
        borderRadius: 18,
        padding: "10px 18px 16px 18px",
        boxShadow: "0 4px 20px 0 rgba(90,100,140,0.04)",
        border: "1.5px solid #e0e6ea",
        margin: "0 auto",
        maxWidth: 1200,
      }}
    >
      <h2 style={{ fontWeight: 600, fontSize: 20, marginBottom: 12 }}>
        年度指定と月選択
      </h2>

      <label
        style={{
          fontSize: 15,
          marginBottom: 8,
          display: "inline-block",
        }}
      >
        年度 (西暦4桁):
      </label>
      <input
        type="number"
        value={year}
        onChange={handleYearChange}
        placeholder="例: 2025"
        style={{
          fontSize: 16,
          border: "1px solid #e0e6ea",
          borderRadius: 6,
          padding: "6px 12px",
          background: "#fff",
          outline: "none",
          width: "8%",
          marginBottom: "16px",
        }}
      />

      {isYearValid && (
        <div>
          <h3 style={{ fontSize: 18, marginBottom: 10 }}>月を選択</h3>

          <div
            style={{
              border: "2px solid #82c5fc",
              padding: "10px",
              borderRadius: "8px",
              marginBottom: "15px",
            }}
          >
            {/* 当年（4月〜12月） */}
            <div>
              <h4 style={{ margin: "0 0 10px 0" }}>{currentYear}年</h4>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {currentYearLabels.map((label) => (
                  <div key={label} style={{ display: "flex", alignItems: "center" }}>
                    <input
                      type="checkbox"
                      checked={isCheckedByLabel(label)}
                      onChange={(e) => handleCheckByLabel(label, e.target.checked)}
                      style={{ marginRight: 8 }}
                    />
                    <label>{label}</label>
                  </div>
                ))}
              </div>
            </div>

            {/* 翌年（1月〜3月） */}
            <div>
              <h4 style={{ margin: "16px 0 10px 0" }}>{nextYear}年</h4>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {nextYearLabels.map((label) => (
                  <div key={label} style={{ display: "flex", alignItems: "center" }}>
                    <input
                      type="checkbox"
                      checked={isCheckedByLabel(label)}
                      onChange={(e) => handleCheckByLabel(label, e.target.checked)}
                      style={{ marginRight: 8 }}
                    />
                    <label>{label}</label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={toggleSelectAll}
            style={{
              fontSize: 15,
              borderRadius: 7,
              background: "linear-gradient(90deg, #a7e2ff, #c3c1ff)",
              color: "#0a2463",
              fontWeight: 600,
              padding: "6px 30px",
              border: "none",
              cursor: "pointer",
              boxShadow: "0 1px 6px 0 rgba(140,180,255,0.07)",
              transition: "background 0.2s",
              whiteSpace: "nowrap",
              marginTop: "16px",
            }}
          >
            {isAllSelected ? "選択解除" : "全選択"}
          </button>
        </div>
      )}
    </div>
  );
};

export default YearMonthSelector;
