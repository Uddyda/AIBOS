import { useState, useEffect } from "react";
import type { ChangeEvent } from "react";
import type {
  ShiftConfig,
  DailyRequirement,
  WorkConstraints,
  WorkConstraint,
} from "./types/shift"; // 事前に定義した型

function App() {
  // =========================
  // ① シフトデータの状態
  // =========================
  const [data, setData] = useState<ShiftConfig>({
    year: 2025,
    roles: {
      統括: { type: "employee", count: 1 },
      副統括: { type: "employee", count: 1 },
      火葬員: { type: "employee", count: 6 },
      清掃員: { type: "employee", count: 4 },
      売店従業員: { type: "employee", count: 3 },
      霊柩運送員: { type: "employee", count: 3 },
      パート長: { type: "part_timer", count: 4 },
      パート短: { type: "part_timer", count: 4 },
    },
    daily_requirements: {
      責任者: { normal_min: 1, normal_max: 1, friend_min: 1, friend_max: 1 },
      事務: { normal_min: 1, normal_max: 2, friend_min: 1, friend_max: 2 },
      囲炉裏: { normal_min: 1, normal_max: 1, friend_min: 1, friend_max: 1 },
      人火葬: { normal_min: 6, normal_max: 7, friend_min: 5, friend_max: 5 },
      動物火葬: { normal_min: 1, normal_max: 2, friend_min: 1, friend_max: 2 },
      運送: { normal_min: 2, normal_max: 2, friend_min: 2, friend_max: 2 },
      清掃: { normal_min: 2, normal_max: 2, friend_min: 2, friend_max: 2 },
      売店: { normal_min: 2, normal_max: 2, friend_min: 2, friend_max: 2 },
    },
    role_capability: {
      責任者: {
        primary: ["統括"],
        secondary: ["副統括"],
        third: [],
      },
      事務: {
        primary: ["事務員"],
        secondary: ["副統括"],
        third: [],
      },
      囲炉裏: {
        primary: ["火葬業務統括"],
        secondary: ["火葬業務副統括"],
        third: [],
      },
      人火葬: {
        primary: ["火葬員"],
        secondary: ["パート長", "パート短"],
        third: [],
      },
      動物火葬: {
        primary: ["火葬員"],
        secondary: ["パート長", "パート短"],
        third: [],
      },
      運送: {
        primary: ["霊柩運送員"],
        secondary: [],
        third: [],
      },
      清掃: {
        primary: ["清掃員"],
        secondary: [],
        third: [],
      },
      売店: {
        primary: ["売店従業員"],
        secondary: [],
        third: [],
      },
    },

    work_constraints: {
      employee: {
        weekly_days_off: 2,
        max_consecutive_days: 7,
        min_monthly_workdays: 20,
      },
      part_timer: {
        weekly_days_off: 0,
        max_consecutive_days: 3,
        min_monthly_workdays: 0,
      },
      dummy: {
        weekly_days_off: 0,
        max_consecutive_days: 31,
        min_monthly_workdays: 0,
      },
    },
  });

  // =========================
  // ② ファイル一覧の状態
  // =========================
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>(""); // 選択中のファイル名(読込用)
  const [saveFilename, setSaveFilename] = useState<string>(""); // 新規保存用

  // =========================
  // ③ 従業員選択用リスト
  // =========================

  // === (A) どの RoleCapability に追加するかを選ぶために capKey を state で保持してもOK。
  //     ここでは「各capKeyブロック内で追加ボタンを押す→select で選ぶUI」を作る例にします。

  // =========================
  // ④ 起動時にファイル一覧を取得
  // =========================
  useEffect(() => {
    fetch("http://localhost:3001/api/list-files")
      .then((res) => res.json())
      .then((files: string[]) => {
        setFileList(files);
      })
      .catch((err) => {
        console.error("ファイル一覧取得失敗:", err);
      });
  }, []);

  // =========================
  // ⑤ ファイル一覧の <select> で読み込む
  // =========================
  const handleLoadFile = async () => {
    if (!selectedFile) {
      alert("読み込むファイルを選択してください");
      return;
    }
    try {
      const res = await fetch(
        `http://localhost:3001/api/load-json?filename=${selectedFile}`
      );
      if (!res.ok) {
        if (res.status === 404) {
          alert("指定ファイルは存在しません");
        } else {
          alert("読み込みに失敗しました");
        }
        return;
      }
      const loadedData = await res.json();
      setData(loadedData);
      alert(`${selectedFile}.json を読み込みました`);
    } catch (err) {
      console.error("読み込みエラー:", err);
      alert("読み込みエラーです");
    }
  };

  // =========================
  // ⑥ 新規ファイル名を指定して保存
  // =========================
  const handleSaveFile = async () => {
    if (!saveFilename) {
      alert("ファイル名を入力してください");
      return;
    }
    try {
      const res = await fetch(
        `http://localhost:3001/api/save-json?filename=${saveFilename}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );
      if (res.ok) {
        alert(`${saveFilename}.json として保存しました！`);
        // 保存後にファイル一覧を再取得
        const updatedList = await fetch(
          "http://localhost:3001/api/list-files"
        ).then((r) => r.json());
        setFileList(updatedList);
        setSaveFilename(""); // 入力欄リセット
      } else {
        alert("保存に失敗しました。");
      }
    } catch (err) {
      console.error(err);
      alert("エラーが発生しました。");
    }
  };

  // =========================
  // ⑦ 役職の編集ハンドラ
  // =========================
  const handleRoleChange = (
    roleKey: string,
    field: "type" | "count",
    value: string | number
  ) => {
    setData((prev) => ({
      ...prev,
      roles: {
        ...prev.roles,
        [roleKey]: {
          ...prev.roles[roleKey],
          [field]: value,
        },
      },
    }));
  };

  const handleAddRole = () => {
    // 1) 役職名を尋ねる
    const newRoleName = window.prompt("追加する役職名を入力してください:");
    if (!newRoleName) return;

    // 2) typeを尋ねる
    const typeInput = window.prompt(
      "社員なら employee、パートなら part_timer と入力してください:",
      "employee"
    );
    if (!typeInput) return;
    // 入力が "part_timer" かどうかで分岐 (それ以外は社員扱い)
    const newRoleType = typeInput === "part_timer" ? "part_timer" : "employee";

    setData((prev) => ({
      ...prev,
      roles: {
        ...prev.roles,
        // 新しく追加
        [newRoleName]: {
          type: newRoleType,
          count: 1,
        },
      },
    }));
  };

  // =========================
  // ⑧ Daily Requirements の編集ハンドラ
  // =========================
  const handleDailyRequirementChange = (
    reqKey: string,
    field: keyof DailyRequirement,
    value: string
  ) => {
    setData((prev) => ({
      ...prev,
      daily_requirements: {
        ...prev.daily_requirements,
        [reqKey]: {
          ...prev.daily_requirements[reqKey],
          [field]: Number(value),
        },
      },
    }));
  };

  // =========================
  // ⑨ Role Capability の編集ハンドラ
  // =========================

  // (A) テキスト変更
  const handleRoleCapabilityChange = (
    capKey: string,
    level: "primary" | "secondary",
    index: number,
    value: string
  ) => {
    setData((prev) => {
      const capObj = prev.role_capability[capKey];
      const oldArr = capObj[level];
      const newArr = [...oldArr];
      newArr[index] = value;

      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: {
            ...capObj,
            [level]: newArr,
          },
        },
      };
    });
  };

  // (B) 要素削除
  const handleDeleteCapability = (
    capKey: string,
    level: "primary" | "secondary",
    index: number
  ) => {
    setData((prev) => {
      const capObj = prev.role_capability[capKey];
      const oldArr = capObj[level];
      const newArr = [...oldArr];
      newArr.splice(index, 1);

      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: {
            ...capObj,
            [level]: newArr,
          },
        },
      };
    });
  };

  // (C) プルダウン追加
  const handleSelectEmployee = (
    e: ChangeEvent<HTMLSelectElement>,
    capKey: string,
    level: "primary" | "secondary"
  ) => {
    const selectedEmp = e.target.value;
    if (!selectedEmp) return;

    const curArr = data.role_capability[capKey][level];
    if (curArr.includes(selectedEmp)) {
      alert("既に追加されています。");
      return;
    }

    setData((prev) => {
      const capObj = prev.role_capability[capKey];
      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: {
            ...capObj,
            [level]: [...capObj[level], selectedEmp],
          },
        },
      };
    });
  };

  // =========================
  // ⑩ Work Constraints の編集
  // =========================
  const handleWorkConstraintsChange = (
    typeKey: keyof WorkConstraints,
    field: keyof WorkConstraint,
    value: string
  ) => {
    setData((prev) => ({
      ...prev,
      work_constraints: {
        ...prev.work_constraints,
        [typeKey]: {
          ...prev.work_constraints[typeKey],
          [field]: Number(value),
        },
      },
    }));
  };

  // =========================
  // 表示
  // =========================
  return (
    <div style={{ margin: "20px" }}>
      <h1>シフトツール (TypeScript版)</h1>

      {/* 1) ファイル操作エリア */}
      <section
        style={{ border: "1px solid #ccc", padding: 10, marginBottom: 20 }}
      >
        <h2>ファイル操作</h2>

        {/* (A) ファイル保存 (新規ファイル名) */}
        <div style={{ marginBottom: 10 }}>
          <label>保存ファイル名: </label>
          <input
            type="text"
            placeholder="myShift"
            value={saveFilename}
            onChange={(e) => setSaveFilename(e.target.value)}
          />
          <button onClick={handleSaveFile} style={{ marginLeft: 8 }}>
            保存
          </button>
        </div>

        {/* (B) ファイル一覧から読み込み */}
        <div>
          <label>読み込むファイル: </label>
          <select
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
          >
            <option value="">--選択してください--</option>
            {fileList.map((f) => (
              <option key={f} value={f}>
                {f}.json
              </option>
            ))}
          </select>
          <button onClick={handleLoadFile} style={{ marginLeft: 8 }}>
            読み込み
          </button>
        </div>
      </section>

      {/* 年の設定*/}
      <section style={{ marginBottom: 20 }}>
        <h2>年度指定</h2>
        <label>年度(西暦4桁): </label>
        <input
          type="number"
          value={data.year || ""}
          onChange={(e) =>
            setData((prev) => ({
              ...prev,
              year: Number(e.target.value),
            }))
          }
        />
      </section>

      {/* 2) Roles セクション */}
      <section style={{ marginBottom: 20 }}>
        <h2>役職一覧</h2>
        <button onClick={handleAddRole}>役職追加</button>
        <table border={1} cellPadding={5} style={{ marginTop: 10 }}>
          <thead>
            <tr>
              <th>役職名</th>
              <th>type</th>
              <th>count</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.roles).map(([roleKey, roleValue]) => (
              <tr key={roleKey}>
                <td>{roleKey}</td>
                <td>
                  <select
                    value={roleValue.type}
                    onChange={(e) =>
                      handleRoleChange(roleKey, "type", e.target.value)
                    }
                  >
                    <option value="employee">employee</option>
                    <option value="part_timer">part_timer</option>
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    value={roleValue.count}
                    onChange={(e) =>
                      handleRoleChange(roleKey, "count", Number(e.target.value))
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 3) Daily Requirements セクション */}
      <section style={{ marginBottom: 20 }}>
        <h2>一日に必要な人数</h2>
        <table border={1} cellPadding={5}>
          <thead>
            <tr>
              <th>キー</th>
              <th>normal_min</th>
              <th>normal_max</th>
              <th>friend_min</th>
              <th>friend_max</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.daily_requirements).map(
              ([reqKey, reqValue]) => (
                <tr key={reqKey}>
                  <td>{reqKey}</td>
                  {(
                    [
                      "normal_min",
                      "normal_max",
                      "friend_min",
                      "friend_max",
                    ] as (keyof DailyRequirement)[]
                  ).map((field) => (
                    <td key={field}>
                      <input
                        type="number"
                        value={reqValue[field]}
                        onChange={(e) =>
                          handleDailyRequirementChange(
                            reqKey,
                            field,
                            e.target.value
                          )
                        }
                      />
                    </td>
                  ))}
                </tr>
              )
            )}
          </tbody>
        </table>
      </section>

      {/* 4) Role Capability セクション */}
      <section style={{ marginBottom: 20 }}>
        <h2>割り当て可能な職種</h2>
        {Object.entries(data.role_capability).map(([capKey, capObj]) => (
          <div
            key={capKey}
            style={{ marginBottom: 20, border: "1px solid #ddd", padding: 10 }}
          >
            <h4>{capKey}</h4>

            {/* 横並びレイアウトをするコンテナ */}
            <div style={{ display: "flex", gap: "40px" }}>
              {/* Primary 一覧 */}
              <div>
                <label>Primary:</label>
                <ul>
                  {capObj.primary.map((member, idx) => (
                    <li key={idx}>
                      <input
                        type="text"
                        value={member}
                        onChange={(e) =>
                          handleRoleCapabilityChange(
                            capKey,
                            "primary",
                            idx,
                            e.target.value
                          )
                        }
                      />
                      <button
                        onClick={() =>
                          handleDeleteCapability(capKey, "primary", idx)
                        }
                      >
                        削除
                      </button>
                    </li>
                  ))}
                </ul>

                {/*
                  --- [追加] Primary への追加用セレクト ---
                  下記のように roles のキーをオプションにして select を作り、
                  onChange で handleSelectEmployee(e, capKey, "primary") を呼び出します。
                */}
                <div style={{ marginTop: 8 }}>
                  <label>追加: </label>
                  <select
                    onChange={(e) => handleSelectEmployee(e, capKey, "primary")}
                    defaultValue=""
                  >
                    <option value="">--役職を選択--</option>
                    {Object.keys(data.roles).map((roleKey) => (
                      <option key={roleKey} value={roleKey}>
                        {roleKey}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Secondary 一覧 */}
              <div>
                <label>Secondary:</label>
                <ul>
                  {capObj.secondary.map((member, idx) => (
                    <li key={idx}>
                      <input
                        type="text"
                        value={member}
                        onChange={(e) =>
                          handleRoleCapabilityChange(
                            capKey,
                            "secondary",
                            idx,
                            e.target.value
                          )
                        }
                      />
                      <button
                        onClick={() =>
                          handleDeleteCapability(capKey, "secondary", idx)
                        }
                      >
                        削除
                      </button>
                    </li>
                  ))}
                </ul>

                {/*
                  --- [追加] Secondary への追加用セレクト ---
                */}
                <div style={{ marginTop: 8 }}>
                  <label>追加: </label>
                  <select
                    onChange={(e) =>
                      handleSelectEmployee(e, capKey, "secondary")
                    }
                    defaultValue=""
                  >
                    <option value="">--役職を選択--</option>
                    {Object.keys(data.roles).map((roleKey) => (
                      <option key={roleKey} value={roleKey}>
                        {roleKey}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Third 一覧のブロックは削除（非表示） */}
          </div>
        ))}
      </section>

      {/* 5) Work Constraints セクション */}
      <section style={{ marginBottom: 20 }}>
        <h2>就業規則</h2>
        <table border={1} cellPadding={5}>
          <thead>
            <tr>
              <th>typeKey</th>
              <th>weekly_days_off</th>
              <th>max_consecutive_days</th>
              <th>min_monthly_workdays</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.work_constraints).map(
              ([typeKey, constValue]) => (
                <tr key={typeKey}>
                  <td>{typeKey}</td>
                  {(
                    [
                      "weekly_days_off",
                      "max_consecutive_days",
                      "min_monthly_workdays",
                    ] as (keyof WorkConstraint)[]
                  ).map((field) => (
                    <td key={field}>
                      <input
                        type="number"
                        value={constValue[field]}
                        onChange={(e) =>
                          handleWorkConstraintsChange(
                            typeKey as keyof WorkConstraints,
                            field,
                            e.target.value
                          )
                        }
                      />
                    </td>
                  ))}
                </tr>
              )
            )}
          </tbody>
        </table>
      </section>

      {/* 6) JSON 出力プレビュー */}
      <section>
        <h2>生成される JSON</h2>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </section>
    </div>
  );
}

export default App;
