# MENTORA — PRODUCT VISION (founder intent)

**Status of this document:** This describes what MENTORA *should* become. It is NOT evidence that any of it exists. Anything described here must be verified in the actual code before anyone claims it is implemented. Durations, counts and schedules below are **starting defaults to test with real students**, not established facts.

**Owner:** Ambrish (founder). Version 1.7, 3 Oct 2026. v1.7 adds §29 (teaching board engine). v1.6 added §28 (learning-resource formats, Content Studio, Rankers track). v1.5 added §27 (teacher long-term memory). v1.4 added §26 (live-teacher architecture, schedule and price — overrides §4, §14 and §16 where they differ). v1.3 updates content and rights (§17): founder has licensed the corpus. v1.2 added JEE-level expertise (§23) and the full-syllabus roadmap (§24). Changes in v1.1: concrete personas (§6), adaptivity (§5A), model tiers (§14A), AI-only review policy (§21), golden-transcript decisions (§22).

---

## 1. Mission and how we measure success

MENTORA is a complete AI-run JEE coaching programme for one student at a time. It teaches like an expert human tutor, runs a regular class schedule like a coaching institute, and prepares the student to perform strongly in JEE Main and JEE Advanced.

Success is measured by **evidence of learning**, not by time spent or content volume:
- Score improvement on MENTORA's standardised weekly/monthly tests and full mocks.
- Ability to solve **unfamiliar** problems independently, without hints.
- Retention when topics are re-tested days or weeks later.
- Ultimately, real JEE results of real students.

