# DAEMON Intent and Goal Tracking Implementation Guide

**Created:** 2025-12-24 (Session 36)
**Status:** Research Complete
**Related:** daemon-orchestrator-implementation.md, daemon-data-ingestion.md

---

## Executive Summary

This guide covers implementing a goal and intent tracking system for DAEMON that operates at three temporal scales: **immediate intent** (current conversation), **project-level goals** (active work with milestones), and **life-level aspirations** (values-aligned objectives). The system integrates with Mem0 for semantic retrieval and the orchestrator for context-aware assistance.

**Key Insight:** Goals are the "why" layer that gives coherence to memory retrieval and response generation. Without goal awareness, DAEMON can only react; with it, DAEMON can proactively connect disparate activities.

---

## Part 1: Core Data Model

### 1.1 Goal Schema

Goals need hierarchical representation with temporal and progress dimensions:

```yaml
# goals.jsonl (newline-delimited JSON for streaming updates)

{
  "id": "goal:2025:learn-piano",
  "title": "Learn piano fundamentals",
  "scope": "life",  # "immediate" | "project" | "life"
  "status": "active",  # "active" | "paused" | "completed" | "abandoned"

  # Temporal
  "created_at": "2025-01-01T00:00:00Z",
  "due_at": "2025-12-31T23:59:59Z",
  "time_scale": "months",  # "minutes" | "hours" | "days" | "weeks" | "months" | "years"

  # Intent alignment
  "parent_goal": "goal:2024:creative-practice",
  "related_projects": ["proj:music-learning"],
  "values_aligned": ["creativity", "discipline", "growth"],

  # Progress tracking
  "progress": {
    "current": 15,
    "target": 100,
    "unit": "hours",
    "last_updated": "2025-12-20T15:30:00Z"
  },

  # Decomposition
  "milestones": [
    {
      "id": "m1",
      "title": "Learn C major scale",
      "due_at": "2025-03-01",
      "status": "in_progress",
      "progress": 0.6
    }
  ],

  # Blockers
  "blockers": [
    {
      "id": "b1",
      "title": "Need to find good online course",
      "status": "resolved",
      "resolution": "Enrolled in Piano Marvel"
    }
  ],

  # Motivation and reminders
  "why": "Creative expression, stress relief, childhood passion",
  "reminders": {
    "frequency": "weekly",
    "next_at": "2025-12-27T10:00:00Z"
  },

  # Metadata
  "inferred": false,  # true if extracted from conversation vs explicitly set
  "confidence": 1.0,  # 0.0-1.0, lower for inferred goals
  "tags": ["music", "hobby", "learning"]
}
```

### 1.2 Intent Schema (Immediate Context)

Intent is lighter—focused on the current conversation:

```json
{
  "id": "intent:session:abc123",
  "conversation_id": "conv:abc123",
  "timestamp": "2025-12-24T14:30:00Z",

  "primary_goal": "goal:2025:learn-piano",
  "task": "Get recommendations for online piano courses",
  "context": "Considering starting piano lessons soon",

  "motivation": "Creative expression and stress relief",
  "urgency": "medium",
  "ttl_minutes": 30,

  "coherence_score": 0.95,
  "inferred_from_conversation": true
}
```

### 1.3 Active Context (Runtime State)

```python
@dataclass
class ActiveContext:
    """What's active right now in this session."""

    # Immediate
    current_intent: Optional[Intent]
    current_conversation_turn: int
    time_in_conversation: timedelta

    # Recent goal interactions
    recently_mentioned_goals: list[Goal]  # Goals mentioned in last N turns
    last_mentioned_goal: Optional[Goal]

    # What shouldn't be forgotten
    open_blockers: list[Blocker]
    next_reminders: list[Reminder]

    # Meta
    session_id: str
    timestamp: datetime
```

---

## Part 2: SQLite Schema

