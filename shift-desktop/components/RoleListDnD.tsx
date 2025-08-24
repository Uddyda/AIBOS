import React, { useState } from "react";
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

type RoleData = { type: "employee" | "part_timer"; count: number };
type RoleListDnDProps = {
  roles: { [role: string]: RoleData };
  order: string[];
  onOrderChange: (newOrder: string[]) => void; 
  onChangeRole: (roleKey: string, field: "type" | "count", value: string | number) => void;
  onAddRole: (roleKey: string, type: "employee" | "part_timer") => void;
  onDeleteRole: (roleKey: string) => void;
};

function SortableRoleRow({
  id,
  roleValue,
  onChangeRole,
  onDeleteRole, 
}: {
  id: string;
  roleValue: RoleData;
  onChangeRole: (field: "type" | "count", value: string | number) => void;
  onDeleteRole: (id: string) => void;
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
    <tr
      ref={setNodeRef}
      style={{
        background: isDragging ? "#eaf4fe" : "transparent",
        ...(transform ? { transform: CSS.Transform.toString(transform), transition } : {}),
        cursor: "grab",
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        transition: "background 0.18s",
      }}
      {...attributes}
      {...listeners}
    >
      <td style={{ fontWeight: "bold", minWidth: 80 }}>{id}</td>
      <td>
        <select
          value={roleValue.type}
          onChange={e => onChangeRole("type", e.target.value as "employee" | "part_timer")}
          style={{
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            fontSize: 15,
            borderRadius: 5,
            border: "1px solid #e0e6ea",
            background: "#f4f8fc",
            padding: "2.5px 6px",
            zIndex: 2,
            position: "relative"
          }}
          onPointerDown={e => e.stopPropagation()}
        >
          <option value="employee">社員</option>
          <option value="part_timer">パート</option>
        </select>
      </td>
      <td>
        <input
          type="number"
          value={roleValue.count}
          onChange={e => onChangeRole("count", Number(e.target.value))}
          style={{
            width: 68,
            fontSize: 15,
            borderRadius: 5,
            border: "1px solid #e0e6ea",
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            background: "#f8fafc",
            padding: "2.5px 6px",
            zIndex: 2,
            position: "relative"
          }}
          onPointerDown={e => e.stopPropagation()}
        />
      </td>
      <td>
        <button
          onMouseDown={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
          onMouseUp={e => (e.currentTarget.style.transform = "")}
          onMouseLeave={e => (e.currentTarget.style.transform = "")}
          onTouchStart={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
          onTouchEnd={e => (e.currentTarget.style.transform = "")}
          onClick={e => {
            e.stopPropagation();
            onDeleteRole(id);
          }}
          onPointerDown={e => e.stopPropagation()}
          style={{
            color: "#d00",
            padding: "3px 8px",
            fontSize: "13px",
            minWidth: 28,
            border: "1px solid #e0e6ea",
            borderRadius: 5,
            marginLeft: 6,
            background: "#fff",
            cursor: "pointer",
            lineHeight: "18px",
            zIndex: 1,
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            boxShadow: "none",
          }}
        >
          削除
        </button>
      </td>
      <td>
        <span
          style={{
            color: "#b2b7c2",
            fontSize: 18,
            cursor: "grab",
            userSelect: "none",
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            marginLeft: 2,
          }}
        >
          ☰
        </span>
      </td>
    </tr>
  );
}

const RoleListDnD: React.FC<RoleListDnDProps> = ({
  roles,
  order,
  onOrderChange,
  onChangeRole,
  onAddRole,
  onDeleteRole,
}) => {
  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleType, setNewRoleType] = useState<"employee" | "part_timer">("employee");

  const sensors = useSensors(useSensor(PointerSensor));

  const handleAdd = () => {
    if (!newRoleName.trim()) return;
    onAddRole(newRoleName, newRoleType);
    setNewRoleName("");
    setNewRoleType("employee");
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;
    if (active.id !== over.id) {
      const oldIndex = order.indexOf(active.id as string);
      const newIndex = order.indexOf(over.id as string);
      if (oldIndex !== -1 && newIndex !== -1) {
        onOrderChange(arrayMove(order, oldIndex, newIndex));
      }
    }
  };

  return (
    <div style={{
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        background: "#f6fafd",
        borderRadius: 18,
        padding: "10px 18px 16px 18px",
        boxShadow: "0 4px 20px 0 rgba(90,100,140,0.04)",
        border: "1.5px solid #e0e6ea",
        margin: "0 auto",
        maxWidth: 600,
      }}
    >
      <h2 style={{ fontWeight: 600, fontSize: 20, marginBottom: 12 }}>役職一覧</h2>
      <div style={{
        marginBottom: 18,
        display: "flex",
        gap: 10,
        alignItems: "center"
      }}>
        <input
          type="text"
          value={newRoleName}
          placeholder="役職名"
          onChange={e => setNewRoleName(e.target.value)}
          style={{
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            fontSize: 15,
            border: "1px solid #e0e6ea",
            borderRadius: 6,
            padding: "6px 12px",
            background: "#fff",
            outline: "none",
            minWidth: 110,
          }}
        />
        <select
          value={newRoleType}
          onChange={e => setNewRoleType(e.target.value as "employee" | "part_timer")}
          style={{
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            fontSize: 15,
            border: "1px solid #e0e6ea",
            borderRadius: 6,
            padding: "6px 12px",
            background: "#fff",
            outline: "none"
          }}
        >
          <option value="employee">employee</option>
          <option value="part_timer">part_timer</option>
        </select>
        <button
          style={{
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
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
          }}
          onMouseDown={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
          onMouseUp={e => (e.currentTarget.style.transform = "")}
          onMouseLeave={e => (e.currentTarget.style.transform = "")}
          onTouchStart={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
          onTouchEnd={e => (e.currentTarget.style.transform = "")}
          onClick={handleAdd}
        >
          役職追加
        </button>
      </div>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={order}
          strategy={verticalListSortingStrategy}
        >
          <table
            border={0}
            cellPadding={6}
            style={{
              marginTop: 2,
              width: "100%",
              borderCollapse: "separate",
              borderSpacing: 0,
              borderRadius: 16,
              background: "#fafdff",
              overflow: "hidden",
              boxShadow: "0 1px 4px 0 rgba(100,120,170,0.02)",
              fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            }}
          >
            <thead>
              <tr style={{
                background: "#f1f6ff",
                color: "#445",
                fontSize: 16,
              }}>
                <th>役職名</th>
                <th>type</th>
                <th>count</th>
                <th>削除</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {order.map((roleKey) => (
                <SortableRoleRow
                  key={roleKey}
                  id={roleKey}
                  roleValue={roles[roleKey]}
                  onChangeRole={(field, value) => onChangeRole(roleKey, field, value)}
                  onDeleteRole={onDeleteRole}
                />
              ))}
            </tbody>
          </table>
        </SortableContext>
      </DndContext>
    </div>
  );
};

export default RoleListDnD;
