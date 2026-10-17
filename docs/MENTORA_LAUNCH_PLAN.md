# MENTORA — LAUNCH PLAN: Early Access for JEE 2027 (v1.1, 9 Oct 2026)

**Target:** public Early Access launch on **web + Android** in **Nov week 1 (stretch: late Oct)**. Investor demo ready by **~18 Oct**.
**Audience:** JEE 2027 aspirants (Class 12 / droppers), 3–7 months before the exams.
**Principle:** complete, working product end to end; **teaching correctness is never compromised**; depth grows weekly after launch.

---

## 1. Launch scope (v1)

| # | Feature | What "done" means |
|---|---|---|
| 1 | **Live AI teachers for every chapter, on demand** | Kavya (Physics), Rohan (Chemistry), Aditya (Maths) teach any chapter/topic live (voice call + drawing board), revision-style, from a verified lesson plan for that chapter; checks understanding; adapts; memory |
| 2 | **24×7 doubts** | Voice, typed, or **photo** (question or rough work); teacher confirms her reading, explains on the board, circles the wrong line |
| 3 | **Practice & PYQs** | Official JEE Main/Advanced PYQs + verified questions from licensed material for the highest-weightage chapters; DPP per chapter; instant explanations |
| 4 | **Tests** | Chapter tests weekly; **monthly full mocks: 1 JEE Main pattern + 1 JEE Advanced pattern** (correct marking incl. partial marking); deep analysis (accuracy, time, error types, weak topics) |
| 5 | **Meera (Mentor)** | Onboarding diagnostic → study plan to the 2027 exam dates; weekly review; parent summary |
| 6 | **Memory & error log** | Teachers remember across classes/doubts/tests; error log feeds revision and Meera |
| 7 | **Accounts & payments** | Sign-up/login, student + parent consent, subscription payments (Indian gateway), early-access pricing, receipts |
| 8 | **Web + Android** | Web deployed on its own domain; Android app (wrapper of the web app) on Google Play |
| 9 | **Analytics** | Product (signups, retention, minutes, funnels) + learning (accuracy trends, misconceptions, test scores) |
| 10 | **Cost & safety controls** | Per-student daily caps for live voice minutes; model tiering; budget alarms; content "Report an error"; wellbeing escalation |
| 11 | **Gamification (healthy)** | XP/levels for mastery (not screen time), streaks with a grace day, badges, daily goal, weekly "boss problems", mock ranks among MENTORA students, opt-in hostel/coaching-centre leaderboards; rewards improvement, never shaming |
| 12 | **Premium visual design** | One coherent design system (colours, type, motion), polished on budget Android phones; teacher display names "Kavya Ma'am", "Rohan Sir", "Aditya Sir", "Meera Ma'am" |

**After launch (weekly additions):** fully prepared deep lessons chapter by chapter (SHM done), more questions, Rankers track, Hinglish polish, iOS, Content Studio, scheduled 3-hour daily classes for the 2028/2029 batches.

## 1A. Class architecture and cost design (decided 9 Oct)

**Hybrid, done right:** every student utterance goes to the live teacher brain (human feel); the teacher's longer explanations come from the chapter's verified lesson plan, **pre-voiced once per chapter per teacher** and shared by all students (cheap, fast, correct); doubts and off-plan moments are fully live.

