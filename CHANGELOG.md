# Changelog

All notable changes to the Engram core (DNA) are documented here.

Based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

Only changes to `core/` are tracked here — the source of truth for all Engram installations.

## [Unreleased]

### Fixed
- VERSION file is now the single source of truth for Engram version (`3d7905a`)

### Added
- `/commit` command now auto-updates CHANGELOG.md when core/ changes (`1e72d29`)

### Changed
- Shift from brain-only to brain-primary architecture with synced .md files (`05ac19c`)

## [3.0.0] - 2026-02-03

### Added
- Complete metacircular system: genesis, evolution, brain, skills, agents (`cb64fd7`)
- Organizational brain with graph-based knowledge and semantic search (`5db29c6`)
- `/recall` command for querying brain via embeddings + spreading activation (`5db29c6`)
- Automatic embeddings regeneration in `/learn` workflow (`671bc71`)
- NestJS/Laravel/Flask detection in genesis analyzer (`9cbb313`)
- NestJS skill template (`9cbb313`)
- Base-ingester seed skill and `/ingest` command (`e9841a0`)
- Template skills staging and evaluation flow in init-engram (`edd5a3a`)
- Genesis template matching: check pre-built templates before generating (`b5e542d`)
- Backup migration system for `/init-engram` upgrades (`c76aa25`)

### Changed
- Templates directory renamed from `stacks/` to `skills/` for semantic clarity (`cf47110`)
- Infra detection added to project analyzer; orphan extras removed (`c5b8efa`)
