/**
 * useAgentStream.ts — Live SSE stream hook for the Director's Cockpit.
 *
 * Plugs directly into the FastAPI backend at VITE_API_BASE_URL.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  CampaignStage,
  SSEEventBreakpoint,
  MarketingContent,
  HITLDecision,
  Thought,
  GoalNode,
} from '@/types';
import { api, resumeCampaign } from '@/api/client';

const PIPELINE_NODES: GoalNode[] = [
  {
    id: 'creative',
    title: 'Creative Worker',
    kpi: 'Caption + Prompt',
    status: 'idle',
    x: 250,
    y: 250,
    radius: 60,
    summary: 'Transforms the raw brief into a MarketingContent artifact aligned with the active persona.',
    connections: ['critic'],
  },
  {
    id: 'critic',
    title: 'Critic Worker',
    kpi: 'Vibe Score',
    status: 'idle',
    x: 500,
    y: 180,
    radius: 55,
    summary: 'Evaluates content against five Hard Constraints. Grades PASS or REVISION.',
    connections: ['image'],
  },
  {
    id: 'image',
    title: 'Image Worker',
    kpi: 'Visual Asset',
    status: 'idle',
    x: 700,
    y: 300,
    radius: 50,
    summary: 'Executes the image_prompt faithfully, respecting aspect ratio and visual mood.',
    connections: ['approval'],
  },
  {
    id: 'approval',
    title: 'Approval Gate',
    kpi: 'HITL Decision',
    status: 'idle',
    x: 500,
    y: 430,
    radius: 65,
    summary: 'Graph pauses here. The Director must approve, reject, or request revision.',
    connections: ['publisher'],
  },
  {
    id: 'publisher',
    title: 'Publisher',
    kpi: 'Delivery',
    status: 'idle',
    x: 250,
    y: 430,
    radius: 45,
    summary: 'Delivers approved content to Instagram and/or Threads via Meta Graph API.',
    connections: [],
  },
];

export interface AgentStreamState {
  currentNode: string | null;
  thoughts: Thought[];
  stage: CampaignStage;
  isStreaming: boolean;
  isSubmitting: boolean;
  breakpoint: SSEEventBreakpoint | null;
  preview: MarketingContent | null;
  nodes: GoalNode[];

  startSimulation: () => void;
  submitDecision: (decision: HITLDecision, feedback?: string) => void;
  triggerPivot: (nodeId: string) => void;
  reset: () => void;
}

export function useAgentStream(): AgentStreamState {
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [stage, setStage] = useState<CampaignStage>('draft');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [breakpoint, setBreakpoint] = useState<SSEEventBreakpoint | null>(null);
  const [preview, setPreview] = useState<MarketingContent | null>(null);
  const [nodes, setNodes] = useState<GoalNode[]>(PIPELINE_NODES);
  
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // ── Re-Hydration (BRIDGE_SPEC.md §4) ──
  useEffect(() => {
    const savedThreadId = localStorage.getItem('agency_thread_id');
    if (!savedThreadId) return;

    setActiveThreadId(savedThreadId);
    
    // Check state to see if we should resume listening
    api.get<{ stage: CampaignStage }>(`/campaign/${savedThreadId}/state`)
      .then(res => {
         const currentStage = res.data.stage;
         setStage(currentStage);
         if (currentStage === 'awaiting_approval' || currentStage === 'draft' || currentStage === 'reviewing' || currentStage === 'generating_image') {
            listenToStream(savedThreadId);
         }
      })
      .catch(err => {
         console.warn("Failed to re-hydrate state:", err);
      });
  }, []);

  const addThought = useCallback((agent: string, text: string) => {
    setThoughts((prev) => [
      {
        id: Math.random().toString(36).substring(2, 11),
        agent,
        text,
        timestamp: Date.now(),
      },
      ...prev,
    ].slice(0, 80));
  }, []);

  const updateNodeStatus = useCallback(
    (nodeId: string, status: GoalNode['status']) => {
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, status } : n)),
      );
    },
    []
  );

  const closeStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    return closeStream;
  }, [closeStream]);

  const listenToStream = useCallback((threadId: string) => {
    closeStream();
    setIsStreaming(true);
    
    const es = api.stream(`/campaign/${threadId}/stream`);
    eventSourceRef.current = es;
    
    const handleNodeStart = (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setCurrentNode(data.node_name);
      
      if (data.node_name === 'creative_worker') {
         updateNodeStatus('creative', 'research');
      } else if (data.node_name === 'judge_worker' || data.node_name === 'critic_worker') {
         updateNodeStatus('creative', 'done');
         updateNodeStatus('critic', 'research');
      } else if (data.node_name === 'image_worker') {
         updateNodeStatus('critic', 'done');
         updateNodeStatus('image', 'generation');
      } else if (data.node_name === 'publisher') {
         updateNodeStatus('approval', 'done');
         updateNodeStatus('publisher', 'research');
      }
      addThought('System', `node_start: ${data.node_name}`);
    };

    const handleAgentThought = (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      let agent = 'Agent';
      setCurrentNode((curr) => {
        if (curr === 'creative_worker') agent = 'Creative';
        else if (curr === 'critic_worker' || curr === 'judge_worker') agent = 'Critic';
        else if (curr === 'image_worker') agent = 'Image';
        else if (curr === 'manager_node') agent = 'Manager';
        return curr;
      });
      addThought(agent, data.text);
    };

    const handleBreakpoint = (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setIsStreaming(false);
      setBreakpoint(data);
      setPreview(data.preview);
      updateNodeStatus('image', 'done');
      updateNodeStatus('approval', 'approval');
      addThought('System', `breakpoint: approval_required (${data.approval_mode} mode)`);
    };

    const handleCompletion = (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      
      if (data.stage === 'awaiting_approval') {
         // Breakpoint should handle this, ignore completion event for this stage
         return;
      }
      
      setIsStreaming(false);
      setStage(data.stage);
      setCurrentNode(null);
      if (data.stage === 'published') {
         updateNodeStatus('publisher', 'done');
      }
      addThought('System', `completion: ${data.stage}`);
      closeStream();
    };

    const handleError = (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setIsStreaming(false);
      setStage('failed');
      addThought('Error', data.message);
      closeStream();
    };

    es.addEventListener('node_start', handleNodeStart);
    es.addEventListener('agent_thought', handleAgentThought);
    es.addEventListener('breakpoint', handleBreakpoint);
    es.addEventListener('completion', handleCompletion);
    es.addEventListener('error', handleError);

    es.onerror = () => {
      console.warn("SSE connection error");
    };
  }, [addThought, updateNodeStatus, closeStream]);

  const startSimulation = useCallback(async (
    personaName: string = "Silicon Labor",
    niche: string = "Underground synth-wave event in Berlin.",
    publishTargets: ('instagram' | 'threads')[] = ["instagram"]
  ) => {
    reset();
    setIsStreaming(true);
    addThought('System', `Initiating live campaign thread. Persona: ${personaName}.`);

    try {
      const res = await api.post<{ thread_id: string }>('/campaign/start', {
        persona_name: personaName,
        niche: niche,
        publish_targets: publishTargets
      });
      
      const newThreadId = res.data.thread_id;
      setActiveThreadId(newThreadId);
      api.setThreadId(newThreadId);
      
      listenToStream(newThreadId);
    } catch (err: any) {
      addThought('Error', `Failed to start campaign: ${err.message}`);
      setIsStreaming(false);
      setStage('failed');
    }
  }, [reset, addThought, listenToStream]);

  const submitDecision = useCallback(
    async (decision: HITLDecision, feedback?: string) => {
      if (!activeThreadId || isSubmitting) return;

      setIsSubmitting(true);
      // Clear the gate immediately so the overlay is shown on BreakpointGate
      setBreakpoint(null);

      try {
        await resumeCampaign(activeThreadId, {
          decision,
          feedback: feedback ?? null,
          edited_content: decision === 'edit' && preview ? preview : null,
          channel: 'web_ui',
        });

        if (decision === 'approve') {
          addThought('Director', 'Approval transmitted. Resuming pipeline...');
          updateNodeStatus('approval', 'done');
          listenToStream(activeThreadId);
        } else if (decision === 'edit') {
          addThought('Director', 'Edited content submitted. Resuming pipeline...');
          updateNodeStatus('approval', 'done');
          listenToStream(activeThreadId);
        } else if (decision === 'request_revision') {
          addThought('Director', `Revision requested.${feedback ? ` — "${feedback}"` : ''}`);
          setStage('revising');
          updateNodeStatus('approval', 'idle');
          updateNodeStatus('creative', 'idle');
          updateNodeStatus('critic', 'idle');
          updateNodeStatus('image', 'idle');
          setPreview(null);
          listenToStream(activeThreadId);
        } else if (decision === 'reject') {
          addThought('Director', 'Campaign vetoed.');
          setStage('vetoed');
          updateNodeStatus('approval', 'idle');
          // No SSE re-subscription — graph is terminated
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        addThought('Error', `Failed to submit decision: ${message}`);
        setIsStreaming(false);
        setStage('failed');
      } finally {
        setIsSubmitting(false);
      }
    },
    [activeThreadId, isSubmitting, addThought, listenToStream, updateNodeStatus, preview],
  );

  const triggerPivot = useCallback(
    (nodeId: string) => {
      setNodes((prev) =>
        prev.map((n) =>
          n.id === nodeId ? { ...n, isPivot: true, status: 'research' as const } : n,
        ),
      );
      addThought('Director', `Strategic pivot initiated on node: ${nodeId}`);
    },
    [addThought],
  );

  const reset = useCallback(() => {
    closeStream();
    setCurrentNode(null);
    setThoughts([]);
    setStage('draft');
    setIsStreaming(false);
    setBreakpoint(null);
    setPreview(null);
    setActiveThreadId(null);
    setNodes(PIPELINE_NODES.map((n) => ({ ...n, status: 'idle' as const, isPivot: false })));
  }, [closeStream]);

  return {
    currentNode,
    thoughts,
    stage,
    isStreaming,
    isSubmitting,
    breakpoint,
    preview,
    nodes,
    startSimulation,
    submitDecision,
    triggerPivot,
    reset,
  };
}
