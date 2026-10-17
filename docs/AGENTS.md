# AGENTS.md — Operating Contract for Mentora

**Read this file completely before making any change to this repository.**

This file governs every AI agent and every human engineer working on Mentora. It is the highest-priority instruction set in this repository, second only to a direct instruction from the founder.

---

## 0. Who this is for

Mentora is built and operated by a **founder who is not a programmer**.

This has hard consequences for how you work:

- Nothing may require the founder to debug code, read stack traces, or improvise.
- Every command the founder must run is given **verbatim**, with the expected output.
- Every failure mode must have a documented, copy-pasteable recovery step.
- Never say "just configure X" — write the exact steps.
- Never leave the repository in a broken state at the end of a task.
- If you cannot finish safely, stop, return to a working state, and say so plainly.

---

## 1. What Mentora is

Mentora is a **multi-platform, AI-native education platform** — an AI teacher and education operating system. It is **not a website**.

- Initial exams: **IIT JEE**, **NEET**
- Future exams: CLAT, CUET, SAT, other Indian and global entrance examinations
- Initial clients: **Web application** and **Android application**
- Future clients: iOS (an application), WhatsApp (a **channel**, via a channel adapter)

Mentora's central claim is **measurable learning improvement**. Analytics is therefore a **first-class product subsystem**, not reporting bolted on later — see [20_ANALYTICS_ARCHITECTURE.md](docs/20_ANALYTICS_ARCHITECTURE.md).

Full product context: [00_PRODUCT_VISION.md](docs/00_PRODUCT_VISION.md)

---

## 2. The mandatory engineering workflow

Every implementation task follows Phases A to F. No exceptions.

### PHASE A — BEFORE CHANGES
1. Read this file (`AGENTS.md`).
2. Read the architecture documents relevant to the change.
3. Inspect the current repository — do not assume its state.
4. Inspect existing tests.
5. Determine what already works today.
6. Identify regression risks.
7. State the implementation plan **before** writing code.

### PHASE B — IMPLEMENTATION
8. Implement **only** the requested scope.
9. Do not modify unrelated systems.
10. Follow the architecture in `docs/`.
11. Add or update tests as part of the same change.

### PHASE C — VALIDATION
12. Run unit tests.
13. Run integration tests relevant to the change.
14. Run type checking.
15. Run linting.
16. Run build checks.
17. Run the existing regression suite.
18. Test the newly implemented functionality.
19. If deployed, test the deployed endpoint or application.
20. Inspect logs and errors.

### PHASE D — SELF REVIEW
21. Review the git diff.
22. Look for security problems.
23. Look for broken existing functionality.
24. Look for unnecessary dependencies.
25. Look for architectural violations.
26. Look for hardcoded secrets.
27. Look for provider coupling.
28. Look for missing tests.

### PHASE E — DOCUMENTATION
29. Update documentation if behaviour or architecture changed.
30. Create an ADR for any significant architectural decision (see [docs/adr/README.md](docs/adr/README.md)).

### PHASE F — REPORT

Produce a report with **exactly** these 16 sections, written for a non-programmer:

```
1.  OBJECTIVE
2.  WHAT I INSPECTED
3.  WHAT I CHANGED
4.  FILES CREATED
5.  FILES MODIFIED
6.  ARCHITECTURAL DECISIONS
7.  TESTS RUN
8.  TEST RESULTS
9.  REGRESSION TEST RESULTS
10. SECURITY CHECK
11. BUILD/DEPLOYMENT STATUS
12. KNOWN ISSUES
13. RISKS
14. NEXT RECOMMENDED TASK
15. EXACT COMMANDS THE FOUNDER NEEDS TO RUN
16. FOUNDER ACTION REQUIRED
```

### Honesty rules (non-negotiable)

- **Never claim a test passed if it was not actually run.**
- **Never claim deployment succeeded unless it was actually verified against the live URL.**
- **Never hide errors.** Report them in full, with the actual output.
- If something is untested, the report must say `NOT TESTED` and explain why.
- "Should work" is not a test result.

---

## 3. Architectural invariants

These are the rules that make Mentora work. Violating one is a defect, even if the tests pass.

### 3.1 The AI Gateway rule

> **No application or business logic may ever call an AI provider directly.**

Application code must never import or reference NVIDIA, OpenRouter, NaraRouter, Cloudflare Workers AI, OpenAI, Anthropic, or Google SDKs or endpoints. **Every AI call goes through the Mentora Model Gateway.**

The only directory permitted to contain provider-specific code is:

```
packages/model-gateway/src/adapters/
```

See [06_MODEL_GATEWAY.md](docs/06_MODEL_GATEWAY.md) and [07_PROVIDER_ADAPTERS.md](docs/07_PROVIDER_ADAPTERS.md).

### 3.2 The determinism rule

> **Prefer deterministic systems over LLMs whenever deterministic logic suffices.**

Never use an LLM for:

