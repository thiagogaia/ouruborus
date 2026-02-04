<p align="center">
  <img src="logo.svg" width="180" alt="Engram"/>
</p>

<h1 align="center">Ouroborus v3</h1>

<p align="center">
  <strong>Self-evolving persistent memory for Claude Code.</strong><br/>
  <em>Each session ends smarter than it started. The system generates itself.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-6366f1?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/brain-organizational-8b5cf6?style=flat-square" alt="Brain"/>
  <img src="https://img.shields.io/badge/seeds-8-a78bfa?style=flat-square" alt="Seeds"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"/>
</p>

---

## What is it

Ouroborus transforms Claude Code into an agent that **learns from each session**, **remembers across conversations**, and **evolves its own capabilities**. It installs a metacircular system with an **organizational brain** — a knowledge graph with semantic search, cognitive processes, and persistent memory.

### Version History

| Version | Codename | Key Feature |
|---------|----------|-------------|
| v1 | Fixed | Static skills, manual evolution |
| v2 | Metacircular | Self-generating skills with genesis/evolution engines |
| **v3** | **Brain** | **Organizational memory with knowledge graph + embeddings** |

### v2 → v3: What changed

| Aspect | v2 | v3 (with brain) |
|--------|----|--------------------|
| Memory | Knowledge files only | **Knowledge graph + embeddings** |
| Search | Manual file reading | **Semantic search with /recall** |
| Recall | None | **Spreading activation retrieval** |
| Forgetting | None | **Ebbinghaus decay curve** |
| Consolidation | None | **Automatic connection strengthening** |
| Multi-project | One at a time | **Batch install multiple projects** |
| Seeds | 6 | **8 (+ 3 specialist agents)** |

## How it works

```
┌─ INSTALL (setup.sh) ─────────────────────────────────┐
│                                                       │
│  Detects stack → installs DNA (schemas) + genesis    │
│  + seed skills + brain (graph + embeddings)          │
│                                                       │
├─ GENESIS (/init-engram) ─────────────────────────────┤
│                                                       │
│  Analyzes project → generates custom skills/agents   │
│  → populates brain with existing knowledge           │
│  → validates against schemas → registers in manifest │
│                                                       │
├─ USE (daily work) ───────────────────────────────────┤
│                                                       │
│  /recall queries brain for relevant memories         │
│  Skills loaded on demand (progressive disclosure)    │
│  Agents forked for specialized tasks                 │
│                                                       │
├─ EVOLVE (/learn) ────────────────────────────────────┤
│                                                       │
│  Records knowledge → creates memories in brain       │
│  → tracks usage → detects patterns → proposes skills │
│  → cognitive processes (decay, consolidate, archive) │
│                                                       │
└────── 🐍 cycle repeats, each time smarter ───────────┘
```

## Quick Start

### 1. Clone

```bash
git clone https://github.com/your-user/engram.git ~/engram
```

### 2. Install

```bash
cd ~/engram
./setup.sh /path/to/your/project

# Or install in multiple projects at once:
./setup.sh ~/project1 ~/project2 ~/project3

# Batch mode (no prompts, for CI/CD):
./setup.sh --batch ~/project1 ~/project2
```

The installer detects your stack automatically:

| Detects | Examples |
|---------|----------|
| Language | Node.js, Python, PHP, Rust, Go, Ruby |
| Framework | Next.js, React, Vue, Angular, Django, Laravel, FastAPI |
| ORM | Prisma, Drizzle, TypeORM, Sequelize |
| Database | PostgreSQL, MySQL, MongoDB, SQLite, Supabase |
| UI | shadcn/ui, MUI, Chakra, Tailwind |
| Auth | NextAuth, Clerk, Lucia, Better Auth |
| Tests | Vitest, Jest, Playwright, Cypress |
| Infra | Docker, package manager, monorepo |

### 3. Generate with AI

```bash
cd /your/project
claude
/init-engram
```

Claude uses the **genesis skill** to analyze your project, generate custom skills/agents, populate the brain with existing knowledge, and run a health check.