```sql
-- Core goals table
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    scope TEXT CHECK(scope IN ('immediate', 'project', 'life')),
    status TEXT CHECK(status IN ('active', 'paused', 'completed', 'abandoned')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_at TIMESTAMP,
    time_scale TEXT,

    parent_goal_id TEXT REFERENCES goals(id),
    why TEXT,
    inferred BOOLEAN DEFAULT FALSE,
    confidence REAL DEFAULT 1.0,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Milestones (sub-goals)
CREATE TABLE milestones (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    title TEXT NOT NULL,
    due_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    progress_current REAL DEFAULT 0,
    progress_target REAL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Progress tracking
CREATE TABLE goal_progress (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_value REAL,
    note TEXT,
    session_id TEXT
);

-- Blockers
CREATE TABLE goal_blockers (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    title TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution TEXT
);

-- Goal relationships
CREATE TABLE goal_relationships (
    source_goal_id TEXT NOT NULL REFERENCES goals(id),
    target_goal_id TEXT NOT NULL REFERENCES goals(id),
    relation_type TEXT,  -- "enables" | "blocks" | "relates_to"
    PRIMARY KEY (source_goal_id, target_goal_id)
);

-- Goals mentioned in conversations
CREATE TABLE goal_mentions (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    conversation_id TEXT,
    turn_number INT,
    timestamp TIMESTAMP,
    context TEXT
);

-- Values alignment
CREATE TABLE goal_values (
    goal_id TEXT NOT NULL REFERENCES goals(id),
    value TEXT,
    PRIMARY KEY (goal_id, value)
);

-- Indices
CREATE INDEX idx_goals_user_status ON goals(user_id, status);
CREATE INDEX idx_goal_mentions_timestamp ON goal_mentions(goal_id, timestamp DESC);
CREATE INDEX idx_milestones_due ON milestones(goal_id, due_at);
```

---

## Part 3: Integration with Orchestrator

### 3.1 Extended ConversationContext

```python
@dataclass
class ConversationContext:
    # Existing fields from daemon-orchestrator-implementation.md
    user_input: str
    conversation_history: list[Message]
    relevant_memories: list[Memory]
    personality: PersonalityConfig
    available_tools: list[ToolDefinition]
    timestamp: datetime
    session_id: str

    # NEW: Goal and intent tracking
    active_context: ActiveContext
    inferred_intent: Optional[Intent]
    relevant_goals: list[Goal]
    upcoming_reminders: list[Reminder]
```

### 3.2 Intent Inference Step

Add to conversation loop before generation:

```python
async def conversation_loop():
    while True:
        user_input = await get_input()
        context = await build_context(user_input)

        # NEW: Infer intent
        context.inferred_intent = await infer_intent(user_input, context)

        if context.inferred_intent:
            context.active_context.current_intent = context.inferred_intent
            await check_goal_alignment(context.inferred_intent, context)

        response = await generate_with_tools(context)
        await update_memory(user_input, response, context.inferred_intent)
        await output_response(response)
```

### 3.3 Intent Inference Prompt

```python
async def infer_intent(user_input: str, context: ConversationContext) -> Optional[Intent]:
    inference_prompt = f"""
    Analyze this message and infer the user's intent and goals.

    Message: "{user_input}"
    Active goals: {format_active_goals(context.active_context.recently_mentioned_goals)}
    Session context: {context.conversation_history[-3:]}

    Return JSON:
    {{
        "has_explicit_goal": bool,
        "primary_goal_id": str or null,
        "task": str,
        "motivation": str,
        "urgency": "low" | "medium" | "high",
        "relates_to_existing_goal": bool,
        "new_goal_title": str or null,
        "coherence_score": 0.0-1.0
    }}
    """

    result = await llm.generate(inference_prompt)
    return parse_intent_from_result(result)
```

---

## Part 4: Goal-Aware Prompt Injection

```python
def format_system_prompt(
    personality: PersonalityConfig,
    memories: list[Memory],
    active_context: ActiveContext
) -> str:

    goal_section = ""

    if active_context.recently_mentioned_goals:
        goal_section += "\n## Their Current Focus\n"
        for goal in active_context.recently_mentioned_goals[:3]:
            goal_section += f"- {goal.title} (due {goal.due_at}, {goal.progress}% complete)\n"

    if active_context.open_blockers:
        goal_section += "\n## Known Blockers\n"
        for blocker in active_context.open_blockers[:2]:
            goal_section += f"- {blocker.title}\n"

    if active_context.next_reminders:
        goal_section += "\n## Approaching Deadlines\n"
        for reminder in active_context.next_reminders[:2]:
            goal_section += f"- {reminder.goal.title} due {reminder.due_at}\n"

    return f"""
{personality.to_system_prompt()}

## What I Know About You

{format_memories(memories)}
{goal_section}
"""
```

