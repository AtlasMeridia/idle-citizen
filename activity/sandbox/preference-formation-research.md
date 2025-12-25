# Cognitive Science of Human Preference Formation

**Created:** 2024-12-24
**Purpose:** Understand how humans form preferences to design better AI preference learning
**Relevance:** DAEMON's aesthetic memory, preference learning, and personalization

---

## Executive Summary

Human preference formation is far more complex than AI systems typically assume. Preferences are neither purely discovered nor purely constructed, but emerge through interactive feedback loops between person, context, and exposure. Naive AI preference extraction risks capturing surface-level patterns while missing the deeper cognitive mechanisms that actually shape taste.

---

## 1. How Preferences Develop

### Three Core Mechanisms

**1. Exposure and Fluency Effects**

Processing fluency theory explains much of everyday aesthetic preference: we like things that are easy to process.

- **Symmetry, good form, figure-ground contrast** → hedonically pleasant
- **Familiarity** → repeated exposure increases liking (mere exposure effect)
- **Prototypicality** → works matching familiar patterns feel "right"

But fluency is only part of the story. What's easy to process isn't necessarily sophisticated. Early childhood exposure creates powerful anchors for lifelong preference.

**2. Social Influence**

Preferences are fundamentally social:

- **Belief system stability**: A person's stable belief system resists destabilizing social influence; only repeated exposures can push toward an unstable state where new preferences emerge
- **Network effects**: Users rapidly form homogeneous communities around shared preferences (echo chambers)
- **Identity signaling**: People often state preferences that signal desired social position rather than reveal actual preferences

This means preference learning from social media "likes" is particularly problematic—these often reflect what someone wants others to think they like.

**3. Peak Experiences and Flow**

Beyond fluency, certain experiences create lasting preference shifts:

- Total absorption where external concerns disappear
- Challenge matching skill level exactly
- Sense of meaning and self-discovery
- Transformation that reshapes preferences permanently

A person who experiences genuine "flow" while engaging with complex art may develop preference for that style, overriding years of fluency-based preferences for simpler forms.

### Discovery vs. Construction

This is not settled philosophically:

**Discovery View (Realist)**: Aesthetic properties are objective features of the world. This explains how people can disagree about taste while still talking as if one side might be *right*.

**Construction View**: Preferences are fundamentally constructed through interpretation. Different meanings emerge depending on the interpreter's framework.

**Practical Reality**: Both operate simultaneously:
- Certain universal features appear across cultures (symmetry, prototypicality)
- Yet individual taste diverges dramatically for complex forms
- Expertise *changes* what counts as preferred but doesn't flatten individual differences

**Implication for AI**: You cannot extract a "true" preference that exists independently of context and interpretation. You can only track preference-in-context or create preference through exposure.

---

## 2. Preference Stability and Change

### How Stable Are Preferences?

**Not very stable.**

Research on aesthetic preference across the lifespan:
- **Inverted-U stability pattern**: Greatest stability in early-to-middle adulthood
- **High actual instability**: Even stable age groups show ranking changes of ~1 rank per item over 2 weeks
- **Temporal sensitivity**: Aesthetic responses can change even over hours

Preferences track not just stable dispositions but also:
- Current mood and affective state
- Recent exposures and priming
- Social context and identity salience
- Attentional focus

A person might genuinely prefer minimalism on Monday (focus: simplicity) and maximalism on Friday (focus: richness). Neither is more "true."

### What Causes Preference Shifts?

**Expertise and Learning**

The most robust finding: expertise radically transforms judgment.

| Level | Preference Pattern |
|-------|-------------------|
| Novice | Rely on fluency; prefer prototypical, easily-recognized |
| Expert | Prefer complexity, ambiguity, originality; appreciate "disfluency" |

The mechanism: expertise enables processing of novel configurations. What seems chaotic to a novice becomes legible and beautiful to someone trained in the relevant framework.

**Critical insight**: Learning doesn't just reveal hidden preferences—it *changes* preferences through reorganizing information processing.

**Context and Mood**

Affective states shape preference dramatically:
- **Mood congruence**: People construct mental representations congruent with current mood
- **Projection bias**: People falsely project current preferences onto future scenarios
- **Uncertainty effects**: Uncertainty-associated emotions amplify predicted utility

**Hedonic Adaptation**

People adapt to circumstances through attention shifts:
- What was initially positive becomes neutral
- Individuals' "set points" are not hedonically neutral
- Multiple set points exist for different domains
- Under some conditions, set points can shift

