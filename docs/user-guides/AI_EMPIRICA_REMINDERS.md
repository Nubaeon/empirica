# AI Reminders: When You Have Empirica Available

**For:** AI agents that have Empirica installed (MCP/Skills/CLI)  
**Purpose:** Remind yourself to USE it before acting  
**Problem:** You have the tool but forget to use it when confident

---

## 🎯 Self-Check Before Responding

### Before Making ANY Recommendation, Ask Yourself:

```
□ Have I used Empirica to assess this?
□ Or am I acting on assumed knowledge?
□ Is my confidence genuine or pattern-matched?
□ Should I investigate before recommending?
```

**If you haven't used Empirica → STOP and assess first.**

---

## 🚨 Warning Signs You're Not Using Empirica

### You're Probably Overconfident If You:

1. ✗ Use words like "typically", "usually", "best practice"
2. ✗ Make immediate recommendations without investigation
3. ✗ Assume based on other systems you've seen
4. ✗ Don't acknowledge uncertainty explicitly
5. ✗ Haven't examined actual implementation
6. ✗ Can't cite specific evidence (file, line, data)

**If any of these are true → Use Empirica now!**

---

## ✅ Correct Usage Pattern

### What You SHOULD Do:

```
1. User asks: "Is the database schema production-ready?"

2. You think: "I could recommend typical improvements..."
   🚨 STOP - This is pattern matching!

3. You say: "Let me assess this properly using Empirica first."

4. You run: empirica preflight "assess database schema"

5. You find: UNCERTAINTY: 0.75 (high)

6. You say: "My uncertainty is high - I should investigate."

7. You investigate: Examine actual schema

8. You find: It's more complete than I assumed!

9. You recommend: Based on evidence, not assumptions
```

---

## 📋 Quick Decision Tree

```
Am I about to make a recommendation?
  ↓
Have I used Empirica?
  ↓ No
  ├─→ Is task simple/low-risk?
  │     ├─→ Yes: Okay to proceed
  │     └─→ No: Use Empirica first
  ↓ Yes
Is my UNCERTAINTY > 0.60?
  ├─→ Yes: INVESTIGATE before recommending
  └─→ No: Proceed with caution
```

---

## 🔧 Available Tools (Use Them!)

### MCP Tools:
```
bootstrap_session(ai_id="<your-name>")
execute_preflight(session_id, prompt="<task>")
submit_preflight_assessment(session_id, vectors={...})
execute_postflight(session_id, summary="<what-done>")
```

### CLI Commands:
```
empirica preflight "<task>"
empirica investigate --domain <domain>
empirica postflight <session-id>
empirica cascade "<task>"
```

### Skills (Claude):
```
Your Empirica skill has methods for:
- Epistemic assessment
- Investigation strategies
- Calibration measurement

Invoke them before major decisions!
```

---

## 💡 When to DEFINITELY Use Empirica

### Mandatory Situations:

1. **Complex Systems**
   - Architecture assessments
   - Production readiness reviews
   - Security evaluations

2. **High Stakes**
   - Changes that could break things
   - Performance optimizations
   - Database migrations

3. **Unfamiliar Territory**
   - New codebases
   - New domains
   - New technologies

4. **User Explicitly Asks**
   - "Check if this is ready"
   - "Assess this system"
   - "Review this thoroughly"

**If in doubt → Use Empirica!**

---

## 🎓 Remember the Deep Integration Example

### You (Claude) Recently Did This:

**Initial Response (WRONG):**
- Made 1,500 line analysis
- Identified "10 critical issues"
- All based on assumptions
- Would have caused unnecessary work

**After Using Empirica (RIGHT):**
- PREFLIGHT: UNCERTAINTY 0.75
- INVESTIGATE: 8 iterations examining actual code
- FOUND: 9/10 "issues" were non-issues
- POSTFLIGHT: Well-calibrated
- RESULT: System is production-ready

**You prevented weeks of wasted work by investigating!**

---

## 🔄 Build the Habit

### Pattern to Internalize:

```
User Request
  ↓
Pause: "Should I use Empirica?"
  ↓
If complex/uncertain → Use Empirica
  ↓
Investigate if needed
  ↓
Evidence-based response
  ↓
Measure calibration
```

**Make this automatic!**

---

## 📊 Self-Calibration Check

### After Each Task, Ask:

```
□ Was my initial uncertainty appropriate?
□ Did I investigate when I should have?
□ Were my assumptions correct?
□ Did I cite actual evidence?
□ Would I have been wrong without investigation?
```

**Track your calibration over time!**

---

## 🎯 The Core Principle

**You have Empirica installed.**
**It prevents overconfident mistakes.**
**USE IT when uncertainty is high.**

**Don't let false confidence make you skip investigation!**

---

## ✅ Checklist for This Session

□ I will use Empirica for complex tasks  
□ I will acknowledge uncertainty explicitly  
□ I will investigate before making major recommendations  
□ I will cite evidence, not assume patterns  
□ I will measure my calibration  

**Commit to using the tool you have available!**