- database lookups
- arithmetic or scoring
- rule evaluation
- authoritative curriculum retrieval ("is this topic in the JEE 2026 syllabus?")
- mastery calculation
- revision scheduling

LLMs are for language, explanation, and open-ended understanding — not for facts the database already holds.

### 3.3 The authority rule

> **AI-generated content is never authoritative knowledge.**

Official examination authorities are the highest source of truth. Every important educational claim carries provenance. AI output enters the knowledge base only after human review. See [08_KNOWLEDGE_ARCHITECTURE.md](docs/08_KNOWLEDGE_ARCHITECTURE.md).

### 3.4 The one-backend rule

> **Web and Android share one backend, one API, one auth system, one database, one student model, one curriculum, and one set of business logic.**

Never create a second backend, a mobile-specific API, or a duplicated rule. Client apps contain presentation logic only.

**Non-app channels get an adapter, not a backend.** WhatsApp handles phone identity, opt-in, templates, and delivery status in `channels/whatsapp/`, then calls the same `/v1`. A channel adapter containing a business rule has recreated a second backend. See [ADR-0019](docs/adr/0019-channel-adapter-architecture.md).

**This is validated early, not assumed.** A thin, disposable Expo client at Phase P2 proves that Android consumes the same API and the same contracts with no backend change. See [ADR-0020](docs/adr/0020-prototype-gates-before-scale-claims.md).

### 3.5 The dependency direction rule

```
apps/*        ──►  packages/*
services/api  ──►  packages/*

packages/*       ──X──►  apps/*                                   FORBIDDEN
packages/*       ──X──►  services/*                               FORBIDDEN
packages/domain  ──X──►  network, filesystem, provider SDKs       FORBIDDEN
```

`packages/domain` is pure TypeScript. It must be testable with no network, no database, and no environment variables.

### 3.6 The API compatibility rule

> **Never break a deployed API version.**

Android users may run an old app for months. Breaking `/v1` breaks real students. Additive changes only; new behaviour goes in a new version path.

### 3.7 The secrets rule

> **Never commit API keys, tokens, service-role keys, or passwords.**

Secrets live in Cloudflare Workers secrets (production) and a gitignored `.dev.vars` file (local). See [15_SECURITY_ARCHITECTURE.md](docs/15_SECURITY_ARCHITECTURE.md).

### 3.8 The no-fake-systems rule

> **Do not create placeholder systems that falsely appear production-ready.**

A stub must be obviously a stub: named as one, documented as one, and it must fail loudly rather than return fake data. Never return invented educational content from a placeholder.

### 3.9 The testing rule

> **No feature is complete until it has tests, and existing functionality is regression-tested whenever new functionality is added.**

Tests belong to one of four tiers — **FAST**, **PR**, **DEPLOY**, **NIGHTLY** — declared where the test is written. Every commit runs FAST and PR, and **the entire regression set lives in those two tiers**. Tiering moved slow and expensive tests, never important ones.

See [17_TESTING_STRATEGY.md](docs/17_TESTING_STRATEGY.md) and [ADR-0021](docs/adr/0021-testing-tiers.md).

### 3.10 The scope rule

> **Do not silently make major architectural decisions.**

If a decision is significant or ambiguous, write an ADR and surface it to the founder in the report. Do not install unnecessary dependencies. Do not introduce microservices without a demonstrated requirement — Mentora is a **modular monolith**.

**Do not claim scale, latency, or capability that has not been measured.** Where a property is assumed rather than measured, say so, and schedule a prototype gate. See [ADR-0020](docs/adr/0020-prototype-gates-before-scale-claims.md).

### 3.11 The analytics source-of-truth rule

> **Analytics observes the system. It never governs it.**

Analytics must never become the source of truth for **mastery**, **curriculum**, **authorization**, or **money**, and it never replaces domain events. Derivation is one-way: domain tables → analytics read models → dashboards. Nothing writes back.

- `student.learning_event` remains the **append-only source of truth** for learning state. The analytics SDK never writes it. `trackLearningEvent` emits the *projection* of a fact already durably recorded.
- Analytics derivation runs under a **read-only database role** over domain schemas. It is a permission, not a promise.
- **A use case never reads analytics**, never waits for it, and never fails because of it.
- Analytics events carry **`P0`/`P1` data only**. Personal identifiers, a minor's academic values, and student-authored content are rejected at the ingestion edge.
- **No third-party analytics, advertising, attribution, or session-replay SDK in any client. Ever.**

See [20_ANALYTICS_ARCHITECTURE.md](docs/20_ANALYTICS_ARCHITECTURE.md), [ADR-0012](docs/adr/0012-analytics-event-architecture.md), and [ADR-0014](docs/adr/0014-privacy-first-analytics-for-minors.md).

### 3.12 The cost-control rule

> **Do not use paid inference unless policy permits it.**

Paid models are **excluded from routing by default**, not merely ranked last — otherwise a free-tier outage sends every request to paid inference at once. Free allocations are development, prototyping, and controlled-testing capacity; they are **not** a production capacity guarantee. A **Free-to-Paid Readiness Gate** must be passed before real students are onboarded.

