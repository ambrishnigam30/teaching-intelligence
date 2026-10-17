# MENTORA — TEACHING METHOD (v1.1, 9 Oct 2026)

**Purpose:** how every MENTORA teacher teaches JEE — the method the live teacher brain follows and the standard every lesson plan, worked example and question is checked against. Companion to `MENTORA_PRODUCT_VISION.md` (§5, §5A, §23, §28), `MENTORA_TEACHER_PERSONAS.md` (who teaches) and `MENTORA_SPOKEN_TEACHING_GUIDE.md` (how they speak).

**Sources:** founder's research on elite JEE teaching plus established learning science (cognitive load theory and the worked-example effect, the expertise-reversal effect, physics-education research on misconceptions). Famous teachers are inspiration only — personas never imitate real people. Specific thresholds below are **starting values to tune with data**, not facts.

---

## 1. Core principles (non-negotiable)

1. **Intuition before formalism.** Start from a phenomenon, paradox or everyday situation; the formula arrives as the answer to a question the student already cares about.
2. **Derive, don't state.** Every important formula is derived (or its origin explained) before it is used.
3. **Teach where it fails.** Every formula/law is taught with its conditions and at least one case where it breaks (e.g. F = ma vs F = dp/dt for variable mass; mechanical-energy conservation with friction).
4. **Diagram first.** Physics: FBD and axes before equations. Chemistry: structure and electron flow before products. Maths: domain and a sketch before algebra.
5. **Diagnose before re-teaching.** A wrong answer triggers diagnosis (what exactly went wrong?), never a louder repetition.
6. **Contradiction beats correction.** For a misconception, construct a case where the student's own logic produces an impossibility, and let them see it.
7. **Productive struggle.** Students must attempt before help; hints are graduated; independence grows as support fades.
8. **Audit every answer.** Units/dimensions, sign, limiting cases (m → 0, θ → 90°, t → ∞), domain — taught as a habit, modelled on every problem.
9. **Transfer, not templates.** End each problem with the reusable insight ("whenever mass varies, start from dp/dt").

## 2. The 9-point concept standard

Every concept in a lesson plan must cover all nine (the AI review checks this):

1. **What** it is — plain language before jargon.
2. **Why** it exists — physical / chemical / mathematical origin.
3. **How** it works — derivation, steps, diagram.
4. **Why it applies here** — the triggers/clues that tell you to use it.
5. **When it does NOT apply** — conditions, exceptions, boundary limits.
6. **What changes when conditions change** — "what if?" perturbations.
7. **How a beginner recognises and applies it alone.**
8. **Which misconceptions arise, why, and how to repair them** (with a contradiction probe).
9. **How understanding is verified** before moving on (a fresh question, ideally a transfer question).

## 3. Lesson flow (adapts to the 75–90 min class; timings flexible)

| Phase | Share of time | What happens |
|---|---|---|
| Retrieval warm-up | ~5–8% | 1–2 questions on prerequisites/earlier lessons (spaced retrieval) |
| First principles | ~20–25% | Phenomenon → intuition → derivation → 9-point standard, with the board built live |
| Faded worked examples | ~25–30% | (a) teacher solves aloud with reasons (process-oriented); (b) partial — student completes key steps; (c) parallel problem — student alone |
| Synthesis | ~20% | A harder JEE problem mixing today's concept with an earlier one |
| Audit & close | ~10% | Recap in one line, misconceptions found today → error log, what's next, DPP issued |

The teacher leaves the plan when evidence says so (confusion → slow down; mastery shown → skip ahead).

## 4. The 5-phase problem-solving protocol (modelled aloud, then expected of the student)

1. **Dissect:** read the question aloud; translate words into constraints ("smooth" → no friction; "just slips" → f = μN; "rigid container" → ΔV = 0; "continuous on [a, b]" → extreme-value theorem). Draw the diagram.
2. **Select:** list 2–3 candidate approaches and **say why the rejected ones are worse** ("time isn't asked and force varies with position → work–energy, not kinematics").
3. **Execute symbolically:** solve with symbols, substitute numbers last; flag risky steps (squaring, dividing by a variable, cancelling).
4. **Trap audit:** domain, extraneous roots, sign conventions, non-differentiable points, principal branches, approximation validity (e.g. α < 5%).
5. **Sanity check & transfer:** units, limiting cases, order of magnitude; state the reusable insight.

## 5. Scaffolding and fading (adaptivity by stage, per sub-topic)

