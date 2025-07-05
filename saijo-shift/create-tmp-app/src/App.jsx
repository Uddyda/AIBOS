import React, { useState } from 'react';

function App() {
  // 初期値として提示されていた JSON 形式をセット
  const [data, setData] = useState({
    roles: {
      統括: { type: 'employee', count: 1 },
      副: { type: 'employee', count: 1 },
      火葬員: { type: 'employee', count: 6 },
      清掃員: { type: 'employee', count: 4 },
      売店従業員: { type: 'employee', count: 3 },
      霊柩運送員: { type: 'employee', count: 3 },
      パート長: { type: 'part_timer', count: 4 },
      パート短: { type: 'part_timer', count: 4 }
    },
    daily_requirements: {
      責: { normal_min: 1, normal_max: 1, friend_min: 1, friend_max: 1 },
      事: { normal_min: 1, normal_max: 2, friend_min: 1, friend_max: 2 },
      裏: { normal_min: 1, normal_max: 1, friend_min: 1, friend_max: 1 },
      人: { normal_min: 6, normal_max: 7, friend_min: 5, friend_max: 5 },
      動: { normal_min: 1, normal_max: 2, friend_min: 1, friend_max: 2 },
      運: { normal_min: 2, normal_max: 2, friend_min: 2, friend_max: 2 },
      清: { normal_min: 2, normal_max: 2, friend_min: 2, friend_max: 2 },
      売: { normal_min: 2, normal_max: 2, friend_min: 2, friend_max: 2 }
    },
    role_capability: {
      責: ['統括', '副'],
      事: ['事務員', '副'],
      裏: ['火葬業務統括', '火葬業務副統括'],
      人: ['火葬員', 'パート長', 'パート短'],
      動: ['火葬員', 'パート長', 'パート短'],
      運: ['霊柩運送員', '火葬員', '事務員'],
      清: ['清掃員'],
      売: ['売店従業員']
    },
    work_constraints: {
      employee: {
        weekly_days_off: 2,
        max_consecutive_days: 7,
        min_monthly_workdays: 20
      },
      part_timer: {
        weekly_days_off: 0,
        max_consecutive_days: 3,
        min_monthly_workdays: 0
      },
      dummy: {
        weekly_days_off: 0,
        max_consecutive_days: 31,
        min_monthly_workdays: 0
      }
    }
  });

  //
  // 役職 (roles) 編集ハンドラ
  //
  const handleRoleChange = (roleKey, field, value) => {
    setData((prev) => ({
      ...prev,
      roles: {
        ...prev.roles,
        [roleKey]: {
          ...prev.roles[roleKey],
          [field]: value
        }
      }
    }));
  };

  // 役職追加
  const handleAddRole = () => {
    const newRoleName = window.prompt('追加する役職名を入力してください:');
    if (!newRoleName) return;
    setData((prev) => ({
      ...prev,
      roles: {
        ...prev.roles,
        [newRoleName]: {
          type: 'employee', // デフォルトは employee
          count: 1
        }
      }
    }));
  };

  //
  // daily_requirements 編集ハンドラ
  //
  const handleDailyRequirementChange = (reqKey, field, value) => {
    setData((prev) => ({
      ...prev,
      daily_requirements: {
        ...prev.daily_requirements,
        [reqKey]: {
          ...prev.daily_requirements[reqKey],
          [field]: Number(value)
        }
      }
    }));
  };

  //
  // role_capability 編集ハンドラ
  //
  const handleRoleCapabilityChange = (capKey, index, value) => {
    setData((prev) => {
      const newArr = [...prev.role_capability[capKey]];
      newArr[index] = value;
      return {
        ...prev,
        role_capability: {
          ...prev.role_capability,
          [capKey]: newArr
        }
      };
    });
  };

  // role_capability に新規対応役職を追加
  const handleAddCapability = (capKey) => {
    const newCap = window.prompt(
      `「${capKey}」に新しく追加する対応可能な役職名を入力してください:`
    );
    if (!newCap) return;
    setData((prev) => ({
      ...prev,
      role_capability: {
        ...prev.role_capability,
        [capKey]: [...prev.role_capability[capKey], newCap]
      }
    }));
  };

  //
  // work_constraints 編集ハンドラ
  //
  const handleWorkConstraintsChange = (typeKey, field, value) => {
    setData((prev) => ({
      ...prev,
      work_constraints: {
        ...prev.work_constraints,
        [typeKey]: {
          ...prev.work_constraints[typeKey],
          [field]: Number(value)
        }
      }
    }));
  };

  //
  // JSON ダウンロード用ハンドラ
  //
  const handleDownloadJson = () => {
    const jsonString = JSON.stringify(data, null, 2); 
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'schedule_data.json'; 
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ margin: '20px' }}>
      <h1>JSON 生成 UI サンプル</h1>

      {/* Roles セクション */}
      <section style={{ marginBottom: '20px' }}>
        <h2>Roles</h2>
        <button onClick={handleAddRole}>役職追加</button>
        <table border="1" cellPadding="5" style={{ marginTop: '10px' }}>
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
                    onChange={(e) => handleRoleChange(roleKey, 'type', e.target.value)}
                  >
                    <option value="employee">employee</option>
                    <option value="part_timer">part_timer</option>
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    value={roleValue.count}
                    onChange={(e) => handleRoleChange(roleKey, 'count', Number(e.target.value))}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* daily_requirements セクション */}
      <section style={{ marginBottom: '20px' }}>
        <h2>Daily Requirements</h2>
        <table border="1" cellPadding="5">
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
            {Object.entries(data.daily_requirements).map(([reqKey, reqValue]) => (
              <tr key={reqKey}>
                <td>{reqKey}</td>
                <td>
                  <input
                    type="number"
                    value={reqValue.normal_min}
                    onChange={(e) =>
                      handleDailyRequirementChange(reqKey, 'normal_min', e.target.value)
                    }
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={reqValue.normal_max}
                    onChange={(e) =>
                      handleDailyRequirementChange(reqKey, 'normal_max', e.target.value)
                    }
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={reqValue.friend_min}
                    onChange={(e) =>
                      handleDailyRequirementChange(reqKey, 'friend_min', e.target.value)
                    }
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={reqValue.friend_max}
                    onChange={(e) =>
                      handleDailyRequirementChange(reqKey, 'friend_max', e.target.value)
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* role_capability セクション */}
      <section style={{ marginBottom: '20px' }}>
        <h2>Role Capability</h2>
        {Object.entries(data.role_capability).map(([capKey, capArray]) => (
          <div key={capKey} style={{ marginBottom: '10px' }}>
            <h4>{capKey}</h4>
            <button onClick={() => handleAddCapability(capKey)}>追加</button>
            <ul>
              {capArray.map((cap, index) => (
                <li key={index} style={{ marginBottom: '5px' }}>
                  <input
                    type="text"
                    value={cap}
                    onChange={(e) => handleRoleCapabilityChange(capKey, index, e.target.value)}
                  />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* work_constraints セクション */}
      <section style={{ marginBottom: '20px' }}>
        <h2>Work Constraints</h2>
        <table border="1" cellPadding="5">
          <thead>
            <tr>
              <th>typeKey</th>
              <th>weekly_days_off</th>
              <th>max_consecutive_days</th>
              <th>min_monthly_workdays</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.work_constraints).map(([typeKey, constValue]) => (
              <tr key={typeKey}>
                <td>{typeKey}</td>
                <td>
                  <input
                    type="number"
                    value={constValue.weekly_days_off}
                    onChange={(e) =>
                      handleWorkConstraintsChange(typeKey, 'weekly_days_off', e.target.value)
                    }
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={constValue.max_consecutive_days}
                    onChange={(e) =>
                      handleWorkConstraintsChange(typeKey, 'max_consecutive_days', e.target.value)
                    }
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={constValue.min_monthly_workdays}
                    onChange={(e) =>
                      handleWorkConstraintsChange(typeKey, 'min_monthly_workdays', e.target.value)
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* JSON 出力 & ダウンロード */}
      <section>
        <h2>生成された JSON</h2>
        <button onClick={handleDownloadJson}>JSON をダウンロード</button>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </section>
    </div>
  );
}

export default App;
