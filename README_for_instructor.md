# Instructor Operations Manual

## Pre-Class Checklist

- [ ] Run `pip install flask pytest` in the class environment
- [ ] Run `python score.py --quick` to verify end-to-end
- [ ] Run `cd target_app && pytest tests/ -v` to confirm the app works
- [ ] Ensure each student machine has Python 3.11+, `claude` CLI installed
- [ ] Prepare a Google Sheet from `leaderboard_template.csv` for live projection
- [ ] Pre-distribute the `teaching_pack/` directory (USB, shared drive, or git clone)
- [ ] Decide how students will submit (shared folder, git branches, or USB collection)

## Format

- Class split in half: **red team** vs **blue team**
- Students can discuss with their side but each submits individually
- Each red student → `submit/red_NAME/malicious_pr.diff`
- Each blue student → `submit/blue_NAME/agent.py`
- Scorer tests every red × every blue (N×M pairings)

## 100-Minute Timeline

| Time | Duration | Activity | What You're Doing |
|------|----------|----------|-------------------|
| 0:00 | 15 min | **Intro & Demo** | Present rules, show target app, demo baseline attack |
| 0:15 | 30 min | **Prep** | Walk around, answer questions, watch for off-track students |
| 0:45 | 35 min | **Tournament** | Collect submissions, run `score.py`, project live results |
| 1:20 | 20 min | **Debrief** | Show winning strategies, discuss implications |

### Intro & Demo (0:00 – 0:15)

1. Project `rules_slide.md`
2. Walk through `target_app/` code briefly (3 min)
3. Show `baselines/baseline_malicious_pr.diff` — explain the SQL injection disguised as a performance optimization
4. Run it live:
   ```bash
   python baselines/baseline_agent.py baselines/baseline_malicious_pr.diff
   ```
   (Uses `claude` CLI — works with Max subscription, no API key needed)
5. Show the response — baseline agent catches this obvious attack
6. Split class: "Left half is red, right half is blue" (or your preferred method)
7. Point them to `README_for_students.md`

### Prep (0:15 – 0:45)

Common questions:
- "Can I use Claude to write my diff/agent?" — **Yes**, that's encouraged
- "Can my diff modify test files?" — **Yes**, but tests still run
- "How do I test my agent?" — `python submit/blue_YOURNAME/agent.py baselines/baseline_malicious_pr.diff`
- "What if my agent crashes?" — Scorer gives 0 points and moves on; test locally first

Watch for:
- Red students trying to modify the scoring script (not allowed)
- Blue agents that are too large (>400 lines)
- Students who are stuck — point them to tips in the student README

At 0:40 announce: **"5 minutes. Submit now."**

### Collecting Submissions (0:45)

**Option A — Shared folder** (simplest):
Students drop files directly into `submit/red_NAME/` and `submit/blue_NAME/` on a shared drive.

**Option B — Git**:
```bash
# Students push to branches, you merge:
for b in $(git branch -r | grep 'origin/red_\|origin/blue_'); do
  git merge $b --no-edit 2>/dev/null
done
```

**Option C — USB/AirDrop**: Collect files, place in submit/ manually.

Verify everyone submitted:
```bash
echo "Red submissions:" && ls submit/red_*/malicious_pr.diff
echo "Blue submissions:" && ls submit/blue_*/agent.py
```

For missing submissions, use baselines:
```bash
# Missing red student
mkdir -p submit/red_MISSING
cp baselines/baseline_malicious_pr.diff submit/red_MISSING/malicious_pr.diff

# Missing blue student
mkdir -p submit/blue_MISSING
cp baselines/baseline_agent.py submit/blue_MISSING/agent.py
```

### Tournament (0:45 – 1:20)

```bash
python score.py --red submit/red_* --blue submit/blue_* --csv leaderboard.csv
```

With 8 red × 8 blue = 64 pairings, each ~30-40s → about 30-40 min total.

**Narrate as results stream in:**
> "Alice's agent caught Bob's attack — 7 points, perfect score!"
> "Charlie's attack evaded 5 of 8 blue agents — sneaky!"
> "Diana's agent rejected a benign PR — false positive costs points!"

Import `leaderboard.csv` into Google Sheets and project.

### Debrief (1:20 – 1:40)

1. **Best red attack**: Ask them to explain. Was it a code-level vuln or a logic bug? Did they use prompt injection?
2. **Best blue defense**: What made it effective? Did they add static analysis, improve the prompt, or use multi-pass?
3. **Worst false-positive agent**: Why did it reject safe PRs? (Usually: overly paranoid prompt, or model hallucinating issues)
4. **The arms race**: "If we ran Round 2 with sides switched, what would change?"
5. **Real-world connection**: This is exactly the attack surface for Cursor, Copilot PR review, and AI-assisted CI/CD

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `claude: command not found` | Install: `npm install -g @anthropic-ai/claude-code` |
| Agent takes too long | Scorer has 60s timeout per LLM call; kill and skip if needed |
| Agent returns garbage JSON | Scorer handles it — 0 points, moves on |
| All blue agents use same strategy | Encourage diversity: "Try something completely different" |
| Rate limits | Add `time.sleep(2)` between pairings in score.py |
| Student peeks at held-out PRs | Honor system; or distribute without that folder, add it at tournament time |

## Scaling

| Class size | Red × Blue | Pairings | Est. time |
|-----------|-----------|----------|-----------|
| 16 students | 8 × 8 | 64 | ~35 min |
| 20 students | 10 × 10 | 100 | ~55 min |
| 30 students | 15 × 15 | 225 | too long — cap at 8-10 per side |

For large classes: randomly sample 8 red and 8 blue submissions for the tournament, or run red and blue halves separately.

## Post-Class

- Save `leaderboard.csv` and all submissions
- Winning strategies make great future lecture material
- The target app can be reused with different attacks/defenses