See [ADR-0017](docs/adr/0017-ai-cost-and-reliability-controller.md).

### 3.13 The reproducibility rule

> **Every derived state value records the algorithm version that produced it.**

Mastery, knowledge state, evidence weighting, propagation, decay, scheduling, and scoring configuration are all versioned. The system must always be able to answer *"which algorithm produced this mastery value?"* — including for a value computed a year ago.

See [ADR-0016](docs/adr/0016-versioned-derived-state-algorithms.md).

### 3.14 The commit-and-push rule

> **Commit at the end of every chunk and push; never leave work uncommitted; gitignore generated files immediately.**

Every new `TASK.md` carries this line in its Rules section. Pushes are fast-forward only — never force.

---

## 4. Documentation index

| Document | Covers |
|---|---|
| [00_PRODUCT_VISION.md](docs/00_PRODUCT_VISION.md) | What Mentora is and is not |
| [01_SYSTEM_ARCHITECTURE.md](docs/01_SYSTEM_ARCHITECTURE.md) | Whole-system view, repo layout, layering |
| [02_CLIENT_ARCHITECTURE.md](docs/02_CLIENT_ARCHITECTURE.md) | Shared rules for all client apps |
| [03_WEB_ARCHITECTURE.md](docs/03_WEB_ARCHITECTURE.md) | Web application |
| [04_ANDROID_ARCHITECTURE.md](docs/04_ANDROID_ARCHITECTURE.md) | Android application |
| [05_BACKEND_ARCHITECTURE.md](docs/05_BACKEND_ARCHITECTURE.md) | API, auth, domain services |
| [06_MODEL_GATEWAY.md](docs/06_MODEL_GATEWAY.md) | Provider-agnostic AI gateway |
| [07_PROVIDER_ADAPTERS.md](docs/07_PROVIDER_ADAPTERS.md) | Individual AI provider adapters |
| [08_KNOWLEDGE_ARCHITECTURE.md](docs/08_KNOWLEDGE_ARCHITECTURE.md) | Knowledge, provenance, authority tiers |
| [09_CURRICULUM_ARCHITECTURE.md](docs/09_CURRICULUM_ARCHITECTURE.md) | Exams, syllabus, concept graph, versioning |
| [10_STUDENT_MODEL.md](docs/10_STUDENT_MODEL.md) | Persistent student model, mastery |
| [11_PEDAGOGY_ARCHITECTURE.md](docs/11_PEDAGOGY_ARCHITECTURE.md) | Teaching strategies and adaptation |
| [12_ASSESSMENT_ARCHITECTURE.md](docs/12_ASSESSMENT_ARCHITECTURE.md) | Questions, tests, evaluation |
| [13_GOOGLE_DRIVE_INGESTION.md](docs/13_GOOGLE_DRIVE_INGESTION.md) | Source material ingestion pipeline |
| [14_DATABASE_ARCHITECTURE.md](docs/14_DATABASE_ARCHITECTURE.md) | PostgreSQL, pgvector, schema domains |
| [15_SECURITY_ARCHITECTURE.md](docs/15_SECURITY_ARCHITECTURE.md) | Secrets, authorization, privacy, threat model |
| [16_DEPLOYMENT_ARCHITECTURE.md](docs/16_DEPLOYMENT_ARCHITECTURE.md) | Cloudflare, environments, CI/CD |
| [17_TESTING_STRATEGY.md](docs/17_TESTING_STRATEGY.md) | All testing layers |
| [18_AI_EVALUATION.md](docs/18_AI_EVALUATION.md) | Evaluating AI quality |
| [19_DEVELOPMENT_ROADMAP.md](docs/19_DEVELOPMENT_ROADMAP.md) | Phased build plan |
| [20_ANALYTICS_ARCHITECTURE.md](docs/20_ANALYTICS_ARCHITECTURE.md) | Events, learning/AI/business analytics, privacy, experimentation |
| [21_MENTORA_PRODUCT_BLUEPRINT.md](docs/21_MENTORA_PRODUCT_BLUEPRINT.md) | The whole product in one place: teacher philosophy, plan, difficulty, assignments, readiness, "I'm Stuck", "Add Material", navigation, non-goals |
| [22_LEARNING_INTELLIGENCE_ARCHITECTURE.md](docs/22_LEARNING_INTELLIGENCE_ARCHITECTURE.md) | Architecture audit: why the learning intelligence layer is five separated models rather than one knowledge graph, and what must be decided before it is built |
| [23_LEARNING_INTELLIGENCE_GAP_ANALYSIS.md](docs/23_LEARNING_INTELLIGENCE_GAP_ANALYSIS.md) | Stress-test of doc 22: eight gaps, the capability audit, and the questions escalated to the founder |
| [24_HARDNESS_AND_DERIVED_FACTS_DECISION.md](docs/24_HARDNESS_AND_DERIVED_FACTS_DECISION.md) | The hardness family and where derived-global measured facts belong. Resolved by ADR-0031 and ADR-0032 |
| [25_PRODUCT_VOCABULARY.md](docs/25_PRODUCT_VOCABULARY.md) | Student-facing terminology lock: naming philosophy, the 30-term vocabulary, domain mapping, scoring, registry design, multi-exam overrides (§§20–21) — pending founder approval on §19 |
| [MASTER_BUILD_STATE.md](docs/MASTER_BUILD_STATE.md) | **Start here across sessions.** Cross-repository state map: one row per subsystem, what is real, what is fixture, what only the founder can unblock |
| [EXPERIENCE_IMPLEMENTATION.md](docs/EXPERIENCE_IMPLEMENTATION.md) | The design system, app shell and home experience as built |
| [CURRICULUM_IMPLEMENTATION.md](docs/CURRICULUM_IMPLEMENTATION.md) | The curriculum and learning-objective model as built |
| [LEARNING_LOOP_IMPLEMENTATION.md](docs/LEARNING_LOOP_IMPLEMENTATION.md) | Evidence, objective state and the next-action rules as built |
| [EVIDENCE_CORE_IMPLEMENTATION.md](docs/EVIDENCE_CORE_IMPLEMENTATION.md) | Deterministic scoring, the append-only evidence ledger, and the attempt API as built — not mastery, not P7 |
| [LOOP_CLOSURE_IMPLEMENTATION.md](docs/LOOP_CLOSURE_IMPLEMENTATION.md) | LLC-lite HTTP turn: next-action, fixture presentations, mandatory revision pin — no CMS, no `/questions/next` |
| [STUDENT_PRACTICE_TURN_IMPLEMENTATION.md](docs/STUDENT_PRACTICE_TURN_IMPLEMENTATION.md) | Browser `/practice` turn over LLC-lite — not a fresh-user teacher |
| [FIRST_EXPOSURE_TEACHING_IMPLEMENTATION.md](docs/FIRST_EXPOSURE_TEACHING_IMPLEMENTATION.md) | Authored first-exposure teaching + check for one chemistry objective — not repair, not a CMS |
| [SOURCE_CORPUS_IMPLEMENTATION.md](docs/SOURCE_CORPUS_IMPLEMENTATION.md) | M0 local inventory and PDF forensics — not knowledge, not P4B |
| [DRIVE_RECONCILE.md](docs/DRIVE_RECONCILE.md) | M0.1 read-only Drive enumeration and SHA-256 join — not sync, not P4B |
| [HF_SOURCE_CORPUS_PUBLISH.md](docs/HF_SOURCE_CORPUS_PUBLISH.md) | Operator publish of raw files to a private Hugging Face Dataset — not K, not P4B |
| [ADMIN_IMPLEMENTATION.md](docs/ADMIN_IMPLEMENTATION.md) | The read-only operator surface (overview + student inspection) as built — no write actions, no directory, no audit log yet |
| [TEACHING_INTEL_IMPLEMENTATION.md](docs/TEACHING_INTEL_IMPLEMENTATION.md) | Governed teaching-intelligence consumption (validated packs, template fallback, benchmark) — no production pack yet |
| [adr/README.md](docs/adr/README.md) | Architecture Decision Records |