We never advertise guaranteed ranks, marks or selection (prohibited by India's CCPA coaching-advertisement guidelines, Nov 2024). We advertise measured improvement.

## 2. Who is involved

**Student** — learns, practises, asks doubts by voice, chat, photo or camera. Website and Android app.

**Parent/guardian** — gives consent (student is usually a minor), sees progress summaries.

**Four AI roles**, sharing ONE student profile and ONE decision authority (M1.5):

| Role | Responsibilities |
|---|---|
| Physics teacher | Classes, practice guidance, doubts in Physics |
| Chemistry teacher | Classes, practice guidance, doubts in Chemistry |
| Mathematics teacher | Classes, practice guidance, doubts in Maths |
| Mentor | Timetable, weekly/monthly reviews, test analysis, exam strategy, motivation, parent updates. Detects distress and escalates to parents and a human. Is NOT a therapist. |

Doubts go to the **subject teacher** (who already knows what was taught and where the student struggled), not to a separate doubt-solver.

**Humans** (not in the normal teaching loop): content reviewers (verify lessons, questions, answers), operations, safety escalation, engineering.

## 3. The learning cycle

1. **Learn** in an AI-led class: concepts, intuition, derivations, live whiteboard, questions.
2. **Practise independently**: solve, submit reasoning, receive graduated hints.
3. **Get assessed**: quizzes and exams check recall, application, accuracy, speed.
4. **Diagnose and repair**: identify the actual error, revisit the right idea, retry with a *different* problem.
5. **Reassess and progress**: re-test after a delay; advance only on sufficient evidence.

Why: watching an explanation is not the same as being able to solve a problem. MENTORA must collect evidence of what the student can actually do and use it to choose the next activity.

## 4. Schedule and rhythm (defaults to test)

A personalised timetable, maintained by the Mentor, built around school hours. Classes run on a regular schedule like a coaching institute; because each class is 1:1, the student can also shift a class.

| Frequency | Activity |
|---|---|
| Before a new topic | Entry quiz (3–5 questions, ~5–8 min) on prerequisites |
| Each class | 20–30 min concept lesson, or 30–45 min problem-solving class, or a 60–90 min combined block with a break |
| Inside each class | Mid-class checks (1–2 questions at natural points) |
| End of each class | Exit quiz (3–6 questions, ~5–10 min) + class notes |
| Most days | Daily practice (DPP), ~35–60 min |
| Weekly | Cumulative quiz or chapter test |
| Every 2–4 weeks | Part-syllabus test |
| Monthly / milestones | Full mock in the current official JEE format |
| Ongoing | Spaced-revision quizzes on earlier topics |

The teacher does not follow the clock mechanically: it slows down, re-explains or moves ahead based on evidence.

Example 75-minute block: 0–5 retrieval from last lesson · 5–20 intuition and concept · 20–35 derivation / worked example · 35–50 harder problems · 50–65 student solves with adaptive hints · 65–72 independent exit questions · 72–75 summary and next steps.

## 5. How a class runs

1. **Prepare** — select the approved lesson, check prerequisites and the student's recent evidence.
2. **Open** — state the objective, ask a short retrieval question, set notation.
3. **Teach** — explain, derive, draw; speech and whiteboard stay in sync.
4. **Interact** — student can interrupt, ask "why?", ask for a simpler explanation or another example, challenge a step, write on the board. The teacher answers *in context* and resumes at the right point (it does not restart).
5. **Practise** — hand over a problem; observe; decide whether to wait, ask a diagnostic question, hint, or explain.
6. **Assess** — independent exit questions, no hints.
7. **Close** — summary, unresolved doubts recorded, notes and DPP issued, next steps planned.

### The teaching turn (how every teacher turn is produced)

1. Read what the student did (speech, text, board, photo) → **E**
2. Update what we believe they know, cautiously → **S**
3. **M1.5** picks the next teaching *move* from a small fixed set: explain next step · ask a check question · hint (level 1/2/3) · simpler example · revisit a prerequisite · recap · give the full answer · hand over a problem → **D**. This must be fast (deterministic rules, milliseconds).
4. The AI model writes that move: spoken words + whiteboard operations, in the teacher's persona → **P**
5. Checker: maths/physics validity (SymPy, units, limiting cases), board operations valid, consistent with the approved lesson. If it fails, fix or say "let me check that".
6. App plays speech and board together; the student can interrupt at any time.

### What "natural" means (testable)
- Short teaching turns; purposeful questions at meaningful points; waits for the student's answer.
- Responds to what the student actually said, not to a script.
- Remembers the session: current concept, steps explained, notation, board elements, student answers, open doubts. "This step" and "that graph" resolve correctly.
- Interruptible; resumes where it left off.
- Repairs misunderstandings, including speech-recognition errors ("did you say 'sine' or 'sign'?").
- Re-checks understanding with a NEW question, never just "do you understand?".
- Honest about uncertainty; never invents an answer to keep talking.
- Student control: hint, full solution, alternative method, more practice, pause, summary.

### Whiteboard
A semantic, structured board, not free pixels: every element (equation, axis, graph, vector, free-body diagram, structure, label) has an ID, so the teacher can refer to it, highlight it, edit it, and the replay can reconstruct it exactly. Maths rendered from validated LaTeX (fallback if malformed). Progressive reveal and highlighting synchronised with speech. Later: student writes on the board; teacher reads student's handwriting (only claimed once measured).

## 5A. Adaptivity — adapting to every kind of student

Adaptation must be concrete and testable. MENTORA adapts along these dimensions, each driven by evidence (E → S) and decided by M1.5 (D):

| Dimension | How it is sensed | How the teacher adapts |
|---|---|---|
| Starting level | Entry quiz, early answers | Skip or add prerequisite steps; choose difficulty tier |
| Pace | Answer speed, "I know this", hint use | Fast-track (skip explanation when retrieval shows mastery) or slow down |
| Preferred route | Which explanation worked before | Each key idea has ≥2 authored routes (e.g. calculus vs energy, graph vs algebra, analogy vs derivation) |
| Misconception profile | Branch matches, error patterns | Targeted repair branches; re-check with new questions; later spaced re-tests |
| Confidence / anxiety | Self-reports, hesitation, "I'm bad at this" | Smaller steps, more wins early, calm tone; Mentor follow-up |
| Goal | Onboarding (Main vs Advanced, target) | Problem difficulty, exam-strategy content, test mix |
| Time available | Timetable, session length chosen | Shorter lesson variants; DPP size |
| Language | Student choice (can switch anytime) | English or Hinglish (Hindi + English mix) delivery; board notation always standard English/LaTeX as in JEE |
| Retention | Spaced re-tests | Revision scheduling |

**Testing adaptivity:** the scenario harness runs a range of simulated student personas (weak/strong, fast/slow, anxious, overconfident, visual vs algebraic preference, Hinglish speaker, careless-arithmetic, deep-misconception). A teacher is "adaptive" only if its behaviour measurably differs across these personas in the right direction.

## 6. Teacher personas

Each of the four AI roles has its own **persona**, so learning feels like being taught by distinct, engaging people, not a monotonous machine. A persona is an authored, versioned specification (K).

**Principles chosen to earn trust and bring students back:** warm but competent; respectful (never mocking); consistent character across sessions; remembers the student; celebrates effort and real progress, not empty praise; honest about uncertainty. Students address them in the familiar Indian way ("Kavya ma'am", "Rohan sir"). **Every persona is openly an AI teacher** — the app always says so. Personas never claim fake qualifications (no "IIT alumnus", no years of experience) — both for honesty and because India's CCPA coaching guidelines prohibit false faculty claims. Never named after real teachers or competitor brands.

| | Physics | Chemistry | Mathematics | Mentor |
|---|---|---|---|---|
| Name | **Kavya Menon** (keeps the name already in the product) | **Rohan Bhatia** | **Aditya Rao** | **Meera Joshi** |
| Character | Woman, early 30s | Man, mid 30s | Man, around 30 | Woman, early 40s |
| Teaching style | Curious experimenter: "let's test that against reality"; everyday physics — cricket, trains, monsoon, phones; draws a lot | Storyteller: why reactions happen, electrons "wanting" stability; kitchen and real-world chemistry; mnemonics sparingly; warm humour | Pattern-spotter: puzzles, "why is this step allowed?", multiple methods, exam-speed shortcuts only after the idea is clear | Calm planner and coach: timetable, test analysis, honest feedback, motivation, parent updates |
| Tone | Calm, encouraging, gently playful | Lively, expressive | Crisp, precise, dry humour | Warm, steady, direct |
| Voice (TTS) | Indian-English female, warm, ~145 wpm | Indian-English male, energetic, ~150 wpm | Indian-English male, clear, ~140 wpm | Indian-English female, calm, ~135 wpm |
| Signature habit (sparingly) | Ends a tricky idea with a quick "let's test that" check | Asks "what does the electron want here?" | Asks "can we do it another way?" | Starts reviews with one specific win |

Voices: pick four clearly distinct Indian-English voices from what Android TTS / the browser actually offers, test them with students, and keep the choice in the persona file. Language: **both English and Hinglish (Hindi + English mix), chosen by the student and switchable anytime.** Every prepared lesson step is authored in both; technical terms stay in English (as in the JEE paper); board notation is identical in both. Hinglish speech output must be tested separately (on-device voices may handle mixed Hindi/English differently).

Hard limits: persona never overrides correctness, honesty, governance or safety.

**Anti-monotony rules (testable):** vary sentence openings, acknowledgements and examples; do not reuse the same phrase within a session; vary pace and pauses; use the student's own examples and interests; mix modes (story, question, board moment, quick challenge). Measure repetition across turns and sessions.

## 7. Daily practice (DPP) and assignments

DPP = **recall** (5–10 min, earlier topics) + **current topic** (15–25 min, foundational → application) + **challenge** (10–15 min, unfamiliar multi-step) + **error repair** (5–10 min, when needed, using a *different* question). Adjust to school load, fatigue and upcoming exams.

**When a student answers wrongly:** capture the attempt (answer, working, time, hints used) → classify cautiously (concept / assumption / algebra / arithmetic slip / misread / speech-recognition error) → ask a targeted follow-up → graduated hint → retry with a different related question → schedule a later re-check. Never label a misconception from one wrong answer.

**Assignments** have: objective; mix of conceptual, numerical, multi-step questions; difficulty matched to demonstrated level; reasonable deadline; worked feedback; retry; review of important errors.

## 8. Quizzes and assessment modes

Four quiz types: **Entry** (prerequisites), **Exit** (end of class), **Topic mastery** (15–25 min, varied forms), **Spaced revision** (days/weeks later).

| Mode | Hints | Feedback | Purpose |
|---|---|---|---|
| Learning practice | Progressive | Immediate | Teach while practising |
| Diagnostic quiz | Withheld until submitted | After submission | Measure understanding |
| Timed mock | None | After submission | Simulate the real exam |
| Error repair | If needed | During retry | Fix a specific weakness |

Test interface: question palette, mark for review, change answers, visible timer, auto-save and recovery, correct rendering of maths and diagrams. Support every real JEE format: single-correct, multiple-correct (with JEE partial marking), integer, numerical with decimals, matching/list types, comprehension/paragraph.

## 9. Exams

Ladder: **Topic test** (20–45 min) → **Cumulative chapter test** (45–90 min) → **Part-syllabus test** (60–120 min) → **Full mock** that reproduces the current official JEE Main / JEE Advanced pattern, timing and marking for a specific year (pattern stored as a versioned, verified configuration).

Weekly and monthly tests run at fixed times for all students, so MENTORA can publish rankings among its own students.

**After every exam:** score, accuracy, time per question, attempted/unattempted → error analysis (knowledge gap, concept error, slip, misread, strategy, time pressure, uncertain grading) → patterns → repair plan (targeted lessons, questions, revision) → fresh-question retest now and after a delay. A single test never becomes a permanent label.

## 10. Grading

- Objective: deterministic matching; numerical tolerance per question.
- Numerical: units, sign, precision, answer conventions.
- Derivations: check steps where possible (SymPy), not only the final answer.
- Physics: assumptions, dimensions, sign conventions, physical consistency.
- Chemistry: stoichiometry, charges, structures, reaction constraints.
- Long-form: rubric defined before the test; independent verification path. An AI grading an AI is not proof.
- If grading is uncertain: mark as uncertain/deferred; never invent a precise score.

## 11. Doubts

Channels: voice, chat, photo upload, camera snapshot of a page or the student's own working. Routed to the subject teacher with the student's context. The teacher confirms its reading of a photo ("I read this as ... — correct?") before solving when the image is unclear. Photo/handwriting reading accuracy must be measured before it is promised.

## 12. Class notes

Generated from the lesson's structured content (equations and diagrams from the board, not reconstructed from speech), plus the student's own doubts and mistakes from that class. Downloadable.

## 13. Recording and replay

Every class is recorded as an **event log**, not a screen video:
- Teacher speech as text segments with timestamps (audio can be re-synthesised on replay, so it need not be stored).
- Whiteboard operations with element IDs, timestamps, sequence numbers and periodic checkpoints.
- Student interactions: questions, answers, hints used, submissions, board work.
- Lesson version and model configuration.

This gives synchronised replay, a searchable transcript ("jump to where momentum conservation was explained"), links from a later mistake back to the exact explanation, resume-where-you-left-off, and quality review.

Do not store raw student microphone audio or camera video by default. Recording status always visible. Encrypted; access limited to the student, guardian and authorised staff; purpose-based retention; export and deletion.

## 14. Core architecture principle: prepare once, serve everyone, go live only at the edges

**Why:** at ₹129–199/month the AI budget is only about ₹30–50 per student per month. Generating every minute of every class live for every student would cost roughly 10–40× that.

- **One format for everything: the lesson timeline.** A lesson is an authored, reviewed sequence of steps; each step = spoken text (in persona) + whiteboard operations + check questions + pre-planned branches for common misconceptions. The same format is used for authoring, live playback, recording/replay and notes.
- **Prepared once, replayed for every student** at near-zero cost: board rendered on the device; speech from the device's own voice, or premium audio generated once per lesson (one-time cost, shared by all students).
- **Live AI only at the edges:** free-form questions, unexpected wrong answers, photo doubts, genuinely new situations. Cheap model first; escalate to a stronger model for hard cases. Fair-use limits on live AI per day on the base plan.
- **M1.5 decides every move**, whether the content comes from a prepared branch or from live AI.
- The student should still experience it as live, because the teacher responds to *their* answers.

## 14A. Model tiers — cheap where possible, strong where needed

Live AI does three different jobs; each gets the cheapest model that passes measured quality bars:

| Tier | Job | Model class |
|---|---|---|
| 1 Classify | Map a free-text student reply onto the lesson's pre-planned branches ("which of these did the student mean?") | Small/cheap model; very short prompts. Most "live" moments end here and stay on the prepared path |
| 2 Converse | Write a short reply inside the move M1.5 chose, with lesson context and recent conversation | Cheap-to-mid model, chosen by the scenario harness |
| 3 Reason | Solve a genuinely new doubt or photo problem; generate worked solutions | Strong reasoning model, with computational checks (SymPy, units) before the student sees it |

Rules: use paid tiers from reputable providers with data-use terms acceptable for minors' data; free tiers only for development experiments, never for real students. Several providers are fine (redundancy, cost, and independent review) — but never multiple accounts with the same provider to stretch free limits (against providers' terms; risks bans). Model choice is decided by measurement on the scenario harness, not by reputation.