### 4. Use

| Command | What it does |
|---------|--------------|
| `/recall [query]` | **Query the organizational brain** |
| `/status` | Project state, priorities, next action |
| `/plan [feature]` | Implementation plan with steps |
| `/review` | Code review of changed files |
| `/priorities` | Re-evaluate priorities with ICE Score |
| `/learn` | **Record knowledge + evolve system + feed brain** |
| `/commit` | Semantic git commit |
| `/create [type] [name]` | Generate new skill, agent, or command |
| `/spawn [type] [name]` | Fast runtime creation mid-task |
| `/doctor` | Health check of the Engram installation |
| `/curriculum` | Skill coverage analysis + suggestions |
| `/export [name]` | Export to global memory (~/.engram/) |
| `/import [name]` | Import from global memory |

## The Organizational Brain

The brain in `.claude/brain/` is a **knowledge graph** with semantic search capabilities:

```
brain/
├── brain.py          # Core (NetworkX graph + operations)
├── embeddings.py     # Semantic search (sentence-transformers)
├── cognitive.py      # Processes: consolidate, decay, archive
├── recall.py         # Query interface
├── populate.py       # Populate from existing data
├── graph.json        # Serialized graph (nodes + edges)
├── embeddings.npz    # Embedding vectors
└── cognitive-log.jsonl  # Audit log
```

### Memory Types

| Type | Label | Decay Rate | Example |
|------|-------|------------|---------|
| Decision | ADR | 0.001 (very slow) | ADR-001: Metacircular System |
| Concept | Concept | 0.003 (slow) | "What is Ouroboros" |
| Pattern | Pattern | 0.005 (slow) | PAT-005: Python Script Standard |
| Episode | Commit | 0.01 (medium) | Commit cb64fd73 |
| Person | Person | 0.0001 (almost never) | @developer |

### Cognitive Processes

Inspired by neuroscience:

1. **Encode** — Create memory with automatic edges
2. **Retrieve** — Search with spreading activation
3. **Consolidate** — Strengthen connections (weekly)
4. **Decay** — Ebbinghaus forgetting curve (daily)
5. **Archive** — Move weak memories (monthly)

### Querying the Brain

```bash
# Via command
/recall how does authentication work

# Via script
source .claude/brain/.venv/bin/activate
python3 .claude/brain/recall.py "authentication" --top 5

# Filter by type
python3 .claude/brain/recall.py "auth" --type ADR
```

## Architecture

```
your-project/
├── CLAUDE.md                          # Main instructions
└── .claude/
    ├── manifest.json                  # Component registry + metrics
    ├── settings.json                  # Permissions
    │
    ├── brain/                         # 🧠 Organizational Brain (v3)
    │   ├── brain.py                   #    Graph operations
    │   ├── embeddings.py              #    Semantic search
    │   ├── cognitive.py               #    Decay, consolidate, archive
    │   ├── recall.py                  #    Query interface
    │   ├── graph.json                 #    Knowledge graph
    │   └── embeddings.npz             #    Vector embeddings
    │
    ├── memory/                        # 📝 Memories (markdown)
    │   ├── episodes/                  #    Commits, events
    │   ├── concepts/                  #    Definitions, glossary
    │   ├── patterns/                  #    Approved patterns
    │   ├── decisions/                 #    ADRs
    │   └── people/                    #    Team members
    │
    ├── schemas/                       # 🧬 DNA — component definitions
    │   ├── skill.schema.md
    │   ├── agent.schema.md
    │   ├── command.schema.md
    │   └── knowledge.schema.md
    │
    ├── skills/                        # 🎯 Capabilities (8 seeds)
    │   ├── engram-genesis/            #    Self-generation engine
    │   ├── engram-evolution/          #    Self-evolution engine
    │   ├── engram-factory/            #    Runtime orchestration
    │   ├── project-analyzer/          #    Codebase analysis
    │   ├── knowledge-manager/         #    Feedback loop
    │   ├── domain-expert/             #    Business knowledge
    │   ├── priority-engine/           #    ICE Score
    │   ├── code-reviewer/             #    4-layer review
    │   └── [auto-generated]/          #    Project-specific
    │
    ├── agents/                        # 🤖 Specialists (3 universal)
    │   ├── architect.md               #    Architecture decisions
    │   ├── db-expert.md               #    Database optimization
    │   └── domain-analyst.md          #    Domain discovery
    │
    ├── commands/                      # ⚡ Slash commands (14)
    │
    └── knowledge/                     # 📚 Knowledge files
        ├── context/CURRENT_STATE.md
        ├── priorities/PRIORITY_MATRIX.md
        ├── patterns/PATTERNS.md
        ├── decisions/ADR_LOG.md
        ├── domain/DOMAIN.md
        └── experiences/EXPERIENCE_LIBRARY.md
```