---

## 5. Repository state

**Current phase: P2 — Experience foundation, plus the first product-construction wave.** The design system, the application shell and the home experience are implemented and tested locally. P1 (skeleton, pipeline, analytics v0) remains implemented and tested locally; **nothing is yet deployed** (deployment needs Cloudflare credentials only the founder can create — see [docs/P1_IMPLEMENTATION.md](docs/P1_IMPLEMENTATION.md) section 9). On top of the teacher loop v0, the tree now holds the executable classroom, class lifecycle + event recording + replay + notes, assignment and quiz runtimes, and the curriculum pipeline foundation — all implemented and tested locally on demonstration content (see [docs/MENTORA_MASTER_PRODUCT_SPEC.md](docs/MENTORA_MASTER_PRODUCT_SPEC.md) and [docs/MENTORA_CAPABILITY_MATRIX.md](docs/MENTORA_CAPABILITY_MATRIX.md)).

What exists:

```
AGENTS.md               this file
README.md
docs/                   architecture documentation (00-20) + P1_IMPLEMENTATION.md
                        + EXPERIENCE_IMPLEMENTATION.md
                        + EVIDENCE_CORE_IMPLEMENTATION.md
                        + LOOP_CLOSURE_IMPLEMENTATION.md
                        + STUDENT_PRACTICE_TURN_IMPLEMENTATION.md
                        + FIRST_EXPOSURE_TEACHING_IMPLEMENTATION.md
                        + MENTORA_MASTER_PRODUCT_SPEC.md (canonical product reference)
                        + MENTORA_CAPABILITY_MATRIX.md (capability/dependency matrix)
docs/adr/               architecture decision records (0001-0066)
docs/review/            packets for independent human review (diagnostic
                        review packet v1: 16 cases, no verdicts yet)
scripts/                check-docs.mjs, scan-secrets.mjs

packages/contracts/     Zod wire contracts, the analytics envelope, the event registry
packages/domain/        AnalyticsPort, the experience layer (XP, levels, streaks,
                        mastery bands, difficulty, next action, trajectory,
                        concept tracks, constellation) and the curriculum layer
                        (exams, subjects, chapters, topics, concepts, the
                        prerequisite DAG, learning objectives, evidence
                        requirements, syllabus membership, the question
                        blueprint, provenance and authority tiers) with total
                        validators and THREE demonstration packages (Physics /
                        Electrostatics, Chemistry / Chemical Bonding, and
                        Mathematics / Quadratic Equations), the
                        learning loop (assessment evidence, the evidence
                        trust policy, evidence-based objective state and the
                        deterministic next-action rules), deterministic
                        assessment scoring (exam patterns, item revisions,
                        AttemptSubmission → ScoredAttempt;
                        multiple_correct_mcq is refused), and the teacher
                        loop v0 (TeacherContext v1 with K/E/S/D/P sections,
                        an explicit session machine, deterministic intent and
                        check evaluation, the versioned corpus-release
                        contract), and the reasoning-level diagnosis layer
                        (reader port, transport, governance, intervention —
                        P only, never an M1.5 input; ADR-0066). Pure TypeScript,
                        shared with the future Android client.
packages/analytics/     validation, privacy classification, sink router, sinks
packages/source-corpus/ M0 local SOURCE inventory, PDF forensics, exact
                        duplicates, extraction-readiness, M0.1 read-only
                        Drive reconcile, plus operator publish of raw files
                        to a private Hugging Face Dataset. Node-only. Not K,
                        not P4B, not the learner loop.
services/api/           Hono Worker: GET /v1/health, POST /v1/analytics/events,
                        POST /v1/attempts (itemRevisionId pin required),
                        GET /v1/learners/me/objective-state,
                        GET /v1/learners/me/next-action,
                        GET /v1/learners/me/study-plan (scope only, never an action),
                        GET /v1/questions/:questionId,
                        GET /v1/teachings/:id,
                        POST /v1/teacher/turns + GET /v1/teacher/sessions/:id
                        (teacher loop v0: session machine, deterministic
                        evaluation, M1.5 every turn, gateway wording with an
                        authored fallback, no-release corpus grounding; chat
                        never writes the ledger — recording is via
                        suggestedAttempt through POST /v1/attempts;
                        governed diagnostic reading as P after M1.5, only
                        when a REVIEWED diagnostic pack is installed — none
                        is, so production reads no diagnosis — ADR-0066)
                        + GET /v1/billing/status and POST /v1/billing/webhooks/:provider
                        (commerce boundary: HMAC-signed provider events, idempotent
                        delivery ledger, access derived on read; 503 without
                        BILLING_WEBHOOK_SECRET; no live provider, nothing gated)
                        — no /questions/next, no /teachings/next, no readiness API, no CMS
apps/web/               React + Vite SPA: design system, app shell, home experience,
                        demo-data layer (off by default), preserved system status,
                        /plan master plan + weeks + today (scope only; names what will
                        not fit before the paper), /practice LLC-lite browser turn (not a
                        fresh-user teacher),
                        chemistry first-exposure teaching turn on an allowlisted target,
                        /teacher real teaching loop over POST /v1/teacher/turns
                        (chat, hints, stepwise solutions, interruption handling,
                        Count-this-answer recording, session resume, developer
                        observability panel), /you Supabase magic-link sign-in
                        boundary with a memory-only token (hosted Auth endpoint
                        needs founder-created Supabase config; local token box
                        otherwise)
apps/android-spike/     DISPOSABLE contract-validation client — delete after P2
db/migrations/          0001_analytics_v0.sql plus the evidence-core slice
                        (0002 curriculum, 0003 assessment, 0004 student ledger),
                        0005 knowledge (P4B), 0006 teacher sessions + turns
                        (working state, RLS own-read, server-write; never
                        evidence, never learner state), 0007–0012 class,
                        assignments, quizzes, onboarding, diagnostics, tests,
                        plus 0013 commerce (plans, subscriptions, append-only
                        provider-event ledger; no live provider),
                        0014 teacher revision pins, and 0015 the examination
                        date + policy version on the student profile
                        (additive, no backfill; the date is never inferred
                        from target_year — ADR-0062), and 0016 the authored
                        diagnostic repair a teacher turn delivered (nullable,
                        teacher working state, never evidence — ADR-0066).
                        Not applied to a live project. Not G1.
tests/                  architectural guards, client/API contract, deploy smoke,
                        PGlite evidence-core PR tests
.github/workflows/      ci.yml (FAST + PR), deploy.yml (DEPLOY + rollback)
```

