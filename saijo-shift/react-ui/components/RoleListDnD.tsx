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
  roleOrder: string[];
  onRoleOrderChange: (order: string[]) => void;
  onChangeRole: (roleKey: string, field: "type" | "count", value: string | number) => void;
  onAddRole: (roleKey: string, type: "employee" | "part_timer") => void;
};

function SortableRoleRow({
  id,
  roleValue,
  onChangeRole,
}: {
  id: string;
  roleValue: RoleData;
  onChangeRole: (field: "type" | "count", value: string | number) => void;
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
        background: isDragging ? "#b4f8ff" : "#fff",
        cursor: "grab",
        transition,
        transform: CSS.Transform.toString(transform),
      }}
      {...attributes}
      {...listeners}
    >
      <td>{id}</td>
      <td>
        <select
          value={roleValue.type}
          onChange={e => onChangeRole("type", e.target.value as "employee" | "part_timer")}
        >
          <option value="employee">employee</option>
          <option value="part_timer">part_timer</option>
        </select>
      </td>
      <td>
        <input
          type="number"
          value={roleValue.count}
          onChange={e => onChangeRole("count", Number(e.target.value))}
        />
      </td>
    </tr>
  );
}

const RoleListDnD: React.FC<RoleListDnDProps> = ({
  roles,
  roleOrder,
  onRoleOrderChange,
  onChangeRole,
  onAddRole,
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
      const oldIndex = roleOrder.indexOf(active.id as string);
      const newIndex = roleOrder.indexOf(over.id as string);
      if (oldIndex !== -1 && newIndex !== -1) {
        onRoleOrderChange(arrayMove(roleOrder, oldIndex, newIndex));
      }
    }
  };

  return (
    <div>
      <input
        type="text"
        value={newRoleName}
        placeholder="役職名"
        onChange={e => setNewRoleName(e.target.value)}
        style={{ marginRight: 8 }}
      />
      <select
        value={newRoleType}
        onChange={e => setNewRoleType(e.target.value as "employee" | "part_timer")}
        style={{ marginRight: 8 }}
      >
        <option value="employee">employee</option>
        <option value="part_timer">part_timer</option>
      </select>
      <button style={{ marginBottom: 8 }} onClick={handleAdd}>役職追加</button>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={roleOrder}
          strategy={verticalListSortingStrategy}
        >
          <table border={1} cellPadding={5} style={{ marginTop: 10, width: "100%" }}>
            <thead>
              <tr>
                <th>役職名</th>
                <th>type</th>
                <th>count</th>
              </tr>
            </thead>
            <tbody>
              {roleOrder.map((roleKey) => (
                <SortableRoleRow
                  key={roleKey}
                  id={roleKey}
                  roleValue={roles[roleKey]}
                  onChangeRole={(field, value) => onChangeRole(roleKey, field, value)}
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