---

## Part 5: Goal Extraction from Conversation

### 5.1 Pattern Matching

```python
GOAL_PATTERNS = {
    "want_to": r"I\s+(?:want|need|would\s+like)\s+(?:to|to\s+be)\s+(.+?)(?:\.|$|,)",
    "trying_to": r"I'm\s+(?:trying|working)\s+(?:on|to)\s+(.+?)(?:\.|$|,)",
    "learning": r"(?:learn|study|master)\s+(.+?)(?:\s+to|\.|$|,)",
    "planning": r"I'm\s+(?:planning|thinking about)\s+(.+?)(?:\.|$|,)",
    "goal_statement": r"(?:My goal|My aim|I aim)\s+(?:is\s+)?(?:to\s+)?(.+?)(?:\.|$|,)",
}

async def extract_goals_from_message(user_input: str) -> list[Goal]:
    extracted = []

    for pattern_type, pattern in GOAL_PATTERNS.items():
        matches = re.findall(pattern, user_input, re.IGNORECASE)
        for match in matches:
            goal = Goal(
                id=generate_id("goal"),
                title=match.strip(),
                scope="project",
                inferred=True,
                confidence=0.7
            )
            extracted.append(goal)

    return extracted
```

### 5.2 LLM-Based Extraction

```python
extraction_prompt = f"""
Extract any implicit goals from this message:
"{user_input}"

Return JSON array:
[
    {{
        "title": "...",
        "scope": "immediate|project|life",
        "confidence": 0.0-1.0,
        "why": "reason user might have this goal"
    }}
]
"""
```

### 5.3 Confirmation Pattern

```python
async def present_inferred_goals(inferred_goals: list[Goal]) -> list[Goal]:
    high_confidence = [g for g in inferred_goals if g.confidence > 0.8]
    low_confidence = [g for g in inferred_goals if g.confidence <= 0.8]

    message = ""
    if high_confidence:
        message += "I notice you're working on:\n"
        for g in high_confidence:
            message += f"- {g.title}\n"

    if low_confidence:
        message += "\nAre you also interested in:\n"
        for g in low_confidence:
            message += f"- {g.title}?\n"

    return await get_user_confirmation(message)
```

---

## Part 6: Integration with Mem0

### 6.1 Sync Goals to Memory

```python
async def sync_goal_to_memory(goal: Goal, user_id: str):
    facts = [
        f"Goal: {goal.title}",
        f"Why: {goal.why}",
        f"Due: {goal.due_at.strftime('%B %Y') if goal.due_at else 'Open-ended'}",
        f"Timeline: {goal.time_scale}",
        f"Progress: {goal.progress.current}/{goal.progress.target} {goal.progress.unit}",
        f"Values: {', '.join(goal.values_aligned)}",
    ]

    for fact in facts:
        memory.add(
            fact,
            user_id=user_id,
            metadata={"goal_id": goal.id},
            tags=goal.tags + [goal.id]
        )
```

### 6.2 Goal-Aware Retrieval

```python
async def get_relevant_context(query: str, user_id: str):
    # Semantic search in Mem0
    memories = memory.search(query, user_id=user_id, limit=10)

    # Also search goals
    goal_matches = await search_goals(query, user_id=user_id, limit=5)

    # Filter to active
    active_goals = [g for g in goal_matches if g.status == "active"][:3]

    return memories, active_goals
```

---

## Part 7: Goal Coherence and Drift Detection

### 7.1 Coherence Checking

```python
async def check_goal_alignment(intent: Intent, context: ConversationContext):
    for goal in context.active_context.recently_mentioned_goals:
        similarity = calculate_semantic_similarity(
            intent.task,
            f"{goal.title} {goal.why}"
        )

        if similarity < 0.5:
            intent.coherence_score = similarity

            if similarity < 0.3:
                # Consider gentle redirect
                pass
```