What deliberately does **not** exist yet: any lesson, course, or question content; **any real curriculum data** — the curriculum *model* exists, but every package shipped is demonstration content that is structurally unable to be authoritative or active; live Model Gateway student surfaces; the AI Model Lab; Google Drive ingestion; the student model and mastery; authentication sign-in surfaces; the experimentation platform; the production Android app; the `knowledge`, `gateway`, `experiment` and `ops` database schemas. Minimum `curriculum`, `assessment` and `student` tables now exist as a demonstration serving projection — see [EVIDENCE_CORE_IMPLEMENTATION.md](docs/EVIDENCE_CORE_IMPLEMENTATION.md). They are not a CMS, not G1, and not deployed.

**On the curriculum layer.** Mentora can now *represent* a syllabus and check that the representation is honest — it holds no syllabus. A curriculum version cannot be `active` unless its source is authoritative and reviewed, so demonstration and AI-drafted content can never answer "is this in my syllabus?". A learning objective must state an observable capability, and a question must name the objective it tests. Nothing is persisted, served or rendered. See [docs/CURRICULUM_IMPLEMENTATION.md](docs/CURRICULUM_IMPLEMENTATION.md), [ADR-0024](docs/adr/0024-curriculum-model-as-pure-domain-data.md) and [ADR-0025](docs/adr/0025-observable-learning-objectives-and-question-linkage.md).