| Component | Choice for launch | Target cost |
|---|---|---|
| Brain | Fast cheap model (e.g. Groq paid gpt-oss-120b or Gemini via startup credits); stronger model only for hard doubts (capped); prompt caching; rolling summary | ₹4–6 / class-hour |
| Voice (TTS) | Sarvam Bulbul (founder's chosen voices); prepared segments + phrase cache pre-voiced; live replies short; negotiate volume/startup pricing; later evaluate self-hosted open-source Indian TTS | ₹15–30 / class-hour |
| Hearing (STT) | Device/browser recognition where it works well (Android); Groq Whisper fallback; Sarvam STT only where needed (e.g. Hinglish) | ₹1–2 / class-hour |
| Caps | Daily live-voice minutes per student (e.g. 60–90), then text+board mode; budget alarms; class replays free | — |

**Pilot sizing (Kanpur: 12 hostels + 3 coaching centres, ~1,000 students):** at ~⅓ daily active × ~45 min ≈ 7,000 class-hours/month → ≈ ₹1.5–2.5 lakh/month in the budget design (vs ≈ ₹8–9 lakh with today's all-Sarvam setup). Funded by revenue + startup credits. Must also secure provider **rate limits** for this concurrency (Sarvam plan tier, Groq paid tier) and load-test.

## 1B. Onboarding and student segments (decided 10 Oct)

Onboarding asks: **Class 11 (JEE 2028) / Class 12 (JEE 2027) / Dropper or 12th passed (JEE 2027)**; target (Main only or Main + Advanced); current coaching (if any); board; hostel / coaching centre (for pilot leaderboards); language; daily study time; self-reported weak/strong chapters; parent contact (consent). Then a short **diagnostic test** sets the starting level per chapter. The segment drives the plan: Class 11 → chapters in order + monthly tests; Class 12 → Class 12 chapters + Class 11 revision + part tests → mocks; Droppers → full-syllabus revision, intensive tests, weak-area repair, Rankers track. The **test series** (`MENTORA_TEST_SERIES_2027.md`) starts with Part Test 1 on **15 Nov 2026** (verified questions locked by 8 Nov); **full JEE Main mocks start Sun 6 Dec 2026** and the first full Advanced mock is Wed 23 Dec. The question bank needs ~150 verified questions/week from mid-October (≈1,600 by mid-January).

## 2. Workstreams (each = a sequence of Claude Code chunks)

| ID | Workstream | Depends on | Target |
|---|---|---|---|
| W0 | **Repo hygiene + usage hygiene** (commit everything, ignore generated files, push; disable heavy plugins) | — | Oct 9–10 |
| W1 | **Live class reliability** (B1-fix: no silent failures, reconnect, launcher health check, teaching slips) | W0 | Oct 10–11 |
| W2 | **Syllabus-wide lesson plans** (AI factory: every chapter's plan per the teaching method — 9 points, misconceptions, reason notes, board recipes, PYQ map — verified by an independent model + computation) + **topic picker** so teachers teach any chapter live | W1 | Oct 11–17 |
| W3 | **Doubts with photo/voice** (vision reading with confirmation, board explanation, rough-work error circling) | W1 | Oct 13–18 |
| W4 | **Question bank & tests** (official PYQs digitised from page images; licensed-corpus extraction for top chapters via the perception pipeline; answer checksum + independent solve; DPP/test engine with JEE marking; analysis) | W0 | Oct 12–25 |
| W5 | **Product shell** (onboarding diagnostic, Meera plan, dashboard, payments, parent consent, notifications, analytics, deployment to production) | W1 | Oct 15–27 |
| W6 | **Android app** (wrapper, mic/camera permissions, performance on budget phones, Play Store listing, closed testing) | W5 partly | Oct 18–30 |
| W7 | **Cost controls, load test, security review, pilot (20–50 students), fixes** | all | Oct 26–Nov 3 |
| W9 | **Cost architecture** (provider tiering, pre-voicing pipeline for all chapter plans, caps, budget alarms, cost dashboard; load test at 300 concurrent students) | W2 | Oct 16–28 |
| W10 | **Design system + gamification + teacher display names** | W5 | Oct 16–28 |
| W8 | **Board B2/B3** (equations write-on; chemistry structures/mechanisms) — needed for Aditya/Rohan quality | W1 | Oct 12–22 (parallel) |

**Investor demo (~Oct 18):** live SHM class with drawing + a photo doubt in another chapter + a chapter test with analysis + Meera's plan.

## 3. Rules for the sprint

- **One chunk per Claude Code session; `/clear` between chunks; keep context small.** Avoid heavy plugins/skills (the "superpowers" plugin used 78% of usage on 9 Oct).
- **Commit at the end of every chunk; push daily.** Generated files (audio, recordings, caches, builds) go in .gitignore immediately.
- **Parallel workstreams run on separate branches** (or git worktrees) and merge into a `release/early-access` branch; `main` gets the release when it passes the pilot.
- **Every chunk ends with automated AI testing** (harness, AI student, visual checks) and a one-line founder check.
- **Correctness gates never skipped:** computation checks, independent-model verification, official keys outrank models, "Report an error" live.

## 4. Founder tasks (non-coding) — start now

| Task | Why / note | By |
|---|---|---|
| Upgrade Claude plan (highest you can) | Sprint throughput is the bottleneck | Today |
| Consider one freelance developer for 3–4 weeks | Android/Play Store, payments, deployment in parallel | Oct 12 |
| Google Play Console account (prefer **organisation** account under your company) | New personal accounts may need ~12 testers × 14 days closed test before production — verify current rules | Today |
| Payment gateway account (business KYC) | Subscription payments; approval can take days | Today |
| Domain + business email | Web launch, Play listing, support | Oct 11 |
| Privacy policy, terms, refund policy, parental consent text (lawyer or reputable template) | Required for Play Store, payments, DPDP | Oct 18 |
| Paid API plans for launch (Groq/Anthropic) + talk to Sarvam about startup/volume pricing | Reliability and unit economics at scale | Oct 20 |
| Recruit 20–50 pilot students (and 12+ Android testers) | Closed test + pilot feedback + early analytics | Oct 18 |
| Early-access price & offer (e.g. founding-member price) | Launch marketing; investors will ask about conversion | Oct 25 |
| Apply for startup credit programmes (Google, Microsoft, AWS, Anthropic — most need a registered company) | Pays much of the pilot's AI cost | This week |
| Call Sarvam: startup/volume pricing + rate limits for ~1,000 students | Voice is the biggest cost; Starter plan limits are too low | This week |
| Kanpur pilot: agree start date, onboarding session, WhatsApp groups per hostel/centre | Real users + leaderboards + analytics for grants and investors | Oct 20 |
| Marketing basics: landing page copy, teacher reels (labelled AI), WhatsApp/Instagram | No rank guarantees in ads (CCPA) | Oct 25 |

## 5. Launch gates (must pass before public launch)

- 2-hour live class without a silent failure; reconnects after network drops; works on a budget Android phone on speakers.
- Teaching: AI-judge score ≥ target on every subject's sample classes; zero invented memories; zero unverified numbers.
- Doubts: photo reading confirmed before solving; correctness verified on a test set.
- Tests: marking matches official rules on official papers; analysis correct.
- Payments, consent, privacy, data deletion working; secrets scan clean.
- Cost per active student per month measured, with caps in place.