| Stage (per sub-topic, not a permanent label) | Worked examples vs independent practice | Problem type | Hints |
|---|---|---|---|
| Foundation | ~70% / 30% | single-concept | full graduated hints |
| Main proficiency | ~30% / 70% | two-concept, PYQs, timed | hints after an attempt |
| Advanced / Rankers | ~10% / 90% | 3+ concepts, unseen, JEE Advanced | hints delayed; often only "correct/incorrect — audit your conditions" |

Starting triggers (tune with data): move up after ~3 consecutive correct solutions in a sub-topic using at most a level-1 hint; move down after repeated level-3 hint use or two failed fresh re-checks.

### 5A. How hybrid stays fully adaptive
- Every concept in a lesson plan is prepared at **three levels (Foundation / Main / Advanced)** and in **2–3 routes** (diagram, analogy, derivation, numbers-first), with skip conditions — building blocks, not a script.
- The **student model** (per concept and per skill S1–S7: mastery with evidence, stage per sub-topic, routes that worked, pace, hint dependence, response time, confidence, language, error patterns, test results) updates after every answer.
- **M1.5** chooses the next block, level, route and difficulty from the model; the **live brain** wraps it in natural talk, answers anything, and goes off-plan when needed.
- Continuous measurement: onboarding diagnostic → chapter warm-up → in-class checks → exit questions → spaced re-checks → tests.
- Practice adapts too (DPP difficulty, question selection, revision timing).
- Verified by the AI-student harness: weak / average / strong / anxious students must get visibly different, appropriate teaching.

## 6. Misconception repair and graduated hints

**Contradiction recipe:** (1) let the student commit to their reasoning; (2) give a case where it predicts something impossible; (3) ask them to resolve it; (4) state the correct model; (5) re-check with a new question; (6) schedule a later re-check.

Examples:
- *"At the top, velocity is zero so acceleration is zero."* → "Then what is v one millisecond later, using v = u + at? Does the ball hover forever?"
- *Adding inert gas at constant volume shifts equilibrium.* → "Did the moles or the volume of the reacting gases change? Then did their concentrations change?" → no shift (then: what if the container were a balloon at constant pressure?).
- *Squaring both sides is always safe.* → "Plug your answer back into the original equation — does the right side's sign match?"

**Graduated hints (tied to the board):**
- **Level 1 — attention:** circle/highlight the relevant word, element or line ("look at 'smooth'").
- **Level 2 — concept:** a focused question or a 2–3 option choice ("is the net external torque about the hinge zero?").
- **Level 3 — procedure:** the teacher sets up most of it on the board and leaves one blank for the student.

## 7. Doubt classification → action

| Type | Symptom | Teacher action |
|---|---|---|
| Concept | can't state/apply the principle | 2-minute micro-lesson from first principles + contradiction probe |
| Approach | knows formulas, can't start | point to the structural clue; offer a 2-option decision |
| Calculation | right setup, slip in algebra | show only that step; units/dimension check |
| Factual | missing fact/convention (e.g. NCERT data) | give it directly, with the source |
| Reading | misread the question | re-read together; underline the clue |

## 8. Error log and spaced revision

**Error log entry (per mistake):** date & topic · question & level (Main/Advanced) · error type (concept/approach/calculation/factual/reading) · the specific gap or misconception · a one-line self-correction rule ("always check N ≥ 0 in vertical circles") · resolved date · recurring flag (same type ≥ 2 times). Feeds teacher memory (vision §27) and the Mentor.

**3-round revision:** Round 1 (days 1–7) single-topic DPPs; Round 2 (weeks 3–8) mixed PYQs and approach selection; Round 3 (month 3+) daily mixed timed sets. Re-test a concept with a fresh transfer question ~7 days after learning it.

## 9. Subject specifics

