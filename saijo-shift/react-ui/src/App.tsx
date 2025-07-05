import { useState, useEffect } from "react";
import type { ChangeEvent } from "react";
import type {
  ShiftConfig,
  DailyRequirement,
  WorkConstraints,
  WorkConstraint,
} from "../types/shift";
import RoleCapabilityDnD from "../components/RoleCapabilityDnD";
import DailyRequirementsTable from "../components/DailyRequirementsTable";
import RoleListDnD from "../components/RoleListDnD";
import WorkConstraintsTable from "../components/WorkConstraintsTable";

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
  // ② ステート一覧
  // =========================
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [saveFilename, setSaveFilename] = useState<string>("");
  const [showShiftCreate, setShowShiftCreate] = useState(false);
  const [fileForShift, setFileForShift] = useState<string>("");
  const [roleOrder, setRoleOrder] = useState<string[]>(Object.keys(data.roles));

  
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
      setRoleOrder(Object.keys(loadedData.roles)); 
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
        `http://localhost:3001/api/save-json?filename=${saveFilename}&key=normal`,
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
        setSaveFilename("");
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
  // 役職の編集ハンドラ
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

  // 役職追加ハンドラ（RoleListTable用にprops化）
  const handleAddRole = (roleKey: string, type: "employee" | "part_timer") => {
    setData(prev => ({
      ...prev,
      roles: {
        ...prev.roles,
        [roleKey]: { type, count: 1 }
      }
    }));
    setRoleOrder(prev => prev.includes(roleKey) ? prev : [...prev, roleKey]);
  };

  // =========================
  // ⑧ Daily Requirements の編集ハンドラ
  // =========================
  const handleDailyRequirementChange = (
    reqKey: string,
    field: keyof DailyRequirement,
    value: number
  ) => {
    setData((prev) => ({
      ...prev,
      daily_requirements: {
        ...prev.daily_requirements,
        [reqKey]: {
          ...prev.daily_requirements[reqKey],
          [field]: value,
        },
      },
    }));
  };

  // =========================
  // ⑨ Role Capability の編集ハンドラ (DnD用)
  // =========================
  const handleRoleCapabilityDnDUpdate = (
    capKey: string,
    level: "primary" | "secondary",
    newArr: string[]
  ) => {
    setData((prev) => ({
      ...prev,
      role_capability: {
        ...prev.role_capability,
        [capKey]: {
          ...prev.role_capability[capKey],
          [level]: newArr,
        },
      },
    }));
  };

  const handleRoleCapabilityEdit = (
    capKey: string,
    level: "primary" | "secondary",
    index: number,
    value: string
  ) => {
    setData((prev) => {
      const arr = prev.role_capability[capKey][level];
      const newArr = [...arr];
      newArr[index] = value;
      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: {
            ...prev.role_capability[capKey],
            [level]: newArr,
          },
        },
      };
    });
  };

  const handleRoleCapabilityDelete = (
    capKey: string,
    level: "primary" | "secondary",
    index: number
  ) => {
    setData((prev) => {
      const arr = prev.role_capability[capKey][level];
      const newArr = [...arr];
      newArr.splice(index, 1);
      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: {
            ...prev.role_capability[capKey],
            [level]: newArr,
          },
        },
      };
    });
  };

  const handleRoleCapabilityAdd = (
    capKey: string,
    level: "primary" | "secondary",
    value: string
  ) => {
    setData((prev) => {
      const arr = prev.role_capability[capKey][level];
      if (arr.includes(value)) {
        alert("既に追加されています。");
        return prev;
      }
      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: {
            ...prev.role_capability[capKey],
            [level]: [...arr, value],
          },
        },
      };
    });
  };

  // =========================
  // ⑩ Work Constraints の編集
  // =========================
  const handleWorkConstraintsChange = (
    typeKey: keyof WorkConstraints, // ← ここをstringからkeyof WorkConstraintsに
    field: keyof WorkConstraint,
    value: number
  ) => {
    setData(prev => ({
      ...prev,
      work_constraints: {
        ...prev.work_constraints,
        [typeKey]: {
          ...prev.work_constraints[typeKey],
          [field]: value,
        },
      },
    }));
  };

  // =========================
  // ⑪ シフト作成実行機能
  // =========================
  const handleCreateShiftFile = async () => {
    if (!fileForShift) {
      alert("コピー元のファイルを選択してください");
      return;
    }
    try {
      const readRes = await fetch(
        `http://localhost:3001/api/load-json?filename=${fileForShift}`
      );
      if (!readRes.ok) {
        alert(`ファイル ${fileForShift}.json の読み込みに失敗しました。`);
        return;
      }
      const fileData = await readRes.json();
      const saveRes = await fetch(
        `http://localhost:3001/api/save-json?filename=define&key=define`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(fileData),
        }
      );
      if (!saveRes.ok) {
        alert("define.json として保存に失敗しました。");
        return;
      }
      alert(`${fileForShift}.json をコピーして define.json を作成しました！`);
      setFileForShift("");
      setShowShiftCreate(false);
    } catch (err) {
      console.error(err);
      alert("シフト作成中にエラーが発生しました。");
    }
  };

  // =========================
  // 表示
  // =========================
  return (
    <div style={{ margin: "20px" }}>
      <h1>シフトツール (TypeScript版)</h1>

      {/* シフト作成モーダル */}
      <button
        onClick={() => setShowShiftCreate(true)}
        style={{ marginBottom: 20 }}
      >
        シフト作成
      </button>
      {showShiftCreate && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 9999,
          }}
          onClick={() => setShowShiftCreate(false)}
        >
          <div
            style={{
              backgroundColor: "#fff",
              padding: 20,
              borderRadius: 8,
              minWidth: 300,
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2>シフト作成</h2>
            <p>使用するファイルを選択してください</p>
            <select
              value={fileForShift}
              onChange={(e) => setFileForShift(e.target.value)}
              style={{ display: "block", marginBottom: 12 }}
            >
              <option value="">--ファイルを選択してください--</option>
              {fileList.map((f) => (
                <option key={f} value={f}>
                  {f}.json
                </option>
              ))}
            </select>
            <button onClick={handleCreateShiftFile} style={{ marginRight: 8 }}>
              確定
            </button>
            <button onClick={() => setShowShiftCreate(false)}>
              キャンセル
            </button>
          </div>
        </div>
      )}

      {/* 1) ファイル操作エリア */}
      <section
        style={{ border: "1px solid #ccc", padding: 10, marginBottom: 20 }}
      >
        <h2>ファイル操作</h2>
        {/* (A) ファイル保存 */}
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
        {/* (B) ファイル読み込み */}
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



      {/* 年の設定 */}
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

      <div style={{ display: "flex", gap: 40, alignItems: "flex-start" }}>
        {/* 2) Roles セクション */}
        {/* 役職一覧 */}
        <div style={{ flex: 1 }}>
          <h2>役職一覧</h2>
          <RoleListDnD
            roles={data.roles}
            roleOrder={roleOrder}
            onRoleOrderChange={setRoleOrder}
            onChangeRole={handleRoleChange}
            onAddRole={handleAddRole}
          />
        </div>
        {/* 3) Daily Requirements セクション */}
        {/* 一日に必要な人数 */}
        <div style={{ flex: 1 }}>
          <DailyRequirementsTable
            dailyRequirements={data.daily_requirements}
            onChange={handleDailyRequirementChange}
          />
        </div>
      </div>

      {/* 4) Role Capability セクション（DnD UI） */}
      <section style={{ marginBottom: 20 }}>
        <h2>割り当て可能な職種</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr", // 2列グリッド
              gap: 20,                        // カード間のスペース
              alignItems: "flex-start"
            }}
          >
        {Object.entries(data.role_capability).map(([capKey, capObj]) => (
          <RoleCapabilityDnD
            key={capKey}
            capKey={capKey}
            capability={capObj}
            roles={data.roles}
            onUpdate={(level, arr) => handleRoleCapabilityDnDUpdate(capKey, level, arr)}
            onEdit={(level, index, value) => handleRoleCapabilityEdit(capKey, level, index, value)}
            onDelete={(level, index) => handleRoleCapabilityDelete(capKey, level, index)}
            onAdd={(level, value) => handleRoleCapabilityAdd(capKey, level, value)}
          />
        ))}
        </div>
      </section>

      {/* 5) Work Constraints セクション */}
      <WorkConstraintsTable
        workConstraints={data.work_constraints}
        onChange={handleWorkConstraintsChange}
      />

      {/* 6) JSON 出力プレビュー */}
      <section>
        <h2>生成される JSON</h2>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </section>
    </div>
  );
}

export default App;