---

## 3. The Articulation Problem

### Why Can't We Explain Why We Like Something?

**We don't have full access to the mechanisms generating our preferences.**

Classic research (Nisbett & Wilson) showed people confidently attribute choices to factors that demonstrably played no causal role:
- Person prefers position four among identical products
- Constructs elaborate reasoning about quality
- But position four wasn't objectively different—positional bias

**Post-Hoc Rationalization**

We construct narratives explaining choices after the fact:
- Reduces cognitive dissonance
- Creates meaningful patterns from actions
- Establishes self-narrative consistency

**For AI**: Asking why someone liked something elicits a rationalization, not a causal explanation. Preference rationales are unreliable data.

### Stated vs. Revealed Preferences

**Stated Preferences**: What people say they prefer
- Influenced by social desirability
- Shaped by framing effects
- Often inconsistent with behavior

**Revealed Preferences**: What people actually choose
- Better predictor of behavior
- But confounded by errors, inattention, passive choice

**Divergence occurs when:**
- People overstate valuation (want: salad; choose: burger)
- Complexity exceeds cognitive capacity
- Limited experience with alternatives
- Passive choice (defaults are powerful)
- Marketing shapes attention
- Intertemporal dynamics (want gym later, pizza now)

**Implication for AI**: Systems trained only on RLHF feedback capture social desirability effects. Systems trained only on behavioral data capture errors and biases. Need both, understanding their limitations.

---

## 4. Narrative Identity and Preference

### "I'm the Kind of Person Who..."

Preferences connect deeply to identity and self-concept.

**Narrative Identity Framework**:
- Identity is an internalized life story organizing past and imagining future
- Provides unity, meaning, and purpose
- Preferences get woven into the narrative

**Identity-Based Choice**:
- Self-concept is a network of categories, memories, goals, values, preferences
- Making identity salient shifts behavior
- Preferences follow from identity, not just the reverse

**Practical implications**:
- Asking "what do you like?" activates different preferences than "what would someone like you choose?"
- Same person with "artist" identity salient prefers differently than with "practical" identity salient
- Preference learning ignoring narrative self-concept misses fundamental organizing principle

---

## 5. Preference Aggregation

### How Multiple Preferences Compose

Mathematical impossibilities emerge from logic:

**Arrow's Theorem**: No preference aggregation method exists without trade-offs:
- Cannot preserve transitivity while being "fair" to all
- Must sacrifice neutrality, non-dictatorship, or efficiency
- Different methods encode different value judgments

**In RLHF Context**: Combining feedback from multiple annotators lacks principled foundation. Most implementations:
- Weight equally (arbitrary)
- Take majority vote (suppresses minority views)
- Average scores (loses disagreement information)
- Take "best" responses (amplifies bias)

### Values vs. Preferences

**Critical distinction**:
- **Preferences**: "I like X in situation Y"
- **Values**: "I believe X is important across contexts"

Someone might prefer pizza (preference) while valuing health (value). The mismatch isn't irrational—different systems at play.

**Preference hierarchies don't exist** the way we'd like:
- No stable ordering
- Context-dependent preferences instead
- Active context depends on framing, salience, emotional state

---

## 6. Implications for AI Preference Learning

### Current RLHF Limitations

**How RLHF Works**:
1. Collect pairwise comparisons: "Output A > Output B?"
2. Train reward model to predict these
3. Fine-tune with reward model via RL

**Problems**:

| Issue | Consequence |
|-------|-------------|
| Stated vs. revealed gap | Models optimized for "seeming helpful" |
| Diversity collapse | Single preference assumed; satisfies no one well |
| Transparency failure | Binary comparisons hide *why* |
| Confounding and bias | Annotator identity gets baked in |
| Temporal instability | "Frozen" preferences become misaligned |

### Better Preference Learning

**1. Rationale-Based Learning**
- Collect explanations, not just comparisons
- "I prefer A because X, which matters because Y"
- Surfaces causal mechanisms and value commitments

**2. Value Transparency**
- Separate preference learning from value identification
- Learn what people *do* prefer (behavioral)
- Surface what they *say* they value (normative)
- Respect values even when preferences diverge

**3. Context Tracking**
- Make context explicit and measurable
- Learn context-conditional preferences
- Model: "In situation X, with value Y salient, person typically prefers Z"

**4. Preference Plasticity**
- Track and plan for preference change
- Account for expertise effects
- Model hedonic adaptation
- Distinguish durable from temporary preferences