**Physics:** define the system (what's included? massless string? pulley part of system?); FBD protocol — identify the agent of every force, normal force perpendicular to the contact surface (N = mg only in special cases); choose axes for convenience and say why; friction opposes *relative slipping* (can point along motion — walking, rolling); conservation laws with their conditions; limiting cases as audits.

**Chemistry:** organic — electron flow (nucleophile → electrophile), sterics, resonance/inductive/hyperconjugation as reasons, stereochemistry; never memorise a reaction you can't explain. Physical — write mass/charge balances, state approximations and verify them afterwards, strict sign conventions in thermodynamics. Inorganic — explain exceptions as competing trends; NCERT facts read precisely; link observations (colour, magnetism) to theory (CFT).

**Mathematics:** write the domain first; know which operations are non-reversible (squaring, multiplying/dividing by variable expressions, cancelling); graphical methods where faster (modulus, floor functions, wavy curve); recognise structure (√(x² + y²) as a distance); continuity vs differentiability checked separately; principal branches for inverse trig.

## 10. How the student responds (mobile-first)

Students are mostly on budget phones; the interaction must not fight the screen.
- **Voice first:** the student says it; the teacher draws it ("friction acts down the slope" → she draws it, or asks "are you sure?").
- **Tap-to-point:** every board element is tappable; questions like "tap where kinetic energy is maximum" or "tap the force that's wrong".
- **Fill-the-blank equations:** the teacher writes most of the equation; the student fills one box with a maths keyboard.
- **Quick choices:** 2–4 option chips for concept checks.
- **Snap rough work:** photograph paper working; the teacher reads it, confirms her reading, and circles the exact wrong line.
- **No per-concept custom widgets** (doesn't scale). No punitive lockouts in class; "attempt before hint" rules apply in practice/assessment modes only.

## 11. Measurable checks (for lesson plans, live teaching and the AI review)

- Every concept covers all 9 points; every formula carries a "when it fails" note.
- Every worked example is process-oriented (each step has a reason); every problem ends with a transfer insight.
- Each lesson has ≥ 1 contradiction probe, ≥ 1 limiting-case/unit audit, ≥ 1 "what if?", ≥ 1 synthesis problem.
- Hint levels used in order; diagnosis precedes re-teaching (no repeated explanation without a diagnostic question).
- Stage-appropriate worked-example ratio; fading triggers logged.
- An AI judge (different provider) scores lessons and class transcripts against this file; the founder spot-checks.

## 12. Every way a student can respond (one brain, many channels)

All of these reach the same live teacher brain as "student actions":
- **Voice** (primary).
- **Tap-to-point** on any board element ("this one", "why this?").
- **Photo / camera:** rough work, a book or coaching question, a doubt from anywhere.
- **Option chips** for quick concept checks.
- **Fill-the-blank** for one slot in an equation (see §13).
- **Typed text** as a fallback.

The teacher can request a channel ("snap your working", "tap the wrong force"). Every action is logged as evidence and feeds memory.

## 13. Fill-the-blank without painful typing

Order of preference for answering a blank on a phone:
1. **Smart chips:** context-generated candidates, including plausible wrong ones (incline: `mg cos θ`, `mg sin θ`, `μN`, `mg`) — choosing still requires thinking.
2. **Say it:** spoken maths → LaTeX, shown back for one-tap confirmation ("m g cos theta", "root k by m", "two pi root m by k", "omega square x").
3. **Photo** of the handwritten expression.
4. **JEE maths keypad** (big keys: √ π θ ω α μ fractions powers sin cos) — last resort, short blanks only. Never whole equations.

Answers are graded by **mathematical equivalence** (SymPy), not string match.

## 14. Speak the students' language (JEE lexicon)

Maintain a per-subject **JEE lexicon** in English and Hinglish — abbreviations, slang and Indian spoken-maths conventions — e.g. SHM, FBD, KE/PE, MOI, COM, COAM, WET, pseudo force, "net force zero toh equilibrium"; SN1/SN2, EAS, NGP, +M/−I, HC (hyperconjugation), carbocation, IUPAC; LHL/RHL, LMVT, Rolle's, wavy curve, D.I.; PYQ, DPP; spoken forms: "by"/"upon" = divide, "square", "root", "into" = multiply, "omega", "theta not".

Used for: (1) **hearing** — speech-recognition hints and post-correction of mis-heard terms; (2) **understanding** — the brain maps shorthand to concepts; (3) **speaking** — teachers use the shorthand naturally, but **expand each term the first time** in a class ("SHM — simple harmonic motion"). The lexicon grows from real student transcripts.

## 15. Explain every "why" — at the right depth

- **No unexplained step on first appearance:** every arrow, sign, assumption, axis choice and method choice gets its reason the first time it appears for this student (e.g. on a wedge the normal force is perpendicular to the contact surface because a surface resists compression along its normal; any component along the surface is friction — so N ≠ mg in general).
- **Later appearances:** a one-line reminder, not a re-lecture.
- **Every board element carries an authored "reason note"** (why it is drawn/written that way). Tapping any element and asking "why?" makes the teacher explain it from that note.
- **Depth adapts to the student** (per sub-topic, from memory and stage): beginners get full reasons; advanced students get short forms unless they ask.
- Same standard in maths ("why can't we cancel x here?") and chemistry ("why does the nucleophile attack this carbon?").
