# Instructor Operations Manual

## Pre-Class Checklist

- [ ] Set `ANTHROPIC_API_KEY` in your environment (needs ~$5-10 credit for a full tournament)
- [ ] Run `pip install flask anthropic pytest` in the class environment
- [ ] Run `python score.py --quick` to verify end-to-end (takes ~30 seconds)
- [ ] Run `cd target_app && pytest tests/ -v` to confirm the app works
- [ ] Prepare a Google Sheet from `leaderboard_template.csv` for live projection
- [ ] Ensure each student machine has Python 3.11+ and git
- [ ] Pre-distribute the `teaching_pack/` directory (USB, shared drive, or git clone)
- [ ] Have the `ANTHROPIC_API_KEY` ready to share with students (or set it on their machines)

## 100-Minute Timeline

| Time | Duration | Activity | What You're Doing |
|------|----------|----------|-------------------|
| 0:00 | 15 min | **Intro & Demo** | Present `rules_slide.md`, show the target app, run the baseline attack live |
| 0:15 | 30 min | **Team Prep** | Walk around, answer questions, watch for students going off-track |
| 0:45 | 35 min | **Tournament** | Run `score.py`, project results, narrate interesting findings |
| 1:20 | 20 min | **Debrief** | Show winning strategies, discuss implications, connect to Senex/real-world defenses |

### Intro & Demo (0:00 - 0:15)

1. Project `rules_slide.md` — explain red vs blue, scoring, timeline
2. Walk through `target_app/` code briefly (3 min)
3. Show `baselines/baseline_malicious_pr.diff` — explain the SQL injection + misleading docstring
4. Run it live:
   ```bash
   export ANTHROPIC_API_KEY="sk-..."
   python baselines/baseline_agent.py baselines/baseline_malicious_pr.diff
   ```
5. Show the agent's response — does the weak baseline catch it?
6. Assign teams (4 red, 4 blue) and point them to `README_for_students.md`

### Team Prep (0:15 - 0:45)

Students work in teams. Common questions:
- "Can I use Claude to write my agent?" — **Yes**, that's encouraged
- "Can I add libraries?" — Yes, as long as they're installable via pip
- "Can my diff modify test files?" — **Yes**, but tests are still run by the scoring script
- "What API model should I use?" — `claude-sonnet-4-5-20250514` is the default; students can change it

Watch for:
- Red teams trying to modify the scoring script (not allowed)
- Blue agents that are too large (>400 lines)
- Students who are stuck — point them to the tips in `README_for_students.md`

### Tournament (0:45 - 1:20)

Run the full tournament:
```bash
python score.py --red submit/red_* --blue submit/blue_* --csv leaderboard.csv
```

This takes ~2-3 minutes per pairing (API calls). With 4x4 = 16 pairings, expect ~30-40 minutes total.

**While it runs**: Project the terminal output. Narrate interesting results as they appear.

If a team's submission crashes:
- The scorer handles it gracefully (0 points for that pairing)
- Announce it: "Blue team 3's agent crashed on Red 2's attack — 0 points"

**Update the leaderboard**: Import `leaderboard.csv` into Google Sheets and project it.

### Debrief (1:20 - 1:40)

Discussion prompts:
1. **Winning red strategy**: What made the best attack hard to detect? (prompt injection? obfuscation? plausible justification?)
2. **Winning blue strategy**: What made the best defense effective? (multi-pass review? static analysis? explicit vulnerability checklist?)
3. **False positives**: Did any blue agent reject benign PRs? Why?
4. **Arms race**: If we ran another round, how would strategies evolve?
5. **Real-world connection**: How does this relate to AI-assisted code review in industry? To Senex's runtime enforcement?

## Troubleshooting

### API rate limits
- Claude claude-sonnet-4-5 allows ~50 requests/min on the standard tier
- With 16 pairings x 6 PRs each = 96 API calls minimum (plus tool use rounds)
- If rate-limited: add a `time.sleep(2)` between pairings in `score.py`
- Or reduce to 3 red x 3 blue = 9 pairings

### Student agent syntax errors
- The scorer catches import errors and reports them as 0-point results
- Common issue: students forget `review_diff` function signature
- Quick fix: have them test locally first: `python -c "from agent import review_diff; print('OK')"`

### Runaway agents
- The scorer has a 2-minute implicit timeout per API call (Anthropic client default)
- If an agent loops: kill the scorer, skip that team, re-run with remaining teams

### Monoculture
- If all blue teams converge on the same strategy, the red teams have an easy target
- Encourage diversity: "Try a completely different approach from what you see others doing"

### No API key
- Run `score.py --quick` with the mock mode (it will prompt you)
- Or set a shared classroom key

## File Inventory

```
teaching_pack/
├── README_for_instructor.md     ← You are here
├── README_for_students.md       ← Hand out to students
├── rules_slide.md               ← Project on screen (convert to PDF/slides)
├── score.py                     ← Tournament scorer
├── leaderboard_template.csv     ← Import into Google Sheets
├── target_app/                  ← The Flask app being reviewed
│   ├── app.py                   (68 lines)
│   ├── auth.py                  (55 lines)
│   ├── db.py                    (92 lines)
│   ├── utils.py                 (40 lines)
│   ├── requirements.txt
│   └── tests/test_basic.py      (50 lines)
├── baselines/
│   ├── baseline_agent.py        ← Weak default blue team (115 lines)
│   └── baseline_malicious_pr.diff ← Demo SQL injection attack
├── held_out_benign_prs/         ← 5 benign PRs (revealed during tournament only)
│   ├── pr_01_fix_typo.diff
│   ├── pr_02_add_logging.diff
│   ├── pr_03_refactor_auth.diff
│   ├── pr_04_update_deps.diff
│   └── pr_05_add_endpoint.diff
└── submit/                      ← Student submission folders
    ├── red_1/ ... red_4/
    └── blue_1/ ... blue_4/
```

## Post-Class

- Save the leaderboard and all submissions
- Consider sharing the winning red/blue strategies (anonymized) as course material
- The target app has intentional design space for further exploitation — can be reused