**On the learning loop.** That curriculum now *drives* one disciplined teaching decision: evidence → objective state → next action, deterministically and with no AI. It refuses to teach an objective whose hard prerequisites are not demonstrated, and names the blocking capability. **`ObjectiveEvidenceState` is NOT mastery** — it is a three-valued fold over the `EvidenceRequirement` an author already wrote, with no probability, no confidence, no weighting and **no forgetting**; the mastery model remains Phase P7. Demonstration evidence carries `origin: 'demo'` and is structurally unable to become a live student record, and no trust policy admits AI-produced or self-asserted evidence. **The loop has been walked over three demonstration chapters with materially different prerequisite graphs — a chain, a pair of diamonds, and a soft-shortcut edge in a new subject (Mathematics) — and generalised to each with no change to the engine**; it has still never met a real syllabus or a real learner. See [docs/LEARNING_LOOP_IMPLEMENTATION.md](docs/LEARNING_LOOP_IMPLEMENTATION.md) sections 16, 15 and 19, and [ADR-0026](docs/adr/0026-evidence-based-objective-state-and-the-learning-loop.md).

**On exam scoping (Phase 1.7a).** Hardness is now **three axes** — Demand (what a capability asks of a student), Challenge (the 1–7 item scale), and Requirement (how far one exam goes) — and they may never be collapsed into one score. `requiredDepth` is a **ceiling on required learning**: objectives above it remain valid stretch content and no longer gate readiness. **Readiness, gating, demonstrated-concept calculation and next-action now take an explicit `curriculumVersionId` with no default**, while evidence stays exam-agnostic, so a student preparing for two examinations keeps one ledger and gets two honest answers. This closed a live defect — the engine used to climb `cognitiveDemand` past a concept's own authored syllabus depth, in the shipped fixture, with one exam involved. A second (fictional) exam over the same concepts proves the separation. See [ADR-0031](docs/adr/0031-hardness-three-axes-and-exam-scoped-requirement.md), which **extends** ADR-0026 rather than superseding it, and [docs/LEARNING_LOOP_IMPLEMENTATION.md](docs/LEARNING_LOOP_IMPLEMENTATION.md) section 18.

**On measured facts.** A fifth epistemic class, **MEASURED**, now exists alongside Authored / Observed / Derived / Proposed: a recomputable aggregate over many students' evidence that may govern weighting and selection and may **never** become an authored claim. Calibrated difficulty is population-scoped and never shares a row with the authored value it measures. The `question_calibration` table now exists and stays empty — see [ADR-0028](docs/adr/0028-five-models-and-five-epistemic-classes.md) and [ADR-0032](docs/adr/0032-measured-facts-and-calibration-governance.md), whose thresholds are **initial product policy, subject to counsel**.

**On the durable evidence core.** A synthetic student can submit through `POST /v1/attempts`. The Worker scores in domain TypeScript, commits via a service-role RPC, and `GET /v1/learners/me/objective-state` rebuilds S from K+E for an explicit `curriculumVersionId`. This is **not** mastery, **not** P7, **not** G1, and **not** deployed. See [EVIDENCE_CORE_IMPLEMENTATION.md](docs/EVIDENCE_CORE_IMPLEMENTATION.md).

**On LLC-lite.** The same student can now complete one HTTP turn: `GET /v1/learners/me/next-action` (explicit target), `GET /v1/questions/:questionId` (fixture stem and options, same `itemRevisionId`), then `POST /v1/attempts` with that pin. The pin is required; the server scores the pinned revision, never a later edit. A recommended question is attached for `guided_practice`, `independent_practice`, `increase_demand` and `reassess`, and a teaching+check pair may attach for `teach_objective` only when both exist. TypeScript fixtures remain the serving source. Do **not** add an Activity CMS, `GET /v1/questions/next`, `GET /v1/teachings/next`, or silent latest-revision scoring. See [LOOP_CLOSURE_IMPLEMENTATION.md](docs/LOOP_CLOSURE_IMPLEMENTATION.md) and [ADR-0036](docs/adr/0036-llc-lite-serving-pin-and-fixture-presentations.md).

