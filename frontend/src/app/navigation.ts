import {
  Database,
  FileSearch,
  LayoutDashboard,
  MessagesSquare,
  PlayCircle,
  ShieldCheck,
  SquareTerminal,
  type LucideIcon,
} from 'lucide-react';

export type RouteId =
  | 'overview'
  | 'workbench'
  | 'assistant'
  | 'knowledge'
  | 'sovereignty'
  | 'audit'
  | 'demo';

export interface RouteDefinition {
  id: RouteId;
  label: string;
  /** Longer description used by the command palette and page headers. */
  description: string;
  icon: LucideIcon;
  group: 'Operations' | 'Assurance';
}

export const ROUTES: RouteDefinition[] = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'Fleet status, throughput and compliance at a glance',
    icon: LayoutDashboard,
    group: 'Operations',
  },
  {
    id: 'workbench',
    label: 'Workbench',
    description: 'Run an autonomous engineering task and collect deliverables',
    icon: SquareTerminal,
    group: 'Operations',
  },
  {
    id: 'assistant',
    label: 'Assistant',
    description: 'Ask the on-premise model about procedures and calculations',
    icon: MessagesSquare,
    group: 'Operations',
  },
  {
    id: 'knowledge',
    label: 'Knowledge Base',
    description: 'Search and re-index the local SOP vector store',
    icon: Database,
    group: 'Operations',
  },
  {
    id: 'sovereignty',
    label: 'Sovereignty',
    description: 'Live network isolation evidence and air-gap attestation',
    icon: ShieldCheck,
    group: 'Assurance',
  },
  {
    id: 'audit',
    label: 'Audit Trail',
    description: 'Tamper-evident record of every tool call and inference',
    icon: FileSearch,
    group: 'Assurance',
  },
  {
    id: 'demo',
    label: 'Guided Demo',
    description: 'Six-step walkthrough that exercises every subsystem live',
    icon: PlayCircle,
    group: 'Assurance',
  },
];

export const NAV_GROUPS: Array<RouteDefinition['group']> = ['Operations', 'Assurance'];

const VALID_IDS = new Set(ROUTES.map((route) => route.id));

export function isRouteId(value: string): value is RouteId {
  return VALID_IDS.has(value as RouteId);
}

export function getRoute(id: RouteId): RouteDefinition {
  return ROUTES.find((route) => route.id === id) ?? ROUTES[0];
}
