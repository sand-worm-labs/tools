// Kept in lockstep with schema/tool.schema.json's `inputs[].type` enum —
// update both together.
export type ParamType =
  | "address"
  | "address[]"
  | "chain"
  | "chain[]"
  | "select"
  | "schema_uid"
  | "token_address"
  | "text"
  | "number"
  | "date"
  | "date_range";

export interface ToolInput {
  key: string;
  label: string;
  type: ParamType;
  required: boolean;
  default?: unknown;
}

export interface ToolReturn {
  name: string;
  type: string;
}

export interface Tool {
  tool_id: string;
  g1: string;
  g2?: string;
  g3?: string;
  g4?: string;
  g5?: string;
  description: string;
  scope?: string;
  returns?: ToolReturn[];
  inputs?: ToolInput[];
}

export interface Category {
  category_id: string;
  name: string;
  description: string;
}
