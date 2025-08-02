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
  onAdd: (level: "primary" | "secondary", value: string) => boolean;
};

function SortableItem({
  id,
  value,
  onDelete,
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

  return (
    <li
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        background: isDragging ? "#eafcf8" : "#fff",
        border: "1px solid #e0e6ea",
        padding: "3px 6px 3px 7px",
        marginBottom: 6,
        borderRadius: 6,
        boxShadow: isDragging ? "0 1px 5px 0 rgba(100,180,255,0.10)" : "0 1px 4px 0 rgba(120,140,180,0.02)",
        cursor: "grab",
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        fontSize: 15,
        position: "relative",
      }}
      {...attributes}
      {...listeners}
    >
      <span
        style={{
          flex: 1,
          minWidth: 56,
          fontSize: 15,
          padding: "3px 2px",
          fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
          userSelect: "none",
          border: "none",
          outline: "none",
          background: "transparent",
        }}
      >
        {value}
      </span>
      <button
        onMouseDown={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
        onMouseUp={e => (e.currentTarget.style.transform = "")}
        onMouseLeave={e => (e.currentTarget.style.transform = "")}
        onTouchStart={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
        onTouchEnd={e => (e.currentTarget.style.transform = "")}
        onClick={e => {
          e.stopPropagation();
          onDelete(index);
        }}
        onPointerDown={e => e.stopPropagation()}
        style={{
          color: "#d00",
          padding: "3px 10px",
          fontSize: "13px",
          minWidth: 30,
          border: "1px solid #e0e6ea",
          borderRadius: 5,
          marginLeft: 4,
          background: "#fff",
          cursor: "pointer",
          lineHeight: "18px",
          zIndex: 2,
          fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        }}
      >
        削除
      </button>
      <span
        style={{
          color: "#b2b7c2",
          fontSize: 18,
          cursor: "grab",
          marginLeft: 5,
          userSelect: "none",
          fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        }}
      >
        ☰
      </span>
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
  const sensors = useSensors(useSensor(PointerSensor));

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

  function handleSelectAdd(
    e: React.ChangeEvent<HTMLSelectElement>,
    level: "primary" | "secondary"
  ) {
    const value = e.target.value;
    if (!value) return;
    const isDuplicate = onAdd(level, value);
    if (isDuplicate) {
      alert("既に追加されています。");
    }
    e.target.value = "";
  }

  return (
    <div
      style={{
        marginBottom: 14,
        border: "1px solid #e0e6ea",
        borderRadius: 16,
        padding: 18,
        width: 500,
        maxWidth: "100%",
        boxSizing: "border-box",
        background: "#eafcf8",
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        boxShadow: "0 2px 8px 0 rgba(100,120,170,0.04)",
      }}
    >
      <h4
        style={{
          fontWeight: "bold",
          marginBottom: 8,
          marginTop: 2,
          marginRight: 0,
          marginLeft: 0,
          fontSize: 18,
          letterSpacing: 0.5,
        }}
      >
        {capKey}
      </h4>
      <div style={{ display: "flex", gap: 30 }}>
        {/* Primary */}
        <div style={{ width: 220 }}>
          <label style={{ fontWeight: 600, fontSize: 15 }}>Primary:</label>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd("primary")}
          >
            <SortableContext items={capability.primary} strategy={verticalListSortingStrategy}>
              <ul style={{ minHeight: 32, padding: 0, margin: 0, listStyle: "none" }}>
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
          <div style={{ marginTop: 10 }}>
            <select
              onChange={e => handleSelectAdd(e, "primary")}
              defaultValue=""
              style={{
                minWidth: 120,
                borderRadius: 6,
                padding: "5px 12px",
                fontSize: 15,
                fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
                background: "#f6fafd",
                border: "1px solid #e0e6ea",
                outline: "none"
              }}
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
          <label style={{ fontWeight: 600, fontSize: 15 }}>Secondary:</label>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd("secondary")}
          >
            <SortableContext items={capability.secondary} strategy={verticalListSortingStrategy}>
              <ul style={{ minHeight: 32, padding: 0, margin: 0, listStyle: "none" }}>
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
          <div style={{ marginTop: 10 }}>
            <select
              onChange={e => handleSelectAdd(e, "secondary")}
              defaultValue=""
              style={{
                minWidth: 120,
                borderRadius: 6,
                padding: "5px 12px",
                fontSize: 15,
                fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
                background: "#f6fafd",
                border: "1px solid #e0e6ea",
                outline: "none"
              }}
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
