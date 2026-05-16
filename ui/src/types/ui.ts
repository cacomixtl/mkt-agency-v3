/**
 * ui.ts — UI-specific types used by the Director's Cockpit components.
 *
 * These types represent the visual/interaction layer and do NOT exist
 * in CONTRACTS.py. They map the backend domain model to the canvas,
 * sidebar, and cockpit presentation.
 */

/** Visual status of a node on the GalacticCanvas. */
export type AgentStatus = 'idle' | 'research' | 'generation' | 'approval' | 'done';

/** A node on the GalacticCanvas — represents a pipeline stage or strategic goal. */
export interface GoalNode {
  id: string;
  title: string;
  kpi: string;
  status: AgentStatus;
  x: number;
  y: number;
  radius: number;
  summary: string;
  connections: string[];
  isPivot?: boolean;
}

/** A single thought entry in the PulseSidebar's streaming log. */
export interface Thought {
  id: string;
  agent: string;
  text: string;
  timestamp: number;
}
