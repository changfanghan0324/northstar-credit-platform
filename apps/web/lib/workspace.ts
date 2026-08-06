export const workspaceSections = [
  "overview",
  "inputs",
  "financials",
  "capacity",
  "risk",
  "stress",
  "decision",
  "memo",
] as const;

export type WorkspaceSection = (typeof workspaceSections)[number];