## Architectural Inspirations

Engram v3 combines ideas from three research projects:

| Project | Concept | Implementation in Engram |
|---------|---------|-------------------------|
| **Voyager** (NVIDIA) | Compositional skill library | `composes:` in SKILL.md |
| **Darwin Gödel Machine** (Sakana AI) | Self-modifying system | Genesis generates itself |
| **BOSS** (USC/Google) | Skills emerge from patterns | /learn detects → proposes |

## The Evolution Cycle

During `/learn`, the evolution skill:

- Records knowledge in the brain (creates nodes + edges)
- Runs cognitive processes (decay, consolidate)
- Tracks which components were used
- Detects stale components → proposes archive
- Detects recurring patterns → proposes new skill
- Detects co-activation → proposes composition
- Versions any modified component

## CLI Options

```bash
./setup.sh                          # Install in current directory
./setup.sh /path/to/project         # Install in specific directory
./setup.sh proj1 proj2 proj3        # Install in multiple directories
./setup.sh --batch ~/proj1 ~/proj2  # Batch mode (no prompts)
./setup.sh --update proj1 proj2     # Update core, keep knowledge
./setup.sh --uninstall .            # Remove Engram cleanly
./setup.sh --help                   # Show help
./setup.sh --version                # Show version
```

## Brain Maintenance

For long-running projects, configure periodic cognitive processes:

```bash
# Manual
python3 .claude/brain/cognitive.py health      # Check brain health
python3 .claude/brain/cognitive.py decay       # Run decay (daily)
python3 .claude/brain/cognitive.py consolidate # Run consolidation (weekly)

# Via cron (recommended)
0 2 * * * cd /project && python3 .claude/brain/cognitive.py decay
0 3 * * 0 cd /project && python3 .claude/brain/cognitive.py consolidate
```

## .gitignore Guidance

**Commit everything** in `.claude/` — this is your project's memory:

```
# DO commit:
.claude/brain/graph.json      # Knowledge graph
.claude/brain/embeddings.npz  # Embeddings (use Git LFS for large files)
.claude/memory/               # All memories
.claude/knowledge/            # Knowledge files
.claude/skills/               # All skills
.claude/agents/               # All agents
.claude/commands/             # All commands
.claude/manifest.json         # Registry

# DON'T commit:
.claude/brain/.venv/          # Python virtual environment
.claude/brain/__pycache__/    # Python cache
.claude.bak/                  # Installation backup
CLAUDE.md.bak                 # Backup
```

## Principles

1. **Brain-first** — Query before acting, record after learning
2. **Metacircular** — The system generates and evolves itself
3. **Schema-driven** — Components are correct by construction
4. **Git-native** — All knowledge is versioned, no external infra
5. **Progressive disclosure** — Skills load on demand
6. **Ebbinghaus decay** — Unused memories fade, important ones persist

## Why "Engram"?

> **Engram** (neuroscience): the physical trace of a memory stored in the brain.
> The fundamental unit of learned information that persists between states of consciousness.

The **Ouroboros** icon 🐍 represents the feedback cycle: each session consumes
knowledge from the previous one and produces knowledge for the next.

## License

MIT