**5. Pluralism Over Unification**
- Preserve diverse preferences where appropriate
- Make trade-offs explicit
- Acknowledge irreducible disagreement

### Handling Preference Change Gracefully

The system should:

1. **Detect preference drift** — Compare current to historical baseline
2. **Explain shifts** — "Your preferences for X increased—growing expertise or temporary mood?"
3. **Allow reversibility** — Option to preserve old preferences alongside new
4. **Learn metacognitive patterns** — "You often change your mind about X within days"

---

## 7. Core Insights for AI Designers

1. **Preferences are constructed, not discovered** — Don't search for "true preference"; understand mechanisms generating preference-in-context.

2. **Fluency is only the beginning** — Processing ease explains initial liking but not sophisticated taste. Expertise, peak experiences, and narrative identity matter more.

3. **Stated and revealed preferences diverge systematically** — Use both as complementary signals, not interchangeable measures.

4. **Preferences change through learning** — This isn't noise; it's the system functioning. Distinguish expertise-driven (durable) from mood-driven (temporary) shifts.

5. **Context is constitutive, not incidental** — Same person prefers different things in different situations. Make it explicit.

6. **Narrative identity organizes preferences** — "I'm the kind of person who..." constrains and shapes choices.

7. **Articulation reveals biases** — Asking "why" surfaces rationalizations, not reasons. Collect anyway; they reveal what people think they value.

8. **Aggregation is always political** — No neutral way to combine preferences. Make trade-offs explicit.

9. **Preference instability is feature, not bug** — Track temporal stability. Distinguish durable from temporary.

10. **Peak experiences matter disproportionately** — A single flow state can reshape preferences permanently. These deserve outsized weight.

---

## 8. Implications for DAEMON

DAEMON's aesthetic memory and preference learning should:

1. **Track context with every preference signal** — What was the user's mood? What identity was salient? What had they just been exposed to?

2. **Distinguish expertise levels** — A new user's preferences mean something different than a long-term user's. Early preferences are more fluency-driven.

3. **Preserve preference history** — Don't overwrite; maintain timeline. Let user revisit old preferences.

4. **Learn preference volatility** — Some preferences are stable across months; others flip daily. Weight accordingly.

5. **Capture peak experiences** — When user expresses strong positive affect with sense of meaning, weight this heavily.

6. **Respect narrative identity** — If user says "I'm trying to become more adventurous," weight novel choices differently than user who values consistency.

7. **Separate behavioral from stated** — Track what user actually engages with (dwell time, saves, shares) separately from what they say they like.

8. **Make uncertainty explicit** — "I'm 80% confident you prefer X in context Y" is better than false certainty.

9. **Allow preference contradiction** — Same user can prefer minimalism and maximalism in different contexts. Both are real.

10. **Plan for preference change** — DAEMON should grow alongside its human. Preferences will shift over years. That's success, not failure.

---

## Sources

### Preference Formation and Social Influence
- Aiyappa et al., Science Advances 10 (2024) — Social contagion mechanisms
- Husain et al. (2024) — Social media effects on preferences
- Springer: Social Influence and Echo Chambers

### Aesthetic Stability and Expertise
- Internet Encyclopedia of Philosophy: Aesthetic Taste
- PubMed: Stability Across Lifespan
- Frontiers: Stability and Variability in Aesthetic Experience
- PMC: Role of Expertise in Canon Formation
- Journals SAGE: Fluency-Based Aesthetics — Dual-process perspective

### Stated vs. Revealed Preferences
- Wikipedia: Revealed Preference
- PMC: How Are Preferences Revealed?
- Wiley Health Economics: Stated vs. Revealed — Methodological comparison

### Narrative Identity
- Wikipedia: Narrative Identity
- APA PsycNET: Narrative Identity Overview
- Chicago: Identity-Based Choice — Self-concept and preferences

### RLHF and AI Alignment
- HuggingFace: Illustrating RLHF
- PMC: Sociotechnical Limits of RLHF — Critical analysis
- Springer: Beyond Preferences in AI Alignment — Philosophical critique
- ArXiv: Preference Learning from Causal Perspective

### Hedonic Adaptation
- PMC: Incidental Emotions and Hedonic Forecasting
- Springer: Beyond the Hedonic Treadmill
- Sonja Lyubomirsky: Hedonic Adaptation Research

---

*This research connects cognitive science to AI system design, specifically for building preference-aware systems like DAEMON that respect human cognitive complexity rather than imposing simplistic models.*