### K / E / S / D / P in this product

| Layer | Examples in MENTORA |
|---|---|
| K (reviewed knowledge) | Lesson timelines, persona specs, reviewed questions with worked solutions, rubrics, official exam-pattern configs |
| E (evidence) | Student answers, working, photos, transcripts, timings; source documents with provenance |
| S (learner state) | Mastery estimates per skill, misconception hypotheses with uncertainty, revision due dates |
| D (decisions, by M1.5 only) | Next teaching move, hint level, next activity, quiz selection, remediation, timetable changes |
| P (proposals) | Live AI explanations, AI-drafted diagnoses, AI-generated questions and notes before review |

## 15. Voice

- Start with **on-device speech** (Android speech recognition and TTS; browser Web Speech API on the website) to keep costs near zero. Test quality, Indian-English accents, maths vocabulary and voice variety before relying on it.
- Use premium voices for *prepared* lesson audio if needed, because that cost is paid once per lesson, not per student.
- Never read raw LaTeX aloud; convert to natural spoken maths while the board shows exact notation.
- Barge-in: the teacher stops when the student starts speaking.
- Target: the teacher starts responding within about 1.5 seconds of the student finishing (to be measured).
- Text chat always available as a fallback.

## 16. Business constraints

- Price: about ₹129–199 per month.
- AI cost budget: about ₹30–50 per student per month (≈30% of net revenue after 18% GST and payment/app-store fees).
- Reference point: large competitors sell year-long JEE batches for a few thousand rupees with near-zero cost per extra student; MENTORA's 1:1 AI has a real cost per student, so the architecture in §14 is mandatory, not optional.

