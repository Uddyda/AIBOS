import React from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

type DailyRequirement = {
  normal_min: number;
  normal_max: number;
  friend_min: number;
  friend_max: number;
};

type DailyRequirementsTableProps = {
  dailyRequirements: { [key: string]: DailyRequirement };
  order: string[];
  onOrderChange: (newOrder: string[]) => void;
  onChange: (key: string, field: keyof DailyRequirement, value: number) => void;
  onAdd: (key: string) => void;
  onDelete: (key: string) => void;
};

const DailyRequirementsTable: React.FC<DailyRequirementsTableProps> = ({
  dailyRequirements,
  order,
  onOrderChange,
  onChange,
  onAdd,
  onDelete,
}) => {
  const [newKey, setNewKey] = React.useState("");
  const sensors = useSensors(useSensor(PointerSensor));

  function handleDragEnd(event: any) {
    const { active, over } = event;
    if (!over) return;
    if (active.id !== over.id) {
      const oldIndex = order.indexOf(active.id);
      const newIndex = order.indexOf(over.id);
      onOrderChange(arrayMove(order, oldIndex, newIndex));
    }
  }

  return (
    <div
      style={{
        fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
        background: "#fcfbf8",
        borderRadius: 18,
        padding: "10px 18px 16px 18px",
        boxShadow: "0 4px 20px 0 rgba(90,100,140,0.04)",
        border: "1.5px solid #e0e6ea",
        margin: "0 auto",
        maxWidth: 600,
      }}
    >
      <h2 style={{ fontWeight: 600, fontSize: 20, marginBottom: 12 }}>職種一覧</h2>
      <div style={{
        marginBottom: 18,
        display: "flex",
        gap: 10,
        alignItems: "center"
      }}>
        <input
          type="text"
          placeholder="新しい職種名"
          value={newKey}
          onChange={e => setNewKey(e.target.value)}
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
        <button
          onMouseDown={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
          onMouseUp={e => (e.currentTarget.style.transform = "")}
          onMouseLeave={e => (e.currentTarget.style.transform = "")}
          onTouchStart={e => (e.currentTarget.style.transform = "translateY(2px) scale(0.97)")}
          onTouchEnd={e => (e.currentTarget.style.transform = "")}
          onClick={() => {
            if (!newKey.trim()) return;
            onAdd(newKey.trim());
            setNewKey("");
          }}
          style={{
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            fontSize: 15,
            borderRadius: 7,
            background: "linear-gradient(90deg, #a7e2ff, #c3c1ff)",
            color: "#0a2463",
            fontWeight: 600,
            padding: "6px 24px",
            border: "none",
            cursor: "pointer",
            boxShadow: "0 1px 6px 0 rgba(140,180,255,0.07)",
            transition: "background 0.2s",
            whiteSpace: "nowrap",
          }}
        >
          追加
        </button>
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={order} strategy={verticalListSortingStrategy}>
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
                <th style={{ minWidth: 80 }}>職種名</th>
                <th style={{ minWidth: 90 }}>normal_min</th>
                <th style={{ minWidth: 90 }}>normal_max</th>
                <th style={{ minWidth: 90 }}>friend_min</th>
                <th style={{ minWidth: 90 }}>friend_max</th>
                <th>削除</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {order.map(key => (
                <SortableRow
                  key={key}
                  id={key}
                  value={dailyRequirements[key]}
                  onChange={onChange}
                  onDelete={onDelete}
                />
              ))}
            </tbody>
          </table>
        </SortableContext>
      </DndContext>
    </div>
  );
};

function SortableRow({
  id,
  value,
  onChange,
  onDelete,
}: {
  id: string;
  value: DailyRequirement;
  onChange: (key: string, field: keyof DailyRequirement, value: number) => void;
  onDelete: (key: string) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });

  return (
    <tr
      ref={setNodeRef}
      style={{
        background: isDragging ? "#eef8ff" : "transparent",
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
        <input
          type="number"
          value={value.normal_min}
          style={{
            width: 80,
            fontSize: 15,
            borderRadius: 5,
            border: "1px solid #e0e6ea",
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            background: "#f8fafc",
            padding: "2.5px 6px",
            zIndex: 2,
            position: "relative"
          }}
          onChange={e => onChange(id, "normal_min", Number(e.target.value))}
          onPointerDown={e => e.stopPropagation()}
        />
      </td>
      <td>
        <input
          type="number"
          value={value.normal_max}
          style={{
            width: 80,
            fontSize: 15,
            borderRadius: 5,
            border: "1px solid #e0e6ea",
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            background: "#f8fafc",
            padding: "2.5px 6px",
            zIndex: 2,
            position: "relative"
          }}
          onChange={e => onChange(id, "normal_max", Number(e.target.value))}
          onPointerDown={e => e.stopPropagation()}
        />
      </td>
      <td>
        <input
          type="number"
          value={value.friend_min}
          style={{
            width: 80,
            fontSize: 15,
            borderRadius: 5,
            border: "1px solid #e0e6ea",
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            background: "#f8fafc",
            padding: "2.5px 6px",
            zIndex: 2,
            position: "relative"
          }}
          onChange={e => onChange(id, "friend_min", Number(e.target.value))}
          onPointerDown={e => e.stopPropagation()}
        />
      </td>
      <td>
        <input
          type="number"
          value={value.friend_max}
          style={{
            width: 80,
            fontSize: 15,
            borderRadius: 5,
            border: "1px solid #e0e6ea",
            fontFamily: '"Noto Sans JP", "Yu Gothic UI", Arial, sans-serif',
            background: "#f8fafc",
            padding: "2.5px 6px",
            zIndex: 2,
            position: "relative"
          }}
          onChange={e => onChange(id, "friend_max", Number(e.target.value))}
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
            onDelete(id);
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
            whiteSpace: "nowrap"
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

export default DailyRequirementsTable;