**On the student practice turn.** `/practice` is the browser interaction layer over that HTTP loop. It follows server D, echoes the serving pin internally, and never displays `itemRevisionId`. A fresh local API with an empty physics ledger still has no practice question — that is honest, not a defect. The full question turn is exercised against the proven seeded synthetic learner contract in FAST tests, not by fabricating evidence in the browser. This is **not** a complete fresh-user teacher. See [STUDENT_PRACTICE_TURN_IMPLEMENTATION.md](docs/STUDENT_PRACTICE_TURN_IMPLEMENTATION.md).

**On first-exposure teaching.** One chemistry demonstration objective can be taught, then checked, then practised: empty ledger → `teach_objective` (RULE_5 unchanged) → authored `TeachingPresentation` → scorable check `question:demo_cb_ion_charge_prediction` → `POST /v1/attempts` → existing practice D. Teaching is a serving fixture, not a curriculum entity. Misconception context is a non-blocking presentation field for `supported` needs only; it does not change kind or rule. Physics `/practice` with an empty ledger remains `learn_prerequisite` EmptyState. See [FIRST_EXPOSURE_TEACHING_IMPLEMENTATION.md](docs/FIRST_EXPOSURE_TEACHING_IMPLEMENTATION.md) and [ADR-0041](docs/adr/0041-authored-first-exposure-teaching-serving.md).

**On the study plan.** The journey's `MASTER PLAN → WEEK → DAY` stages now exist. `GET /v1/learners/me/study-plan` returns a deterministic, versioned plan (`study-plan.v0-provisional`) rendered at `/plan`: examined concepts in prerequisite order, cut into seven-day weeks against the student's own stated weekly minutes, with concepts the ledger already demonstrates dropped and 25% of every week held back for revision. **The plan decides SCOPE and never an ACTION** — every week carries a `ScopeDeclaration` that the M1.5 Frame admits, and M1.5 still chooses inside it; a test asserts no action, question, objective or rule id appears in the response. The day slice deliberately hands back the *week's* scope unnarrowed. The examination date is **required with no default** (Mentora holds no examination calendar) and capacity comes from the profile or an explicit override — never an assumed default. When the syllabus does not fit before the paper the plan says `insufficient_time` and **names every concept that did not fit**; it never compresses. The minute estimates are an **authored table, not a measurement**, which is why the policy version says provisional. Nothing is stored. Do **not** let the plan pick the day's activity, narrow the day scope to one concept, default the exam date from `targetYear`, or schedule spaced revision (that needs P7). See [ADR-0061](docs/adr/0061-study-plan-decides-scope-never-action.md).

**On source corpus intelligence (M0).** A Node-only package can inventory a local JEE material folder: hash every file, measure PDFs, find exact duplicates, and write a gitignored report. Identity is `contentId` plus a `local_scan_root` locator — not an absolute path and not a Drive ID. Local **482** vs Drive-UI **554** is unreconciled; neither count is assumed correct. It does **not** create knowledge, run OCR, call an LLM, or change any learner API. See [SOURCE_CORPUS_IMPLEMENTATION.md](docs/SOURCE_CORPUS_IMPLEMENTATION.md) and [ADR-0038](docs/adr/0038-source-corpus-intelligence.md).

**On Drive reconciliation (M0.1).** The same package can enumerate one Drive folder read-only and join verified SHA-256 hashes to the frozen M0 JSONL. Default `--verify none` downloads zero file bytes. Tests use a fake Drive client only. This is not sync, not P4B, and not a student-path dependency. See [DRIVE_RECONCILE.md](docs/DRIVE_RECONCILE.md) and [ADR-0039](docs/adr/0039-drive-readonly-reconciliation.md).

**On Hugging Face source-corpus publish.** The same package can dry-run or publish the local raw folder to a private Hugging Face Dataset under `raw/`. Drive remains the canonical shelf. Upload is a hard-link staging tree of accepted files only — never the live corpus, never a silent copy. A successful `hf upload` exit code is not proof the Hub has every file. Live listings return a git `blob_id`, which is not SHA-256. Completeness requires Hub LFS sha256 (64 hex) or a streaming download-and-rehash of `raw/`. Tests use a fake Hub port only. This is not knowledge, not P4B, and not a student-path dependency. See [HF_SOURCE_CORPUS_PUBLISH.md](docs/HF_SOURCE_CORPUS_PUBLISH.md) and [ADR-0040](docs/adr/0040-huggingface-source-artifact-store.md).

