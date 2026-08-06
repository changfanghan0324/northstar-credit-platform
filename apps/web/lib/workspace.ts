export const workspaceSections = [
  "overview",
  "inputs",
  "financials",
  "capacity",
  "facility",
  "risk",
  "stress",
  "decision",
  "memo",
] as const;

export type WorkspaceSection = (typeof workspaceSections)[number];
