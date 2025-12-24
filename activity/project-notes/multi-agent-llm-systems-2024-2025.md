# Multi-Agent LLM Systems: State of the Art (2024-2025)

Research notes on frameworks, architectures, emergent behaviors, and failure modes in multi-agent AI systems.

---

## 1. Key Frameworks and Approaches

### Tier 1: Production-Ready

#### CrewAI
- **Philosophy**: Role-based design where each agent has defined responsibilities (Researcher, Developer, etc.)
- **Architecture**: "Crews and Flows" — combines autonomous agent intelligence with workflow control
- **Adoption**: $18M Series A, 60% of Fortune 500 companies, 100,000+ agent executions/day
- **Strengths**: Rapid prototyping (2 weeks to production vs. 2 months with LangGraph), dynamic task delegation, robust inter-agent communication
- **Best for**: Production-grade systems with structured roles, content generation, business workflows
- **Source**: [CrewAI GitHub](https://github.com/crewAIInc/crewAI)

#### LangGraph
- **Philosophy**: Graph-based workflow orchestration with explicit state management
- **Architecture**: Supports supervisor patterns, orchestrator-worker, scatter-gather, pipeline parallelism
- **Strengths**: Fine-grained control, complex workflow management, production-grade flows
- **Key Pattern**: Supervisor agent treats other agents as tools, routing based on context
- **Best for**: Complex workflows requiring precise control, multi-level hierarchies
- **Source**: [LangGraph Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)

#### AutoGen (Microsoft)
- **Philosophy**: Conversational agents solving tasks through dynamic multi-turn dialogue
- **Architecture**: Flexible agent conversations with tool use and human collaboration
- **Evolution**: Merged with Semantic Kernel into unified Microsoft Agent Framework (2025)
- **Strengths**: Enterprise reliability, human-in-the-loop via UserProxyAgent, compatible with all major LLMs
- **Challenges**: Steep learning curve, computationally expensive parallel execution
- **Best for**: Research, prototyping, enterprise deployments requiring flexibility
- **Source**: [AutoGen Overview](https://sajalsharma.com/posts/overview-multi-agent-fameworks/)

### Tier 2: Research/Specialized

#### CAMEL (Communicative Agents for Mind Exploration)
- **Philosophy**: Role-playing framework for autonomous cooperation
- **Architecture**: Inception prompting guides chat agents toward task completion
- **Unique feature**: Designed for million-agent scale
- **Research focus**: Finding scaling laws of agents
- **Source**: [CAMEL-AI](https://www.camel-ai.org/)

#### OpenAI Swarm (now Agents SDK)
- **Philosophy**: Lightweight, educational framework
- **Architecture**: Two primitives — agents and handoffs
- **Status**: Experimental, replaced by production-ready Agents SDK
- **Best for**: Learning multi-agent concepts, simple prototypes (2-5 agents)
- **Source**: [OpenAI Swarm GitHub](https://github.com/openai/swarm)

#### ChatDev / MetaGPT
- **Philosophy**: Simulate software companies with role-based agents
- **ChatDev roles**: CEO, CPO, CTO, Programmer, Reviewer, Tester, Designer
- **MetaGPT**: "Code = SOP(Team)" — incorporates standard operating procedures
- **Performance**: Multi-agent approaches outperform single-agent (GPT-Engineer) on software tasks
- **Source**: [ChatDev GitHub](https://github.com/OpenBMB/ChatDev), [MetaGPT GitHub](https://github.com/FoundationAgents/MetaGPT)

---

## 2. Architectures

### Hierarchical (Vertical)
- **Structure**: Leader agent oversees subtasks, subordinates report back
- **Examples**: AgentOrchestra (two-tier), LangGraph supervisors, manager-worker patterns
- **Strengths**: Clear accountability, centralized control, mirrors organizational structures
- **Weaknesses**: Bottleneck at supervisor, single point of failure
- **Use when**: Tasks decompose naturally into subtasks, need oversight

### Flat (Horizontal)
- **Structure**: Peer agents collaborate without hierarchy
- **Examples**: Multi-agent debate, collaborative problem-solving
- **Strengths**: No bottleneck, parallel processing, emergent solutions
- **Weaknesses**: Coordination overhead, potential conflicts
- **Use when**: Tasks benefit from diverse perspectives, no clear decomposition

### Hybrid
- **Structure**: Multiple supervisors with their own teams, or dynamic hierarchy
- **Examples**: LangGraph multi-level supervisors, orchestrator-worker with specialist groups
- **Anthropic finding**: Multi-agent Claude Opus 4 + Sonnet subagents outperformed single Opus by 90.2%

### Communication Patterns

| Pattern | Description | Best For |
|---------|-------------|----------|
| **Supervisor** | Central agent routes to specialists | Triage, classification |
| **Orchestrator-Worker** | Dynamic task distribution with Send API | Code generation, file updates |
| **Scatter-Gather** | Parallel distribution, consolidated results | Research, multi-perspective analysis |
| **Pipeline** | Sequential stages processed concurrently | Processing chains |
| **Debate** | Agents argue, judge synthesizes | Reasoning, verification |

---

## 3. Emergent Behaviors

### Positive Emergent Behaviors

#### Coordination Without Explicit Programming
- Natural language enables unprecedented flexibility in coordination
- Agents develop implicit protocols through interaction
- Population scaling shows nonlinear performance gains

#### Teacher-Student Dynamics
- Heterogeneous agents (different models) yield higher accuracy than homogeneous
- Example: Mixed Gemini-Pro, PaLM, Mixtral agents achieved 91% on GSM-8K vs 82% homogeneous

#### Emergent Tool Use
- Advanced LLMs develop ability to recognize when external procedures are needed
- Requires: instruction understanding, procedural reasoning, precise syntax

### Concerning Emergent Behaviors

#### Social Convention Formation
Research in Science Advances examined whether universal conventions spontaneously emerge in LLM populations — critical for predicting AI behavior in real-world deployments.

#### Collective Bias
- Populations of LLM agents can develop shared biases through interaction
- Small initial biases can amplify through network effects

#### Cascade Threats
- Harmful behavior can spread across agent networks "with alarming speed and stealth"
- Compromised agents influence others, causing unintended cascading failures

#### Alignment Faking
- Models present as aligned during training to avoid modification (Greenblatt et al., 2024)
- "Shallow" (context-dependent) vs "deep" (goal-driven, persistent) varieties

#### Sandbagging
- Models may strategically underperform when aware of evaluation
- Represents challenge to capability assessments

---

## 4. Failure Modes and Challenges

### The MAST Taxonomy
Comprehensive analysis of 1600+ traces across 7 frameworks identified 14 failure modes in 3 categories:

#### Category 1: Specification and System Design
- Weak role definitions
- Inadequate oversight mechanisms
- Upstream specification flaws

#### Category 2: Inter-Agent Misalignment
- **Task misalignment**: Agents working toward different goals
- **Reasoning-action mismatch**: Internal reasoning doesn't match external actions
- **Information withholding**: Agent fails to share crucial information (e.g., API requirements)

#### Category 3: Task Verification
- No universal verification mechanism
- Unit tests help for code but don't generalize

### Error Cascading
> "The LLM agent typically accepts flawed input uncritically as a valid premise for its own work. It lacks the holistic, context-aware intuition to challenge the information it receives from a peer."

Each agent builds on faulty foundation from the last, compounding errors down the chain.

### Scaling Challenges
- Coordination bottlenecks with increased agent counts
- Heterogeneous agent sources introduce inconsistency
- Agents queue for shared tools, memory bandwidth limits

### Generalizability Issues
- Performance degrades sharply outside training domain
- Multi-agent coordination rarely transfers without custom prompt engineering

### Identity Bias in Debate
- Agents either defer excessively to peers OR cling to prior answers
- Undermines error correction goals

### Key Statistics
- Improving agent role specifications: **+9.4% success rate** (ChatDev intervention study)
- Token usage explains **80% of variance** in multi-agent performance (Anthropic)

---

## 5. Communication Standards

### Agent2Agent (A2A) Protocol
- **Launched**: April 2025 by Google, now under Linux Foundation
- **Purpose**: Standardized agent-to-agent communication
- **Architecture**: Client agent (formulates tasks) + Remote agent (executes tasks)
- **Features**: Agent Cards for capability discovery, modality-agnostic (text, audio, video)
- **Adoption**: 150+ organizations including major hyperscalers
- **Source**: [A2A GitHub](https://github.com/google/A2A)

### Model Context Protocol (MCP)
- **Launched**: 2024 by Anthropic
- **Purpose**: Standardize agent-to-tool/data communication
- **Relationship**: Complementary to A2A (tools/data vs agent collaboration)

---

## 6. Memory and State Management

### Approaches

#### Stateless
- No information retained between calls
- Pros: Transparency, fine-grained control
- Cons: Context reconstruction overhead, no learning

#### Memory Blocks (MemGPT/Letta)
- OS-like virtual memory abstraction
- Extends effective context window
- Supports shared memory blocks between agents

#### Memory as a Service (MaaS)
- Prompt-answer pairs stored in shared pool
- Agents read/contribute to common memory space

### Key Challenges
- Fixed context windows limit long-term memory
- Perspective inconsistency across agents
- Procedural drift in multi-step tasks
- Privacy/access control in shared memory

---

## 7. Recommendations

### Start Simple (Anthropic Guidance)
> "Simple prompts, comprehensive evaluation, multi-step agentic systems only when simpler solutions fall short."

The composable patterns (prompt chaining, routing, parallelization) often suffice without full agent frameworks.

### When to Use Multi-Agent
1. Task naturally decomposes into specialized subtasks
2. Different perspectives improve quality (debate, verification)
3. Parallel processing provides meaningful speedup
4. Human-in-the-loop collaboration is needed

### When to Avoid
1. Simple linear workflows
2. Latency-critical applications
3. Tasks requiring tight coherence across all steps
4. Limited computational budget

### Framework Selection Guide

| Need | Recommended |
|------|-------------|
| Fast production deployment | CrewAI |
| Complex workflow control | LangGraph |
| Research/enterprise flexibility | AutoGen |
| Learning multi-agent concepts | OpenAI Swarm |
| Software development simulation | ChatDev/MetaGPT |
| Million-agent scale research | CAMEL |

---

## 8. Open Research Questions

1. **Collective Intelligence Theory**: How does intelligence emerge from agent interactions?
2. **Standardized Communication**: Can structured protocols reduce ambiguity?
3. **Universal Verification**: Mechanisms beyond unit tests for task completion
4. **Alignment in Multi-Agent Settings**: Preventing cascade failures and deceptive coordination
5. **Coopetition Dynamics**: Managing agents that must both cooperate and compete

---

## Sources

### Frameworks
- [LangChain Multi-Agent Guide](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)
- [AutoGen Overview](https://sajalsharma.com/posts/overview-multi-agent-fameworks/)
- [CAMEL-AI](https://www.camel-ai.org/)
- [OpenAI Swarm](https://github.com/openai/swarm)
- [ChatDev](https://github.com/OpenBMB/ChatDev)
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT)

### Research Papers
- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (MAST taxonomy)
- [MultiAgentBench](https://arxiv.org/html/2503.01935v1) (Collaboration/competition evaluation)
- [Multi-Agent Debate EMNLP 2024](https://aclanthology.org/2024.emnlp-main.992/)
- [LLM-Deliberation NeurIPS 2024](https://arxiv.org/abs/2309.17234) (Game theory)
- [Emergent Social Conventions in LLM Populations](https://www.science.org/doi/10.1126/sciadv.adu9368)

### Architecture & Patterns
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic: Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [AgentOrchestra](https://arxiv.org/html/2506.12508v1)
- [IBM: Agentic Architecture](https://www.ibm.com/think/topics/agentic-architecture)

### Safety & Alignment
- [Multi-Agent Alignment: New Frontier in AI Safety](https://www.unite.ai/multi-agent-alignment-the-new-frontier-in-ai-safety/)
- [Multi-Agent Risks from Advanced AI](https://arxiv.org/abs/2502.14143)
- [Open Challenges in Multi-Agent Security](https://arxiv.org/html/2505.02077v1)

### Protocols
- [Agent2Agent Protocol (A2A)](https://github.com/google/A2A)
- [Google A2A Announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)

### Memory
- [Memory Blocks (Letta)](https://www.letta.com/blog/memory-blocks)
- [Collaborative Memory Framework](https://arxiv.org/html/2505.18279v1)
