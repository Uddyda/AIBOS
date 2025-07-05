import React from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

// 型定義
type RoleCapabilityDnDProps = {
  capKey: string;
  capability: { primary: string[]; secondary: string[] };
  roles: { [role: string]: { type: string; count: number } };
  onUpdate: (
    level: "primary" | "secondary",
    newArr: string[]
  ) => void;
  onEdit: (
    level: "primary" | "secondary",
    index: number,
    value: string
  ) => void;
  onDelete: (
    level: "primary" | "secondary",
    index: number
  ) => void;
  onAdd: (level: "primary" | "secondary", value: string) => void;
};

function SortableItem({
  id,
  value,
  onEdit,
  onDelete,
  level,
  index,
}: {
  id: string;
  value: string;
  onEdit: (index: number, value: string) => void;
  onDelete: (index: number) => void;
  level: "primary" | "secondary";
  index: number;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    background: isDragging ? "#b4f8ff" : "#fff",
    border: "1px solid #ccc",
    padding: "2px 6px 2px 2px", // ← [上下, 右, 下, 左]
    marginBottom: 3,
    borderRadius: 3,
    cursor: "grab",
    display: "flex",
    alignItems: "center",
    gap: 4,
  };

  return (
    <li ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <input
        type="text"
        value={value}
        onChange={e => onEdit(index, e.target.value)}
        style={{
          flex: 1,
          minWidth: 50,
          fontSize: "inherit",
          padding: "2px 3px",
          border: "none",          // 👈 枠線なし
          outline: "none",         // 👈 フォーカス時も枠を消したい場合
          fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',//fontの指定
          background: "transparent", // 👈 任意: 枠が消えることで背景色が気になるなら
        }}
      />
      <button
        onClick={() => onDelete(index)}
        style={{
          color: "#c00",
          padding: "0px 5px",
          fontSize: "12px",
          height: 22,
          minWidth: 28,
          border: "1px solid #ccc",
          borderRadius: 3,
          marginLeft: 4,
          background: "#fff",
          cursor: "pointer",
          lineHeight: "18px",
        }}
      >
        削除
      </button>
      <span style={{ color: "#999", fontSize: 18, cursor: "grab" }}>☰</span>
    </li>
  );
}

const RoleCapabilityDnD: React.FC<RoleCapabilityDnDProps> = ({
  capKey,
  capability,
  roles,
  onUpdate,
  onEdit,
  onDelete,
  onAdd,
}) => {
  // DnD sensors
  const sensors = useSensors(useSensor(PointerSensor));

  // --- 並べ替え（primary or secondaryどちらか）
  function handleDragEnd(level: "primary" | "secondary") {
    return (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over) return;
      if (active.id !== over.id) {
        const arr = capability[level];
        const oldIndex = arr.findIndex((item) => item === active.id);
        const newIndex = arr.findIndex((item) => item === over.id);
        if (oldIndex !== -1 && newIndex !== -1) {
          onUpdate(level, arrayMove(arr, oldIndex, newIndex));
        }
      }
    };
  }

  // --- 追加
  function handleSelectAdd(e: React.ChangeEvent<HTMLSelectElement>, level: "primary" | "secondary") {
    const value = e.target.value;
    if (!value) return;
    onAdd(level, value);
    e.target.value = ""; // reset
  }

  return (
    <div     
      style={{
      marginBottom: 12,            // ブロック同士の下余白
      border: "1px solid #ddd",
      borderRadius: 8,
      padding: 12,                 // 内側の余白（全体を小さくしたいなら値を減らす）
      width: 500,                  // ★ カード全体の横幅（必要なら指定）
      maxWidth: "100%",            // 必要なら追加
      boxSizing: "border-box",     // 念のため
      background: "#fafaff",       // 任意
    }}>
      <h4
        style={{
          fontWeight: "bold",
          marginBottom: 4,    // ← 下の余白（間を狭くしたいなら小さく）
          marginTop: 2,       // ← 上の余白（もっと空けたいなら増やす/狭くしたいなら0や2など）
          marginRight: 0,
          marginLeft: 0,
          fontSize: 16        // 必要なら
        }}
      >{capKey}</h4>
      <div style={{ display: "flex", gap: 40 }}>
        {/* Primary */}
        <div style={{ width: 220 }}>
          <label>Primary:</label>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd("primary")}
          >
            <SortableContext items={capability.primary} strategy={verticalListSortingStrategy}>
              <ul style={{ minHeight: 32, padding: 0, margin: 0 }}>
                {capability.primary.map((member, idx) => (
                  <SortableItem
                    key={member + idx}
                    id={member}
                    value={member}
                    onEdit={(i, val) => onEdit("primary", i, val)}
                    onDelete={i => onDelete("primary", i)}
                    level="primary"
                    index={idx}
                  />
                ))}
              </ul>
            </SortableContext>
          </DndContext>
          <div style={{ marginTop: 6 }}>
            <select
              onChange={e => handleSelectAdd(e, "primary")}
              defaultValue=""
              style={{ minWidth: 120 }}
            >
              <option value="">--役職を追加--</option>
              {Object.keys(roles).map((roleKey) => (
                <option key={roleKey} value={roleKey}>
                  {roleKey}
                </option>
              ))}
            </select>
          </div>
        </div>
        {/* Secondary */}
        <div style={{ width: 220 }}>
          <label>Secondary:</label>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd("secondary")}
          >
            <SortableContext items={capability.secondary} strategy={verticalListSortingStrategy}>
              <ul style={{ minHeight: 32, padding: 0, margin: 0 }}>
                {capability.secondary.map((member, idx) => (
                  <SortableItem
                    key={member + idx}
                    id={member}
                    value={member}
                    onEdit={(i, val) => onEdit("secondary", i, val)}
                    onDelete={i => onDelete("secondary", i)}
                    level="secondary"
                    index={idx}
                  />
                ))}
              </ul>
            </SortableContext>
          </DndContext>
          <div style={{ marginTop: 6 }}>
            <select
              onChange={e => handleSelectAdd(e, "secondary")}
              defaultValue=""
              style={{ minWidth: 120 }}
            >
              <option value="">--役職を追加--</option>
              {Object.keys(roles).map((roleKey) => (
                <option key={roleKey} value={roleKey}>
                  {roleKey}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleCapabilityDnD;