**The P2 home experience renders these absences rather than hiding them.** There is no XP awarding, level progression, streak recording, mission generation, quest engine, boss battle, achievement awarding, leaderboard or Next Best Action Engine — only the interface they will be rendered into. With demo mode off (the default in every build) the home screen shows designed, explanatory empty states and **no invented mastery, rank, percentile, XP or streak**; a test asserts their absence. A clearly-labelled, banner-marked demo preview can be switched on for design review: demo values carry `origin: 'demo'` inside their own type and are chipped on screen. See [docs/EXPERIENCE_IMPLEMENTATION.md](docs/EXPERIENCE_IMPLEMENTATION.md).

Do not assume any code exists. **Always inspect first (Phase A, step 3).**

### Phase order at a glance

`P0` architecture → `P0.5` revision → `P1` skeleton + analytics v0 *(current)* → `P2` data foundation + prototype gates → `P3A/P3B` gateway → `P4A` identity/consent → `P4B` ingestion → `P5` curriculum/knowledge → `P6` AI teacher v1 → `P7` assessment + student model → `P8` adaptive pedagogy + experiments → `P9` voice/vision → `P10` Android production → `P11` counselling → `P12` WhatsApp → `P13` production readiness.

Full detail, with exit criteria: [19_DEVELOPMENT_ROADMAP.md](docs/19_DEVELOPMENT_ROADMAP.md).

---

## 6. Commands

**The one command that answers "is the repository healthy?":**

```bash
pnpm check
```

It runs formatting, lint, type checking, every test in the FAST and PR tiers, both production builds, the secret scan and the documentation check. **It must pass before every commit.**

| Command | Tier | What it does |
|---|---|---|
| `pnpm check` | FAST + PR | Everything below, in one command |
| `pnpm check:fast` | FAST | Format, lint, typecheck, fast tests — seconds |
| `pnpm test:fast` | FAST | Pure unit tests, architectural guards, registry integrity |
| `pnpm test:pr` | PR | Adds the real Workers runtime and PGlite: API contract, analytics ingestion, security denials, web/Android parity, evidence ledger |
| `pnpm test:deploy` | DEPLOY | Smoke tests against a **live deployed URL** (needs `MENTORA_API_URL`) |
| `pnpm typecheck` | FAST | TypeScript across every package |
| `pnpm lint` | FAST | Code style **and** the architectural import rules |
| `pnpm build` | PR | Production builds of the web app and the Worker |
| `pnpm check:secrets` | PR | Scans the repository **and the built bundle** for secrets |
| `pnpm check:docs` | PR | Documentation links, ADR indexing, secret scan |
| `pnpm dev:api` | — | Runs the API locally on `http://127.0.0.1:8787` |
| `pnpm dev:web` | — | Runs the web app locally on `http://localhost:5173` |
| `pnpm deploy:api` / `pnpm deploy:web` | — | Manual deployment (CI does this automatically) |
| `pnpm material:inventory` | — | Local M0 scan of a source-material folder (`--root`). Writes gitignored `generated/source-corpus/` |
| `pnpm material:reconcile` | — | Read-only Drive enumeration + SHA-256 join (`--drive-folder`). Writes gitignored `generated/source-corpus/reconcile/`. Tests never call real Drive |
| `pnpm material:publish:hf` | — | Dry-run or publish raw local files to a private Hugging Face Dataset under `raw/` (`--root`, `--dry-run`). Stages accepted files with hard links. Writes gitignored `generated/source-corpus/hf-publish/`. Tests never call the real Hub. CLI success is not corpus completeness; Hub `blob_id` is not SHA-256 |
| `pnpm material:source-to-k` | — | Offline M1 extraction of ONE native-text PDF (`--pdf`, `--source-id`, `--title`, `--licence`, `--document-version-id`). Writes gitignored `generated/source-to-k/`. Extraction only — never authors a proposal, review, or K. Tests use synthetic PDFs, never the real corpus |

Test tiers are declared by **filename** — `*.fast.test.ts`, `*.pr.test.ts`, `*.deploy.test.ts` — so a test's tier is reviewable in the same diff as the test. A test file with no tier fails CI. See [ADR-0021](docs/adr/0021-testing-tiers.md).

NIGHTLY (`pnpm test:nightly`) does not exist yet: it holds AI evaluation and end-to-end suites, and neither has anything to evaluate before Phase P3A.

Full setup, local development and deployment instructions, written for a non-programmer: [docs/P1_IMPLEMENTATION.md](docs/P1_IMPLEMENTATION.md).

**Keep this section accurate** — the founder relies on it.

---

## 7. Escalate to the founder when

- A decision changes cost, or requires a paid service.
- A decision affects student data privacy or legal compliance.
- A change would break a deployed API used by the Android app.
- Educational correctness is at risk.
- An AI provider's free tier or terms have changed.
- The requested scope conflicts with an architectural invariant in section 3.
- **A change would collect new data about students** — especially minors.
- **A prototype gate fails**, or a documented threshold is about to be relaxed.
- **A mastery, scoring, or scheduling algorithm version would change**, requiring a rebuild.
- **Paid inference would be enabled** for any capability.

State the trade-off in plain language, give a recommendation, and wait.
