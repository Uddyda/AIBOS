// src/types/shift.ts
export type RoleType = "employee" | "part_timer";

export interface RoleData {
  type: RoleType;
  count: number;
}

export interface Roles {
  [key: string]: RoleData;
}

export interface DailyRequirement {
  normal_min: number;
  normal_max: number;
  friend_min: number;
  friend_max: number;
}

export interface DailyRequirements {
  [key: string]: DailyRequirement;
}

export interface RoleCapability {
  [key: string]: {
    primary: string[];
    secondary: string[];
    third: string[];
  };
}

export interface WorkConstraint {
  weekly_days_off: number;
  max_consecutive_days: number;
  min_monthly_workdays: number;
}

export interface WorkConstraints {
  employee: WorkConstraint;
  part_timer: WorkConstraint;
  dummy: WorkConstraint;
}

export interface ShiftConfig {
  year: number;
  months: string[];
  roles: Roles;
  daily_requirements: DailyRequirements;
  role_capability: RoleCapability;
  work_constraints: WorkConstraints;
}
