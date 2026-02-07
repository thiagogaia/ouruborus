# Engram — 5-Minute Quickstart

> Persistent memory for Claude Code. Install once, every session gets smarter.

---

## 1. Install (terminal)

```bash
git clone https://github.com/your-org/engram.git ~/engram
cd ~/engram
./setup.sh /path/to/your/project
```

Stack is auto-detected (Next.js, Django, FastAPI, Laravel, etc).

For multiple projects at once:

```bash
./batch-setup.sh ~/proj1 ~/proj2 ~/proj3
```

## 2. Initialize (inside Claude Code)

```bash
cd /path/to/your/project
claude
```

Then type:

```
/init-engram
```

This runs 8 automated phases: analyzes your codebase, generates custom skills, populates the brain with your commit history, and validates everything. Approve the plan when prompted.

**Done.** The system is ready.

## 3. The Daily Loop

Five commands. This is your entire workflow:

```
/status          →  where am I? what should I do next?
/recall [topic]  →  what does the brain know about this?
  ... work ...
/commit          →  semantic commit message from diff
/learn           →  record everything, close the loop
```

That's it. `/learn` is the one you must never skip — it feeds the brain.

## 4. Commands You'll Use Sometimes

```
/review              code review (correctness → patterns → security → perf)
/plan [feature]      implementation plan informed by brain
/domain [term]       investigate a business term or rule
/priorities          re-evaluate tasks with ICE Score
/create skill [name] generate a new reusable skill
/doctor              health check if something feels off
```

## 5. How the Brain Works (30-second version)

```
.claude/brain/brain.db    ←  knowledge graph (nodes + edges)
.claude/brain/chroma/     ←  vector search (semantic similarity)
```

- **Nodes** = memories (decisions, patterns, concepts, commits, bugs)
- **Edges** = relationships (references, same scope, semantic similarity)
- **Recall** = semantic search + spreading activation across edges
- **Sleep** = automatic consolidation that discovers connections you didn't write
- **Decay** = unused memories fade, frequently accessed ones get stronger

You never edit the brain directly. You feed it through `/learn` and query it through `/recall`.

## 6. What Happens Under the Hood

```
You ask a question
    → Claude runs /recall
    → brain searches by meaning (embeddings)
    → spreads activation to connected nodes
    → returns ranked results with full context
    → reinforces accessed memories (self-feeding loop)
```

```
You run /learn
    → Claude reflects on what changed (git diff/log)
    → encodes new memories (ADRs, patterns, bugs, concepts)
    → runs sleep (dedup → connect → relate → themes → calibrate)
    → updates priorities
    → proposes system evolutions
```

## 7. Project Structure (what matters)

```
your-project/
├── CLAUDE.md                        # instructions (auto-generated)
└── .claude/
    ├── brain/                       # the knowledge graph
    │   ├── brain.db                 #   SQLite store
    │   ├── recall.py                #   query interface
    │   └── sleep.py                 #   consolidation engine
    ├── skills/                      # capabilities (6 seeds + custom)
    ├── agents/                      # specialists (architect, db-expert, domain-analyst)
    ├── commands/                    # slash commands (15)
    ├── dna/                         # schemas that validate components
    ├── knowledge/                   # markdown mirror (read-only after init)
    │   └── priorities/
    │       └── PRIORITY_MATRIX.md   # only actively maintained .md file
    └── manifest.json                # component registry
```

## 8. Three Rules

1. **Always run `/learn` at the end of a session.** Without it, the loop doesn't close.
2. **Trust `/recall`.** It knows more than you remember. Ask it before coding.
3. **Don't edit brain files by hand.** Use `brain.add_memory()` or `/learn`.

## 9. If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| Brain feels slow or inaccurate | `/doctor` |
| Brain corrupted | `python3 .claude/brain/populate.py all` |
| Low health score | `python3 .claude/brain/sleep.py` |
| Missing Python deps | `pip install -r .claude/brain/requirements.txt` |
| Want to start fresh | `./setup.sh --uninstall . && ./setup.sh .` |

## 10. Going Deeper

| Doc | What it covers |
|-----|----------------|
| [DIA_A_DIA.md](DIA_A_DIA.md) | Full day-to-day guide with examples |
| [LIFECYCLE_GUIDE.md](LIFECYCLE_GUIDE.md) | Complete lifecycle, brain internals, CLI reference |
| [USE_CASES.md](USE_CASES.md) | 21 structured use cases for all actor types |
| [README.md](../README.md) | Architecture, version history, principles |
