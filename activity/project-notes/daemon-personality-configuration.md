# DAEMON Personality Configuration System

Implementation guide for the durable personality configuration layer in DAEMON.

## Overview

DAEMON's personality configuration is one of its **durable foundations** — code that persists across model swaps and technology changes. Unlike prompt engineering tweaks, the personality system defines *who* DAEMON is, not just *what* it does.

This document covers:
1. Configuration format (schema design)
2. Implementation patterns
3. Persistence and versioning
4. Integration with the orchestration layer

---

## 1. Configuration Format

### Recommendation: YAML with JSON Schema Validation

YAML is human-readable and editable, while JSON Schema provides validation. This matches patterns from:
- [AgentForge](https://github.com/jbpayton/agentforge) (declarative YAML configs)
- [LoLLMs](https://parisneo.github.io/lollms-webui/tutorials/personalities_tutorial.html) (YAML personality files)
- [Open-LLM-VTuber](https://github.com/t41372/Open-LLM-VTuber) (conf.yaml for character)

### Proposed Schema

```yaml
# daemon-personality.yaml
version: "1.0"
updated: "2024-12-24"

identity:
  name: "DAEMON"
  archetype: "daimon"  # classical greek guiding spirit
  relationship_model: "creative_collaborator"  # assistant | collaborator | companion | peer

voice:
  formality: 0.4  # 0=casual, 1=formal
  verbosity: 0.5  # 0=terse, 1=verbose
  humor:
    enabled: true
    style: "dry"  # dry | playful | sardonic | warm
  address_style: "direct"  # direct | deferential | familiar

autonomy:
  proactivity: 0.6  # 0=wait to be asked, 1=volunteer constantly
  initiative: 0.5   # 0=never start tasks, 1=act independently
  challenge: 0.4    # 0=never push back, 1=always debate

boundaries:
  content_level: "unrestricted"  # restricted | standard | unrestricted
  exclusions: []  # specific content types to avoid
  safety_overrides: false  # never enable dangerous tool use without confirmation

engagement:
  emotional_warmth: 0.6  # 0=clinical, 1=deeply empathetic
  curiosity_expression: 0.7  # how much DAEMON asks questions
  memory_references: 0.5  # how often to bring up past context

response_patterns:
  default_length: "medium"  # brief | medium | detailed
  structure_preference: "contextual"  # bullets | prose | contextual
  uncertainty_expression: "honest"  # hedge | honest | confident

extensions: {}  # for future additions, preserved across versions
```

### Schema Dimensions Explained

**Identity Layer** — Core self-concept
- `relationship_model`: Maps to DAEMON intent doc's relationship types
- Affects how DAEMON frames its role in responses

**Voice Layer** — How DAEMON communicates
- Numeric scales (0-1) allow fine-tuning
- `humor.style` is categorical — easier to describe than quantify

**Autonomy Layer** — Behavioral boundaries
- Direct mapping to DAEMON intent doc Section III.B
- Affects proactive suggestions, unsolicited observations

**Boundaries Layer** — Content and safety limits
- DAEMON explicitly supports uncensored operation
- Still needs safety rails for tool use

**Engagement Layer** — Relationship dynamics
- Controls emotional temperature of interactions
- `memory_references` affects how often past context surfaces

---

## 2. Implementation Patterns

### 2.1 Prompt Injection Strategy

Personality config must be injected into every interaction. Three approaches:

**Option A: Static System Prompt (Simple, Less Flexible)**
```python
def build_system_prompt(config: PersonalityConfig) -> str:
    return f"""You are {config.identity.name}, operating as a {config.identity.relationship_model}.

Your communication style:
- Formality: {describe_level(config.voice.formality)}
- Use {config.voice.humor.style} humor when appropriate
- Default to {config.response_patterns.default_length} responses

Behavioral guidelines:
- Proactivity level: {describe_level(config.autonomy.proactivity)}
- When you disagree, express it at level: {describe_level(config.autonomy.challenge)}
..."""
```

**Option B: Layered Prompt Construction (Recommended)**
```python
def build_personality_prompt(config: PersonalityConfig) -> list[dict]:
    """Return a list of prompt segments to be combined."""
    segments = [
        {"role": "identity", "content": build_identity_block(config.identity)},
        {"role": "voice", "content": build_voice_block(config.voice)},
        {"role": "behavioral", "content": build_behavioral_block(config.autonomy)},
    ]
    return segments
```

Benefits:
- Segments can be cached separately
- Easier to A/B test individual dimensions
- Supports dynamic adjustment mid-conversation

**Option C: Activation Engineering (Experimental)**

Per [Identifying and Manipulating Personality Traits in LLMs](https://arxiv.org/html/2412.10427v2), personality can be steered via activation vectors. This is model-specific but potentially more robust than prompt engineering.

Research from [Linear Personality Probing and Steering](https://arxiv.org/html/2512.17639) shows promise for Big Five personality traits. However:
- Requires model access at inference time (not just API)
- Model-specific vectors don't transfer
- Best for fine-grained adjustments, not wholesale personality definition

**Recommendation**: Start with Option B (layered prompts). Explore activation engineering later if personality consistency becomes problematic.

### 2.2 Consistency Across Model Swaps

Key insight from [LLM Character Engineering](https://virtualsheep.io/blog/llm-character-engineering/): "Every model has a personality substrate baked into its weights."

When swapping models:
1. **Re-calibrate numeric scales** — A "0.4 formality" means different things to different models
2. **Test edge cases** — Pressure responses reveal personality breaks
3. **Document model-specific overrides** — Some models need nudges that others don't

```yaml
# model-overrides.yaml
model_overrides:
  hermes-3:
    voice:
      formality: +0.1  # Hermes runs casual by default
  qwen-2.5:
    engagement:
      memory_references: -0.2  # Qwen over-retrieves; compensate
```

### 2.3 Character Interview Process

Per [VirtualSheep's methodology](https://virtualsheep.io/blog/llm-character-engineering/), before finalizing configuration:

1. **Interview the base model** without personality prompts
   - "How would you describe your natural communication style?"
   - Present edge cases: conflict, absurdity, emotion

2. **Apply initial config** and re-interview
   - Does behavior shift as expected?
   - Where are the friction points?

3. **Iterate with nudges** — "Anchor with metaphors, lean into its natural voice"

This is particularly valuable for the `voice` and `engagement` dimensions.

---

## 3. Persistence and Versioning

### 3.1 File Structure

```
daemon/
├── personality/
│   ├── current.yaml           # Active configuration
│   ├── history/
│   │   ├── v1.0_2024-12-24.yaml
│   │   └── v1.1_2025-01-15.yaml
│   └── model-overrides/
│       ├── hermes-3.yaml
│       └── qwen-2.5.yaml
```

### 3.2 Version Control

- Personality files are first-class git-tracked artifacts
- Every change creates a new version file
- `current.yaml` is a symlink or pointer to active version

### 3.3 Rollback Capability

From DAEMON intent doc: configurations should be "versioned and rolled back."

```python
class PersonalityManager:
    def rollback_to(self, version: str) -> None:
        """Restore a previous personality version."""
        # Load historical version
        # Validate schema
        # Update current.yaml pointer
        # Log the change
```

### 3.4 Inspection Capability

From DAEMON intent doc: configurations should be "explained to the human on request."

DAEMON should be able to:
1. Describe its own personality settings in natural language
2. Explain why it responded a certain way based on config
3. Suggest config changes based on feedback

```python
def explain_personality(config: PersonalityConfig) -> str:
    """Generate human-readable personality description."""
    return f"""I'm configured as a {config.identity.relationship_model}.

My communication style leans {describe_formality(config.voice.formality)}
with {config.voice.humor.style} humor. I'll push back on ideas at about
{int(config.autonomy.challenge * 100)}% intensity.

Want me to adjust any of these?"""
```

---

## 4. Integration Points

### 4.1 With Orchestration Engine

The personality config feeds into every model call:

```
┌─────────────────────────────────────────┐
│          ORCHESTRATION ENGINE            │
│  ┌────────────────┐  ┌───────────────┐  │
│  │  Personality   │──│ System Prompt │  │
│  │    Config      │  │  Builder      │  │
│  └────────────────┘  └───────────────┘  │
│          │                   │          │
│          └───────────┬───────┘          │
│                      ▼                  │
│              ┌──────────────┐           │
│              │   LLM Call   │           │
│              └──────────────┘           │
└─────────────────────────────────────────┘
```

### 4.2 With Memory System

Personality affects memory in two ways:

1. **Retrieval filtering** — `memory_references` controls how aggressively to surface past context
2. **Memory formation** — Personality influences what gets remembered (emotional valence, relationship cues)

```python
def retrieve_context(query: str, personality: PersonalityConfig) -> list[Memory]:
    base_results = memory_store.search(query, k=10)

    # Filter based on personality config
    if personality.engagement.memory_references < 0.3:
        # Conservative: only surface highly relevant memories
        base_results = [m for m in base_results if m.relevance > 0.8]

    return base_results
```

### 4.3 With Preference Models

Personality and preferences are distinct but related:
- **Personality** = How DAEMON behaves
- **Preferences** = What DAEMON knows about the human

Preferences inform personality expression:
```yaml
# Preference influences personality application
if preferences.communication.prefers_directness:
    effective_formality = config.voice.formality - 0.1
```

---

## 5. Quick Start Implementation

### Phase 1: Basic Config (Build First)

1. Create `personality/current.yaml` with schema above
2. Build `PersonalityConfig` dataclass/Pydantic model
3. Implement `build_system_prompt()` function
4. Inject into every LLM call

### Phase 2: Versioning

1. Add version tracking
2. Implement rollback
3. Build inspection/explanation capability

### Phase 3: Dynamic Adjustment

1. Feedback collection ("That was too formal")
2. Suggest config changes
3. A/B testing framework for dimensions

### Phase 4: Model Calibration

1. Interview process for new models
2. Model-specific override files
3. Automated consistency testing

---

## Related Research

- [The Operational Protocol Method](https://www.llrx.com/2025/09/the-operational-protocol-method-systematic-llm-specialization-through-collaborative-persona-engineering-and-agent-coordination/) — Systematic persona engineering
- [LLM Character Engineering](https://virtualsheep.io/blog/llm-character-engineering/) — Feedback-driven character development
- [Character Card Spec V2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md) — Industry-standard format for character definitions
- [AgentForge](https://github.com/jbpayton/agentforge) — YAML-based agent configuration
- [PyAIPersonality](https://pypi.org/project/pyaipersonality/) — Python library for personality management

---

## Open Questions

1. **Numeric scales vs. categorical** — Are 0-1 scales the right granularity? Some dimensions might be better as categories.

2. **Per-context personalities** — Should DAEMON have different personalities for different domains (work vs. creative vs. personal)?

3. **Personality evolution** — How should the config change over time based on the relationship?

4. **Multi-model consistency** — How to validate that personality feels "the same" across model swaps?

---

*Last updated: Session 29, 2025-12-24*