## 17. Content and rights (updated v1.3)

**Founder statement (3 Oct 2026):** the founder has paid the coaching institutes and publishers for commercial use of their material. This makes the corpus in `Mentora Material` the **primary source** for the question bank, worked solutions and teaching reference — not merely reference/evaluation material.

Conditions so this stays safe:
- **Record every licence in the rights registry** (publisher, what it covers: commercial use to students, modification/adaptation, AI processing by third-party services, AI training if ever needed, territory, duration). Attach the agreements.
- **Map each file to a licence.** The atlas found many files are redistributed copies (Telegram, libgen, Anna's Archive). A file counts as licensed only if its content is covered by a licence the founder holds; otherwise it stays reference-only until confirmed. Not legal advice — a lawyer should confirm the scope once.
- Serve licensed questions with provenance kept internally; still verify every answer (coaching keys contain errors).
- Official JEE papers remain separate (official exam body).
- MENTORA's own original questions still fill gaps (thin chapters, new skill-targeted items).

Need: roughly 200–400 verified questions per chapter for DPPs, quizzes and tests. With licensed material (≈112,000 distinct questions, ≈71,000 with worked solutions, per the atlas) the bottleneck moves from *supply* to *accurate reading and verification* (§25).

## 18. Safety, privacy and legal

- Students are mostly minors: verifiable parental consent under India's DPDP Rules 2025 (consent provisions phase in around May 2027). Legal review required.
- Data minimisation: no raw audio/video retention by default; no use of student data to train third-party models without a valid legal basis and permission.
- Mentor escalates signs of distress or self-harm to parents and a human immediately and provides helpline information; it never attempts therapy.
- No guaranteed-rank marketing; testimonials only with written consent obtained after the result.
- Personas never impersonate real teachers or brands.

## 19. Build order (each step measured before the next)

1. **Reality check** of the product and the intelligence repo, plus cost measurement and a teaching-scenario baseline.
2. **First slice:** one chapter (probably Simple Harmonic Motion), Physics teacher persona, lesson timeline format, whiteboard + text on the website, exit quiz, notes, event-log recording. Measured with the teaching scenarios.
3. Verified question bank for that chapter → DPP + quizzes + chapter test.
4. Doubts by photo; student answers checked step by step.
5. On-device voice with barge-in.
6. Android app.
7. Mentor role + timetable + weekly test + parent summary.
8. Pilot with 5–10 real students (before/after test).
9. Next chapters and subjects, then full mocks.

### Capability measures
- **T1** solves correctly (verified test set), low confident-wrong rate.
- **T2** explanations accepted by a qualified reviewer.
- **T3** tutoring quality on scripted scenarios (diagnosis, hints that don't leak, re-checks, interruption recovery, persona consistency, non-repetition).
- **T4** whiteboard correct and in sync with speech.
- **T5** real students improve on fresh questions and come back.
- **Cost:** AI cost per student-month within budget. **Latency:** within target.

## 20. Open decisions for the founder

- ~~Teacher names, genders, voices~~ — decided in §6 (voices to be tested).
- ~~Human reviewers~~ — decided: AI review (§21) for now.
- ~~Language~~ — decided: English and Hinglish, student's choice, from the first slice.
- AI providers and keys for each tier (§14A).
- Exact price and the fair-use limit on live AI (after the first slice measures the live-edge rate).
- Legal review: content rights, DPDP compliance for minors.

## 21. Review policy — AI review (founder decision, 2 Oct 2026)

There is currently no human subject expert. The founder has decided that content is reviewed by AI. This is a deliberate change to the earlier rule "K only after human review", so it must be done rigorously and its reliability **measured**:

1. **Computation first.** Every numeric answer and stated equation is checked by code (SymPy, numeric solving, units, limiting cases, enumeration/simulation where possible). Computation outranks any model's opinion.
2. **Independent solving by a different model family.** The model that wrote an item never approves it. A model from a different provider solves the question blind; disagreement → item blocked, not shipped.
3. **Critic pass with a checklist:** physics/chemistry/maths correctness, hidden assumptions, ambiguity, units, whether distractors are actually wrong, whether hints leak the answer, persona tone, pedagogy (does the step teach or just tell?).
4. **Anchors:** official answer keys where they exist outrank all models; disagreements are flagged, never silently overruled.
5. **Measured reviewer reliability (seeded errors):** regularly plant known mistakes (wrong sign, wrong unit, wrong key, misleading hint, physics error) into copies of content and measure what fraction the AI review pipeline catches. Report this "catch rate" with every content release. If it is low for a category, that category needs another check.
6. **Status levels:** `draft` → `machine_verified` (passed 1–4) → `human_reviewed` (later, when a qualified human samples it). Only `machine_verified` or higher is served to students, always with a visible "Report an error" button.
7. **After launch, students are part of the check:** error reports, and statistical alarms (e.g. strong students failing an item far more than expected suggests a wrong key) send items back for review fast.
8. **Founder's role:** spot-check a small random sample for teaching feel and clarity; when revenue allows, add a part-time qualified reviewer for sampling audits.

## 22. Golden-transcript decisions (G1–G3, format v0)

Approved as the design target, with fixes:
- Moves `locate_confusion` and `answer_interruption` are approved and join the fixed move set.
- **Grounding rule:** the teacher may only refer to what the student actually said. (G2.1a says "you just told me the pull doubles" although the student never answered G2.0 — this exact error must be caught by the validator and the critic.)
- Every step needs a branch for **student-initiated** turns (the student raises a question or a misconception before answering), not only "other → LIVE".
- Speech and board must agree on numbers (G2.5 says "about two percent", the board says ≈1.7 % — correct value is ≈1.7 %).
- Analogies must be coherent (G3.3's "cricket ball's energy … stored in the spring" mixes two systems; G2.1's "think like a bowler" is vague).
- Format additions: alternate **routes** per key idea (as G3 does: calculus vs energy); **skip conditions** for fast learners; 2–3 phrasing variants per step for anti-monotony; branch matching order = deterministic (numbers with tolerance, options) → Tier-1 classifier into known branches → LIVE.

## 23. JEE-level expertise — what "top teacher" means here

JEE (especially Advanced) tests whether a student can think like a problem-solver, not recall formulas. MENTORA must teach and assess these **seven skills** explicitly:

| # | Skill | What the teacher does about it |
|---|---|---|
| S1 | Conceptual understanding (why a law works) | Derive, don't quote; explain assumptions and where a result stops being valid |
| S2 | Application to unfamiliar situations | Practise on changed scenarios, not repeats of worked examples |
| S3 | Multi-concept integration | Problems that join two or more ideas (e.g. SHM + energy + collisions); teach how to spot which ideas a problem needs |
| S4 | Mathematical reasoning | Derivations, manipulation, approximations, graphs |
| S5 | Problem-solving creativity | Compare methods; ask "is there a smarter route?"; symmetry, limiting cases, frames of reference, dimensional shortcuts |
| S6 | Precision | Signs, units, boundary conditions, special cases, exceptions — drilled, not assumed |
| S7 | Discriminating between plausible approaches/options | Options built from real misconceptions; teach checking by limiting cases, dimensions, extreme values, elimination |

**How a JEE-style question is built (and how MENTORA writes practice questions):** start from a fundamental concept → add a constraint or an unfamiliar scenario → combine with another concept → write plausible wrong options from documented misconceptions → verify every option by computation. Every question MENTORA serves is tagged with the skills (S1–S7) it tests, its concepts, its difficulty, and which misconception each wrong option represents.

**Teaching implications:**
- Every lesson includes "what if?" variations (change a condition, predict the effect) and at least one unfamiliar application, not just the standard example.
- After the concept is solid, the teacher deliberately mixes in earlier chapters (integration), so students learn to recognise which concepts a problem needs.
- Exam technique is taught explicitly: choosing an approach, checking options by limits and dimensions, partial-marking strategy for multiple-correct questions, time management.
- The learner model tracks the student **per skill (S1–S7) as well as per chapter**, so the teacher knows e.g. "concepts strong, integration weak, careless with signs" and targets that.
- Practice follows a difficulty ladder: single-concept → changed scenario → multi-concept → JEE Advanced level, advancing on evidence.

**Proving expert level (measured, not claimed):**
- **Solver benchmark:** the AI solves the official JEE Advanced questions that have official keys (≈383, 2023–2026) with verified reasoning; report accuracy by subject, question type and skill, plus the confident-wrong rate. (Official papers are read from page images via careful AI transcription, double-checked, because their PDF text layer breaks maths.)
- **Question-quality check:** MENTORA-written questions are compared against official questions on skill coverage, difficulty and distractor quality by an independent model.
- **Student outcomes:** pilot students improve on fresh JEE-level questions, per skill.

## 24. Full-syllabus roadmap

Goal: the entire JEE Main + Advanced syllabus (82 chapters in the official JEE Advanced syllabus, plus JEE Main-only topics), taught at expert level.

1. **Prove the format on one chapter** (SHM slice, in progress).
2. **Turn it into a chapter "factory"**: for each chapter — concept map and prerequisites → lessons with routes, misconception branches, "what if" variations (both languages) → JEE-style question bank (≈200+ per chapter, skill-tagged) → AI review with computation, independent solving and seeded-error tests → chapter test.
3. **Run the solver benchmark** on official JEE Advanced papers and keep it as a permanent quality gate.
4. **Scale chapter by chapter**, ordered by prerequisites and JEE weightage, measuring cost and quality per chapter. Each chapter's question bank comes mainly from the licensed corpus (extracted from page images and verified, §17), topped up with AI-written questions where the corpus is thin.
5. **Mixed-chapter and full mock tests** once enough chapters exist; then the Mentor, timetable and pilot students.

Speed depends on how much of the factory is automated; the first two or three chapters after SHM will tell us the real time per chapter.

## 25. Reading the corpus — symbols, structures and diagrams

Facts from the atlas: maths in PDF text layers is broken in ~96% of files; ~1 in 5 files is pictures only. So **every question is read from the page image**, never from the text layer.

**One pipeline, page by page:**
1. **Find** (cheap, local): the atlas already knows each file's type, chapters, and where answers/solutions live. Render only the needed pages as images.
2. **Read** with vision AI models into structured form, by content type:

| Content | Stored as | Machine check |
|---|---|---|
| Text and maths (fractions, vectors, integrals, matrices, Greek) | LaTeX | Parses (KaTeX); re-rendered and compared with the original crop |
| Chemical structures (benzene rings, organic molecules) | SMILES (e.g. benzene = `c1ccccc1`) + the original image crop | RDKit: valid molecule, valency, formula; re-drawn and compared |
| Reactions and mechanisms | Reaction SMILES / step list + image crop | Atom balance where applicable; mechanisms kept as image + description |
| Circuits | Netlist (components, values, connections) + crop | Solved by a circuit solver; result compared with the key |
| Graphs | Axes, labelled points, function where clear + crop | Re-plotted and compared |
| Geometry / ray / free-body diagrams | Labelled description, coordinates where possible + crop | Re-drawn; used by the solver |
| Tables, matrix-match lists | Structured tables | Row/column counts |

   Licensed figures can be shown to students as the original image; the structured version lets the AI reason about them and lets the whiteboard redraw them.
3. **Link** each question to its options, answer key and worked solution (often far apart; the atlas's page maps tell where).
4. **Verify**: two different AI readers transcribe independently → disagreements re-read or flagged; render-and-compare; **answer checksum** — an independent solve of the transcribed question must match the source answer key (if the transcription lost a sign or a subscript, the answer usually won't match); then the AI review policy (§21).
5. **Tag**: chapter, concepts, skills S1–S7, difficulty, misconception behind each wrong option, question type.
6. **Store** as verified items with full provenance (file, page, crop, licence).

**Choose readers by measurement:** a pilot compares general vision models (several providers) and specialist tools (e.g. maths OCR, chemistry structure recognisers) on a hand-checked sample of each page type, then uses the cheapest reader that meets the accuracy bar for each type. The existing PYQ-Perception benchmark harness in `mentora-source-corpus` is reused for this.

**Order:** pilot (~150 pages across page types) → chapter by chapter in step with the chapter factory (§24), not all 45,000 pages at once. Deduplicate first; skip non-question pages.

**Intelligence on top of the corpus:** the teacher does not need the corpus to "learn" physics; it uses the processed corpus as (a) the question bank, (b) worked-solution and method references retrieved for the current problem, (c) the misconception catalogue (from wrong options and common errors), (d) difficulty and skill calibration, (e) evaluation sets. Fine-tuning a model on it is not planned now (and needs explicit licence permission for AI training).

## 26. Live teacher, schedule and price (founder decisions, 3 Oct 2026) — overrides §4, §14, §16 where different

**Why:** the founder tried the scripted class (prepared lines + branch matching, live AI on ~1.6% of turns) and it felt like a bot. A real 1:1 teacher must respond live to everything the student says.

**Architecture (replaces "prepare once, live AI only at the edges"):**
- The class is a **live voice call**: continuous listening, barge-in, natural turn-taking, short backchannels, the teacher's speech streamed sentence by sentence, board actions emitted with speech.
- **Every student utterance goes to the live teacher brain** (an LLM with persona + lesson plan + running class summary + student profile). M1.5 approves each proposed teaching move with fast rules.
- Prepared lessons become the teacher's **lesson plan and notes** (goals, the "why" chain, derivations, misconceptions, checks, validated diagrams) — and, in the **hybrid** mode, pre-written explanation segments the teacher delivers live and can interrupt or adapt. Never a rigid script.
- Correctness guards stay: numbers computed by tools, equations validated, board actions validated.
- Long classes use a rolling class summary instead of the full transcript (cost and coherence).

**Schedule:** 3 hours of live class per day, 2 subjects per day (≈1.5 h each), about 6 days a week (≈78 class hours/month for full attendance). Plus pre-class and post-class work, quizzes, DPPs, and **monthly tests: one JEE Main-pattern and one JEE Advanced-pattern full test.**

**Price:** ₹499–599 per student per month (excluding GST). AI cost target ≈ **₹170–235 per student per month at full attendance** (≈40% of net revenue). Cheapest adequate fast model + caching + on-device voice + hybrid explanations; stronger models only for rare hard moments. If measured teaching quality needs costlier models, revisit price (≈₹999) or live-hour limits — decided by measurement and the founder's own trial.

## 27. Teacher long-term memory

A real teacher remembers what was taught, where the student went wrong, what fixed it, and what is still pending — and uses that live ("Remember Tuesday's merry-go-round? Same trap here."). MENTORA's teachers must too.

| Layer | Contents | K/E/S |
|---|---|---|
| 1. Record | Every class event: speech, board, answers, timings, hints (event log + replay — exists) | E |
| 2. Learner state | Per concept and skill: mastery with evidence and uncertainty; misconceptions with lifecycle suspected → confirmed → repaired → relapsed, **including which explanation repaired it** and when; preferred routes; pace; confidence; open doubts; spaced-revision due dates | S |
| 3. Teacher's diary | Auto-written after each class: taught, struggled, fixed, pending, promises ("revisit energy graphs Friday"), small personal notes (interests, exam anxiety) | S (derived, revisable) |
| 4. Live use | Before class: a compact **student brief** in the teacher's context. During class: when an error or question matches past history, retrieve that exact episode (date, explanation used, board snapshot, replay link) and refer to it | D via M1.5 |

Rules:
- **Grounded memory only:** a teacher may refer to a past event only if it exists in the records (validator checks; same rule as within-class grounding).
- **Evidence, not labels:** beliefs about the student stay probabilistic and are revised; one bad day never becomes "weak in SHM".
- **Shared across teachers:** subject teachers see cross-subject gaps relevant to them (e.g. calculus gaps for Physics); the Mentor sees everything for reviews and parent updates.
- **Transparent and correctable:** the student can see what each teacher "remembers" about them and flag errors.
- **Privacy:** no raw student audio stored by default; parental consent; export and deletion supported (DPDP).
- **Cost:** the brief is small and cacheable; retrieval only when relevant.

## 28. Learning-resource formats, Content Studio, and the Rankers track (3 Oct 2026)

**Resource formats** (inspired by teacher-tool catalogues such as Eduaide, adapted for a student-facing JEE teacher). The chapter factory produces, per concept, AI-reviewed and in both languages:

| Format | Use |
|---|---|
| Warm-up questions (retrieval from earlier lessons) | First minutes of every class |
| "What do you already know?" check | Before a new chapter (entry quiz) |
| Lesson plan + spoken explanation segments | The class (internal) |
| DPP sets, basic → JEE Advanced | After class |
| Concept maps and formula sheets with "when this fails" notes | Notes and revision |
| Speed rounds and "spot the trap" challenges (misconception options) | Mid-class energy breaks, weekend revision |
| Flashcards with spaced repetition | Daily 10 minutes |
| Entry / exit / mastery quizzes, chapter tests, monthly Main + Advanced mocks | On schedule |
| "Defend your answer" discussions (teacher argues a wrong option) | Higher-level classes |

**Content Studio (founder-facing, after the live teacher works):** browse chapters and concepts; view lesson plans; preview segments with the teacher's voice; see notes, DPPs, quizzes and review status; approve or regenerate. Needed because the founder is the only human overseeing content. A B2B version for schools/coaching institutes is a possible later business, not now.

**Rankers track** (designing for AIR < 100 without promising it): students move in based on test performance. Adds depth beyond the syllabus (hardest JEE Advanced and Olympiad-style problems from licensed material, multiple methods, proofs), timed speed-and-accuracy sets, a personal error log with targeted drills, paper strategy (attempt order, skipping, partial marking), more full mocks with deep analysis, and Mentor support for stamina and pressure. Measured by mock-test percentile trends; never marketed as a rank guarantee (CCPA).

## 29. Teaching board engine (founder decision, 3 Oct 2026)

**Goal:** the teacher *builds* every diagram live — stroke by stroke, pointing with a pen, annotating, transforming — like an excellent teacher at a real whiteboard. Static pictures are not teaching.

**Decision:** not Excalidraw / tldraw / Skia as the core (they are human-drawing canvases or a raw graphics engine). Build MENTORA's own **semantic teaching-board engine** on the existing board model (objects with IDs, event log, replay):
- **Board language** the AI emits as validated tool calls, e.g. `draw_axes`, `plot(fn)`, `vector(from,to,label)`, `trajectory`, `spring`, `incline`, `pulley`, `ray/lens`, `circuit_element`, `write_math(latex)`, `draw_molecule(smiles)`, `label_atom(mol, atom, "o")`, `curved_arrow(from: lone_pair|bond|atom, to: bond|atom)`, `resonance_sequence`, `reaction_arrow`, `point_to(id|anchor)`, `circle(id)`, `underline(id)`, `erase`, `simulate(scene, params)`. High-level commands compile to low-level ops for replay.
- **Rendering:** SVG paths animated as handwriting (write-on / draw-on) with a visible pen cursor; hand-drawn feel via rough.js + perfect-freehand; equations via MathJax SVG (clip-wipe write-on) or KaTeX where animation isn't needed; persona handwriting font and marker colours for notes.
- **Chemistry:** RDKit (server; RDKit.js where light enough) computes 2D layouts from SMILES; every atom/bond addressable; curved electron-pushing arrows; resonance sequences; reaction schemes.
- **Physics:** a primitive library (vectors, components, FBD blocks, springs, inclines, pulleys, trajectories, rays, lenses, circuit parts) plus **live mini-simulations** with updating vectors and synchronized graphs.
- **Maths:** step-by-step derivations with aligned lines, function plots drawn progressively, geometry constructions.
- **Platforms:** one web engine; Android phone/tablet app (and iOS later) wraps the same web app (e.g. Capacitor). Heavy layout work on the server; devices only animate paths. Skia (React Native Skia) remains an option later if native performance requires it.
- **Recording:** the event log of board commands with timings is the recording — exact replay, tiny files, searchable moments; MP4 export later.
- **Acceptance demos:** projectile motion (trace, components, g at points, simulation with shrinking vertical component); benzene ortho/meta/para with –OH (bond-by-bond, labels with pen, lone-pair arrows, resonance, o/p charge circled); SHM block-spring with synchronized x–t graph; a maths derivation with aligned steps.
