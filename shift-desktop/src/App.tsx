import { useState, useEffect } from "react";
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

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:3001";
const api = (path: string) => `${API_BASE}${path}`;

function App() {
  // ① シフトデータの状態
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

  // ② ステート一覧
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [saveFilename, setSaveFilename] = useState<string>("");
  const [requirementOrder, setRequirementOrder] = useState<string[]>(Object.keys(data.daily_requirements));
  const [rolesOrder, setRolesOrder] = useState<string[]>(Object.keys(data.roles));
  const [csvTargetFile, setCsvTargetFile] = useState<string>("");
  const [csvExporting, setCsvExporting] = useState<boolean>(false);
  const [_, setCsvUrls] = useState<null | {
    shift: string, summary: string, workDays: string
  }>(null);
  const [zipUrl, setZipUrl] = useState<string | null>(null);
  const [zipFileName, setZipFileName] = useState<string | null>(null);
  const [shiftDirs, setShiftDirs] = useState<{ dirName: string, mtime: string }[]>([]);
  const [showShiftList, setShowShiftList] = useState(false);
  

  // ④ 起動時にファイル一覧を取得
  useEffect(() => {
    fetch(api("/api/list-files"))
      .then((res) => res.json())
      .then((files: string[]) => {
        setFileList(files);
      })
      .catch((err) => {
        console.error("ファイル一覧取得失敗:", err);
      });
  }, []);

  useEffect(() => {
    fetch(api("/api/list-shift-dirs"))
      .then((res) => res.json())
      .then((dirs) => {
        setShiftDirs(dirs);
      })
      .catch((err) => {
        console.error("shiftディレクトリ一覧取得失敗:", err);
      });
  }, []);
  // 日時フォーマット用
  const formatDate = (isoString:string) => {
    const d = new Date(isoString);
    return d.toLocaleString("ja-JP", { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  // ⑤ ファイル読み込み
  const handleLoadFile = async () => {
    if (!selectedFile) {
      alert("読み込むファイルを選択してください");
      return;
    }
    try {
      console.log("run-python fetch開始");
      const res = await fetch(
        api(`/api/load-json?filename=${selectedFile}`)
      );
      console.log("run-python fetchレスポンス", res);
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

      if (loadedData.requirementOrder) {
        setRequirementOrder(loadedData.requirementOrder);
      } else {
        setRequirementOrder(Object.keys(loadedData.daily_requirements));
      }

      if (loadedData.rolesOrder) {
        setRolesOrder(loadedData.rolesOrder);
      } else {
        setRolesOrder(Object.keys(loadedData.roles));
      }

      alert(`${selectedFile}.json を読み込みました`);
    } catch (err) {
      console.error("読み込みエラー:", err);
      alert("読み込みエラーです");
    }
  };

  // ⑥ ファイル保存と削除
  const handleSaveFile = async () => {
    if (!saveFilename) {
      alert("ファイル名を入力してください");
      return;
    }
    try {
      const orderedRoles: { [key: string]: { type: string; count: number } } = {};
      rolesOrder.forEach(key => {
        if (data.roles[key]) orderedRoles[key] = data.roles[key];
      });
      const orderedDailyRequirements: { [key: string]: DailyRequirement } = {};
      const orderedRoleCapability: { [key: string]: { primary: string[]; secondary: string[]; third?: string[] } } = {};
      requirementOrder.forEach(key => {
        if (data.daily_requirements[key]) orderedDailyRequirements[key] = data.daily_requirements[key];
        if (data.role_capability[key]) orderedRoleCapability[key] = data.role_capability[key];
      });

      const dataToSave = {
        ...data,
        roles: orderedRoles,
        daily_requirements: orderedDailyRequirements,
        role_capability: orderedRoleCapability,
        rolesOrder,
        requirementOrder,
      };

      const res = await fetch(
        api(`/api/save-json?filename=${saveFilename}&key=normal`),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dataToSave),
        }
      );
      if (res.ok) {
        alert(`${saveFilename}.json として保存しました！`);
        try {
          const updatedList = await fetch("http://localhost:3001/api/list-files").then(r => r.json());
          setFileList(updatedList);
        } catch (e) {
          console.error("[frontend] refresh list failed", e); // ←追加
        }
        setSaveFilename("");
      } else {
        alert("保存に失敗しました。");
      }
    } catch (err) {
      console.error(err);
      alert("エラーが発生しました。");
    }
  };

  const handleDeleteFile = async (filename: string) => {
    if (!window.confirm(`${filename}.json を削除しますか？`)) return;
    try {
      const res = await fetch(api(`/api/delete-json?filename=${filename}`), {
        method: "DELETE",
      });
      if (res.ok) {
        alert(`${filename}.json を削除しました`);
        // 再取得
        const updatedList = await fetch(api("/api/list-files")).then((r) => r.json());
        setFileList(updatedList);
        setSelectedFile(""); // 選択も解除
        setCsvTargetFile(""); // csv出力対象も解除
      } else {
        alert("削除に失敗しました");
      }
    } catch (err) {
      console.error("削除エラー:", err);
      alert("削除エラーです");
    }
  };

  const handleOverwriteFile = async () => {
    // ファイルが選択されていない場合は警告
    if (!selectedFile) {
      alert("上書き保存するファイルを選択してください");
      return;
    }
  
    // ここ以降はhandleSaveFileと同じ！
    try {
      const orderedRoles: { [key: string]: { type: string; count: number } } = {};
      rolesOrder.forEach(key => {
        if (data.roles[key]) orderedRoles[key] = data.roles[key];
      });
      const orderedDailyRequirements: { [key: string]: DailyRequirement } = {};
      const orderedRoleCapability: { [key: string]: { primary: string[]; secondary: string[]; third?: string[] } } = {};
      requirementOrder.forEach(key => {
        if (data.daily_requirements[key]) orderedDailyRequirements[key] = data.daily_requirements[key];
        if (data.role_capability[key]) orderedRoleCapability[key] = data.role_capability[key];
      });

      const dataToSave = {
        ...data,
        roles: orderedRoles,
        daily_requirements: orderedDailyRequirements,
        role_capability: orderedRoleCapability,
        rolesOrder,
        requirementOrder,
      };

      const res = await fetch(
        api(`/api/save-json?filename=${selectedFile}&key=normal`), // ←ここをselectedFileに！
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dataToSave),
        }
      );
      if (res.ok) {
        alert(`${selectedFile}.json を上書き保存しました！`); // ここもselectedFile
        const updatedList = await fetch(
          api("/api/list-files")
        ).then((r) => r.json());
        setFileList(updatedList);
        // setSaveFilename(""); ← これは上書き時は不要
      } else {
        alert("上書き保存に失敗しました。");
      }
    } catch (err) {
      console.error(err);
      alert("エラーが発生しました。");
    }
  };
  
  

  // ⑦ 役職の編集ハンドラ
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

  const handleAddRole = (roleKey: string, type: "employee" | "part_timer") => {
    setData(prev => ({
      ...prev,
      roles: {
        ...prev.roles,
        [roleKey]: { type, count: 1 }
      }
    }));
    setRolesOrder(prev => prev.includes(roleKey) ? prev : [...prev, roleKey]);
  };

  const handleDeleteRole = (roleKey: string) => {
    setData(prev => {
      const newRoles = { ...prev.roles };
      delete newRoles[roleKey];
  
      const newRoleCap = { ...prev.role_capability };
      // --- ここをprimary/secondaryのみで回す ---
      const levels: Array<'primary' | 'secondary'> = ['primary', 'secondary'];
      Object.keys(newRoleCap).forEach(capKey => {
        levels.forEach(level => {
          if (newRoleCap[capKey][level]) {
            newRoleCap[capKey][level] = newRoleCap[capKey][level].filter((v: string) => v !== roleKey);
          }
        });
      });
  
      return { ...prev, roles: newRoles, role_capability: newRoleCap };
    });
    setRolesOrder(prev => prev.filter(key => key !== roleKey));
  };

  // 未使用の役職を取得
  const getUnusedRoles = () => {
    const usedSet = new Set<string>();
    const levels: Array<'primary' | 'secondary'> = ['primary', 'secondary'];
    Object.values(data.role_capability).forEach(capObj => {
      levels.forEach(level => {
        if (capObj[level]) {
          capObj[level].forEach((r: string) => usedSet.add(r));
        }
      });
    });
    return Object.keys(data.roles).filter(roleKey => !usedSet.has(roleKey));
  };
  const unusedRoles = getUnusedRoles(); 
  

  // ⑧ Daily Requirements の編集ハンドラ
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

  const handleAddDailyRequirement = (key: string) => {
    if (data.daily_requirements[key]) return;
    setData(prev => ({
      ...prev,
      daily_requirements: {
        ...prev.daily_requirements,
        [key]: { normal_min: 1, normal_max: 1, friend_min: 1, friend_max: 1 }
      },
      role_capability: {
        ...prev.role_capability,
        [key]: { primary: [], secondary: [], third: [] }
      }
    }));
    setRequirementOrder(prev => [...prev, key]);
  };

  const handleDeleteDailyRequirement = (key: string) => {
    setData(prev => {
      const newReqs = { ...prev.daily_requirements };
      delete newReqs[key];
      const newRoleCaps = { ...prev.role_capability };
      delete newRoleCaps[key];
      return {
        ...prev,
        daily_requirements: newReqs,
        role_capability: newRoleCaps
      };
    });
    setRequirementOrder(prev => prev.filter(k => k !== key));
  };

  // ⑨ Role Capability の編集ハンドラ (DnD用)
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
  ): boolean => {
    let duplicate = false;
    setData((prev) => {
      const arr = prev.role_capability[capKey][level];
      if (arr.includes(value)) {
        duplicate = true;
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
    return duplicate;
  };

  // ⑩ Work Constraints の編集
  const handleWorkConstraintsChange = (
    typeKey: keyof WorkConstraints,
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

  // ⑫ 実行ボタン：define.jsonへコピー→計算→DLリンク
  const handleRunWithDefineCopy = async () => {
    console.log("実行ボタンが押された");

    setCsvExporting(true);
    setCsvUrls(null);
    if (!csvTargetFile) {
      alert("CSVを出力するjsonファイルを選択してください");
      setCsvExporting(false);
      return;
    }
    try {
      // 1. 選択ファイルの内容を取得
      const getRes = await fetch(
        api(`/api/load-json?filename=${csvTargetFile}`)
      );
      if (!getRes.ok) {
        alert("jsonの読み込みに失敗しました");
        setCsvExporting(false);
        return;
      }
      const fileData = await getRes.json();

      // 2. define.json として保存
      const saveRes = await fetch(
        api(`/api/save-json?filename=define&key=define`), // define.jsonとして保存)
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(fileData),
        }
      );
      if (!saveRes.ok) {
        alert("define.json として保存に失敗しました。");
        setCsvExporting(false);
        return;
      }

      // 3. python計算（run-python, define.json使用）
      const runRes = await fetch(api("/api/run-python"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: csvTargetFile }), // ←ここは動的なjson名でOK
      });
      if (runRes.ok) {
        const { zipFileName, zipUrl } = await runRes.json();
        setZipFileName(zipFileName);
        setZipUrl(zipUrl);
      } else {
        alert("CSV作成に失敗しました");
      }
    } catch (err) {
      alert("サーバーに接続できませんでした");
      console.error(err);
    }
      setCsvExporting(false);
  };

  // =========================
  // 表示
  // =========================
  return (
    <div style={{ margin: "20px" }}>
      <h1>シフト作成ツール</h1>

      {/* CSV出力エリア */}
      <section style={{ border: "1px solid #82c5fc", padding: 10, marginBottom: 24 }}>
        <h2>CSV出力（実行）</h2>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <select
            value={csvTargetFile}
            onChange={e => setCsvTargetFile(e.target.value)}
            style={{ minWidth: 160 }}
          >
            <option value="">--出力するjsonファイルを選択--</option>
            {fileList.map(f => (
              <option key={f} value={f}>{f}.json</option>
            ))}
          </select>
          <button
            onClick={handleRunWithDefineCopy}
            disabled={csvExporting}
            style={{
              padding: "6px 22px",
              borderRadius: 8,
              background: "linear-gradient(90deg,#8eefff,#b4b1ff)",
              color: "#224",
              fontWeight: 600,
              fontSize: 16,
              border: "none",
              cursor: csvExporting ? "wait" : "pointer"
            }}
          >
            {csvExporting ? "計算中..." : "実行"}
          </button>
        </div>
        {zipUrl && zipFileName && (
          <div style={{ marginTop: 18 }}>
            <b>CSV出力完了：</b><br />
            <a href={api(`${zipUrl}`)} download={zipFileName}>
              作成したシフトをダウンロード
            </a>
            <br />
          </div>
        )}

        <div style={{ marginTop: 18 }}>
              <button
                onClick={() => setShowShiftList(v => !v)}
                style={{
                  background: "linear-gradient(90deg,#c1d0ff,#e0ffe0)",
                  color: "#224",
                  fontWeight: 600,
                  fontSize: 16,
                  border: "none",
                  borderRadius: 8,
                  padding: "6px 22px",
                  cursor: "pointer"
                }}
              >
                過去のダウンロードリンクはこちら
              </button>
              {showShiftList && (
                <div style={{ marginTop: 16 }}>
                  <b>過去のシフト出力（最大10件）</b>
                  <ul>
                    {shiftDirs.length === 0 && <li>まだ出力履歴がありません</li>}
                    {shiftDirs.map(({ dirName, mtime }) => (
                      <li key={dirName} style={{ margin: "8px 0" }}>
                        <a
                          href={api(`/download_zip/${dirName}`)}
                          download={`${dirName}.zip`}
                          style={{ marginRight: 16 }}
                        >
                          {dirName}.zip
                        </a>
                        <span style={{ color: "#888", fontSize: 14 }}>
                          （作成日時: {formatDate(mtime)}）
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
      </section>

      {/* ファイル操作エリア */}
      <section
        style={{ border: "1px solid #ccc", padding: 10, marginBottom: 20 }}
      >
        <h2>ファイル操作</h2>
        <div style={{ marginBottom: 10 }}>
          <label>新たに名前を指定して保存: </label>
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
        <div>
          <label>ファイルの選択: </label>
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
          {/* ここが「上書き保存」ボタン！ */}
          {selectedFile && (
            <button
              onClick={handleOverwriteFile}
              style={{
                marginLeft: 8,
                padding: "6px 22px",
                borderRadius: 8,
                background: "linear-gradient(90deg,#ffe48e,#b1ffb1)", // 黄緑グラデ
                color: "#224",
                fontWeight: 600,
                fontSize: 16,
                border: "none",
                cursor: "pointer",
                transition: "background 0.2s"
              }}
            >
              上書き保存
            </button>
          )}
          {/* 削除ボタン */}
          {selectedFile && (
            <button
              onClick={() => handleDeleteFile(selectedFile)}
              style={{
                marginLeft: 8,
                padding: "6px 22px",
                borderRadius: 8,
                background: "linear-gradient(90deg,#ff8e8e,#ffd1b1)", // 赤系グラデ推奨
                color: "#224",
                fontWeight: 600,
                fontSize: 16,
                border: "none",
                cursor: "pointer",
                transition: "background 0.2s"
              }}
            >
              削除
            </button>
          )}
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
        <div style={{ flex: 1 }}>
          <h2>役職一覧</h2>
          <RoleListDnD
            roles={data.roles}
            order={rolesOrder}
            onOrderChange={setRolesOrder}
            onChangeRole={handleRoleChange}
            onAddRole={handleAddRole}
            onDeleteRole={handleDeleteRole}
          />
        </div>
        <div style={{ flex: 1 }}>
          <DailyRequirementsTable
            dailyRequirements={data.daily_requirements}
            order={requirementOrder}
            onOrderChange={setRequirementOrder}
            onChange={handleDailyRequirementChange}
            onAdd={handleAddDailyRequirement}
            onDelete={handleDeleteDailyRequirement}
          />
        </div>
      </div>

      {/* Role Capability セクション（DnD UI） */}
      <section style={{ marginBottom: 20 }}>
        <h2>割り当て可能な職種
        {unusedRoles.length > 0 && unusedRoles.map(role => (
          <span key={role} style={{
            color: "#e22",
            fontSize: 14,
            fontWeight: 600,
            marginLeft: 10,
            background: "#fff7f7",
            borderRadius: 6,
            padding: "3px 10px"
          }}>
            {role}が使われていません
          </span>
        ))}
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 20,
            alignItems: "flex-start"
          }}
        >
          {requirementOrder.map(capKey => (
            data.role_capability[capKey] && (
              <RoleCapabilityDnD
                key={capKey}
                capKey={capKey}
                capability={data.role_capability[capKey]}
                roles={data.roles}
                rolesOrder={rolesOrder} 
                onUpdate={(level, arr) => handleRoleCapabilityDnDUpdate(capKey, level, arr)}
                onEdit={(level, index, value) => handleRoleCapabilityEdit(capKey, level, index, value)}
                onDelete={(level, index) => handleRoleCapabilityDelete(capKey, level, index)}
                onAdd={(level, value) => handleRoleCapabilityAdd(capKey, level, value)}
              />
            )
          ))}
        </div>
      </section>

      {/* Work Constraints セクション */}
      <WorkConstraintsTable
        workConstraints={data.work_constraints}
        onChange={handleWorkConstraintsChange}
      />

      {/* JSON 出力プレビュー */}
      <section>
        <h2>生成される JSON</h2>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </section>
    </div>
  );
}

export default App;
