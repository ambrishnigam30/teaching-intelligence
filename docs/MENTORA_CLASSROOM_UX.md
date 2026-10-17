# MENTORA — CLASSROOM SCREEN v2 (10 Oct 2026)

**Goal:** the student sees the board and the teacher, and nothing else that doesn't help learning right now. The class must feel effortless on a budget Android phone.

## 1. Principles
1. **The board is the class.** It fills at least 85% of the screen on phone and desktop.
2. **Technical details are never shown to students.** Model names, the voice provider, latency, cost, "Connected" and the stats belong in a hidden debug panel (`?debug=1`, for the founder and developers only).
3. **Problems appear only when they matter.** A connection warning shows only when the connection is bad.
4. **The student always knows whether they were heard** (see §4).
5. **Nothing the teacher writes is ever erased.** The board grows; the student can look back at any time.

## 2. Remove or move (from the current screen)

| Now | Change |
|---|---|
| "Voice: Sarvam · Suhani" tag, model name | Move to the debug panel only |
| "Connected" pill | Hide; show a small warning only when the connection is poor or reconnecting |
| Large "KM" teacher tile + large "You" tile | Replace with a **small round teacher portrait at bottom-left**, with a speaking ring. A tiny "AI" badge stays on the portrait (disclosure rule). Tapping the portrait opens her profile card. The "You" tile goes; the mic button shows your level instead |
| "0 min" timer | A slim progress bar at the top showing class phases + time left. It auto-hides after a few seconds and reappears on tap |
| English / Hinglish toggle | Move to the ⋯ menu (it's also set at onboarding) |
| ✋ Raise hand | Remove: speaking, or tapping the mic, interrupts her |
| "Hold to talk" button | Move to the ⋯ menu as **Noisy-room mode**. It switches on automatically when the room check finds noise |
| CC button | Subtitles are on by default; the toggle moves to the ⋯ menu |

## 3. Layout

| Position | What's there |
|---|---|
| **Top (thin)** | Chapter title · phase dots (Warm-up · Concept · Examples · Practice · Wrap-up) · time left. On phone, just the progress line |
| **Top-right** | ⋯ menu: speech speed (0.8–1.2×), subtitles, English/Hinglish, noisy-room mode, transcript, report a problem, how-to, end class. Plus a ⭐ bookmark button always visible |
| **Bottom-left** | Teacher portrait (speaking ring) + **Pause** |
| **Bottom-centre** | One subtitle line: the teacher's current sentence. When the student speaks, a short **"I heard: …"** chip appears here (see §4) |
| **Bottom-right** | ⌨️ keyboard / 📷 photo button, and a **big mic button** with a live level ring |

## 4. Hearing the student (most important)

**Mic states, shown on the button:**
- **Ready:** a soft ring.
- **Hearing you:** the ring moves with your voice.
- **Got it:** the "I heard: …" chip is shown for 2–3 s.
- **She's talking — just speak to interrupt.**

**Rules:**
- **Never drop speech silently.** If voice was detected but no words came back, she says: *"Sorry, I didn't catch that — once more?"*
- **Wait-time nudges pause while the student is speaking** or the mic sees voice. At most one nudge, then she waits.
- **Unclear words get checked, not answered literally.** If a transcript is low-confidence or odd, she asks "Did you mean …?" and offers 2 tap chips.
- **Long answers are allowed.** A student can talk for 30 s or more with natural pauses. Her turn starts after about 1.2 s of silence, and later when the sentence sounds unfinished.
- **Targets:**

  | Measure | Target |
  |---|---|
  | Barge-in (her voice stops after the student starts) | ≤ 400 ms (was 41 s on 10 Oct) |
  | Dropped utterances in the 20-utterance noise test | 0 |

## 5. The board: infinite canvas, with structure
- **The board is one large canvas laid out like notebook pages.** Each class phase or example gets its own section, placed left to right and then on a new row. Nothing is erased.
- **The view follows the teacher's pen automatically,** at a readable zoom (on a phone, text is never smaller than ~14 px).
- **The student can pinch or scroll to zoom and drag to move,** for example to look back. When they have moved away, a **"Follow teacher"** button appears; the board never jumps back on its own.
- **A section strip** (Concept · Example 1 · Practice …) lets the student jump around. The top phase dots work the same way.
- **Gestures:**
  - double-tap: fit the current section;
  - keyboard: + / − / 0;
  - tap any element: "why?" (already built).

## 6. Colour code (the same for all teachers)

| Colour / mark | Meaning |
|---|---|
| Ink (dark) | Given data and normal working |
| Teacher's own pen colour | Her writing and drawings |
| **Blue** | Method, hint, "why" notes |
| **Yellow highlighter + box** | Key result or formula to remember |
| **Red + wavy underline** | Mistake, trap, or final check |
| **Green ✓** | Verified correct step or answer |

Every colour also has a shape, so the code still works for colour-blind students. At most one highlight per step. Every highlighted key result is collected automatically into the chapter's **formula sheet**. Visuals must carry meaning: no decorative charts.

## 7. Save and revisit (in the app only: no downloads at launch)
- **Every class is saved automatically** in "My Classes", with board replay, audio and a searchable transcript, available any time inside the app (web + Android).
- **⭐ Bookmark** a moment by button or by saying "bookmark this". It saves that board section with its time, adds it to "My Bookmarks", and schedules it for revision.
- **My Notes per chapter:** the saved boards, bookmarks, the **formula sheet** (built from highlighted key results), and *your* mistakes and fixes.
- **No download or PDF export at launch, to protect our material from piracy** (e.g. sharing on Telegram groups) and to respect the licensed-content terms. Later we may allow a **personal, watermarked** PDF of a student's own class notes (name + phone on every page), never of test papers or licensed questions.
- **Tests are the main piracy target:**
  - questions are shown one at a time;
  - each student gets different variants;
  - each student's view carries an invisible watermark;
  - the Android app blocks screenshots during tests.

## 7A. Infinite board and class recordings (must stay compatible)
- **A recording is the board's event log** (what was drawn, where, when) plus the audio timeline. The infinite board adds one thing: a **camera** (which part of the board is in view).
- **Board content keeps its board coordinates.** Today's fixed board becomes the first section of the canvas.
- **Old recordings have no camera events,** so replay shows them in the original fixed view, exactly as before.
- **New recordings add "camera" events,** so replay follows the teacher's pen. The viewer can also pan and zoom during replay and tap "Follow teacher" to return.
- **The student's own panning during class is not mixed into the teacher's camera.** It is kept separately for analytics.
- **Gate:** every existing recorded class must replay identically before and after the change. Compare screenshots at fixed timestamps.

## 8. Transcript
- **Off by default during class,** because reading takes attention away from listening and the board. The subtitle line is enough.
- Available from the ⋯ menu.
- Never shows internal lines or stacks of nudges.
- After class, the transcript is part of the class record (searchable, linked to the board replay).

## 9. Acceptance checks (AI-tested)
1. **Screenshots** on phone (360×800) and desktop. Pass: the board fills ≥ 85% of the screen, and no technical text is visible without `?debug=1`.
2. **Hearing tests** pass the §4 targets with fan-noise and TV-speech tracks.
3. **Follow teacher:** pan away → the button appears → tap it → the view returns to the current pen position.
4. **Saving and recordings:**
   - a bookmark shows up in "My Bookmarks";
   - My Notes shows the formula sheet;
   - there is no download button;
   - all old recordings replay identically (7A).