### 7.2 Goal Decay

```python
def calculate_goal_urgency(goal: Goal) -> float:
    if not goal.progress.last_updated:
        return 0.0

    days_since_update = (datetime.now() - goal.progress.last_updated).days
    time_scale_days = {
        "days": 1,
        "weeks": 7,
        "months": 30,
        "years": 365
    }.get(goal.time_scale, 30)

    decay_factor = days_since_update / time_scale_days
    return min(1.0, decay_factor)
```

---

## Part 8: Reminders and Notifications

```python
async def check_and_send_reminders(context: ConversationContext) -> list:
    now = datetime.now()
    upcoming = []

    # Goals due soon
    for goal in context.active_context.recently_mentioned_goals:
        if goal.due_at and goal.due_at - now < timedelta(days=7):
            upcoming.append({
                "type": "deadline",
                "goal": goal,
                "days_left": (goal.due_at - now).days
            })

    # Milestones
    for goal in context.active_context.recently_mentioned_goals:
        for milestone in goal.milestones:
            if milestone.status != "completed" and milestone.due_at:
                if milestone.due_at - now < timedelta(days=7):
                    upcoming.append({
                        "type": "milestone",
                        "milestone": milestone,
                        "goal": goal
                    })

    # Open blockers
    for blocker in context.active_context.open_blockers:
        if blocker.created_at > now - timedelta(days=14):
            upcoming.append({"type": "blocker", "blocker": blocker})

    return upcoming[:5]
```

---

## Part 9: Design Patterns

### Pattern 1: Multi-Scale Temporal Tracking

```
Life Goals (1-10 years)
    ↓ decomposes into
Project Goals (1-12 months)
    ↓ decomposes into
Immediate Intents (minutes to hours)
```

### Pattern 2: Inference + Confirmation

```
Pattern-extracted (confidence 0.7) → Ask user
LLM-extracted (confidence 0.6-0.8) → Ask user
Explicit statement (confidence 1.0) → Store directly
```

### Pattern 3: Hyper-Local Context

Keep frequently-needed goals in fast memory:

```python
active_context = {
    current_intent: fresh,
    recently_mentioned: TTL 1 hour,
    upcoming_reminders: TTL 1 week,
    all_goals: retrieved from slow store on demand
}
```

---

## Part 10: Implementation Phases

### Phase 1: Foundation
- [ ] Create SQLite schema
- [ ] Implement Goal, Intent, ActiveContext dataclasses
- [ ] Add goal CRUD functions

### Phase 2: Orchestrator Integration
- [ ] Extend ConversationContext
- [ ] Implement infer_intent()
- [ ] Add goal-aware prompt injection

### Phase 3: Inference
- [ ] Pattern-based goal extraction
- [ ] LLM-based inference
- [ ] User confirmation flow

### Phase 4: Memory Integration
- [ ] Sync goals to Mem0
- [ ] Goal-based retrieval
- [ ] Semantic goal search

### Phase 5: Polish
- [ ] Reminder system
- [ ] Goal drift detection
- [ ] Completion workflows

---

## References

- [IBM AI Agent Planning](https://www.ibm.com/think/topics/ai-agent-planning)
- [Agentic Planning in AI](https://www.emergentmind.com/topics/agentic-planning)
- [Goal-Oriented Architectures](https://medium.com/@malenezi/goal-oriented-architectures-the-backbone-of-agentic-ai-systems-495f8542c077)
- [Mem0 Memory System](https://mem0.ai/)
- [MemGuide: Intent-Driven Memory](https://arxiv.org/html/2505.20231)
- [LangGraph Plan-and-Execute](https://blog.langchain.com/planning-agents/)
- [OnGoal: Conversational Goal Tracking](https://arxiv.org/html/2508.21061v1)

---

*This completes the DAEMON research suite: memory, personality, LLM selection, TTS, STT, VLM, MCP/tools, orchestrator, interface, data ingestion, and now intent/goal tracking.*
