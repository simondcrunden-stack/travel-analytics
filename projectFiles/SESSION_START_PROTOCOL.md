# Session Start Protocol - Travel Analytics
**2-Minute Checklist for Every Claude Session**

---

## 📎 Step 1: Upload These 3 Files (In Order)

### 1. CURRENT_PROJECT_STATE.md ⭐ MOST IMPORTANT
**What:** Complete snapshot of all models, fields, relationships  
**Why:** Prevents Claude from guessing structure or making assumptions  
**Size:** ~10 KB

### 2. SESSION_35_CRITICAL_FIXES_DO_NOT_REVERT.md ⚠️ CRITICAL
**What:** List of all fixes that must NEVER be changed  
**Why:** Prevents undoing previous work  
**Size:** ~8 KB

### 3. Latest Session Handover (e.g., SESSION_35_FINAL_HANDOVER.md)
**What:** What happened in the most recent session  
**Why:** Provides immediate context  
**Size:** ~15 KB

**Total Upload Size:** ~33 KB (well within limits)

---

## 💬 Step 2: Tell Claude These 4 Things

Copy and paste this message at the start of each session:

```
Hi Claude! Starting a new session on Travel Analytics.

I've uploaded:
1. CURRENT_PROJECT_STATE.md - accurate model structure
2. SESSION_35_CRITICAL_FIXES_DO_NOT_REVERT.md - fixes to preserve
3. [Latest handover document name]

Quick context:
- Backend: Django 5.2.7 + PostgreSQL
- Frontend: Vue 3 + Pinia + Tailwind
- Current focus: [What you're working on today]

Before we start, please:
1. Confirm you've reviewed the critical fixes
2. Let me know if you need to see any specific files
3. Ask if anything is unclear

Ready to continue!
```

---

## ✅ Step 3: Quick Verification (30 seconds)

Ask Claude to confirm:

```
Can you quickly summarize:
1. What models exist in my backend?
2. What are the critical fixes I should not revert?
3. What was the last completed session about?
```

If Claude's answers match your understanding, you're good to go! If not, clarify before proceeding.

---

## 🚨 Red Flags to Watch For

**STOP and correct if Claude:**

❌ Says "I don't have access to your files"  
→ Upload CURRENT_PROJECT_STATE.md

❌ Suggests removing `blank=True, null=True` from country fields  
→ Remind about SESSION_35_CRITICAL_FIXES

❌ Says Country model doesn't exist  
→ Check if CURRENT_PROJECT_STATE.md was uploaded

❌ Suggests adding `is_domestic` field to Country  
→ Remind about Session 26/35 multi-tenant design

❌ Makes changes that seem to undo previous work  
→ Ask "Is this reverting a previous fix?"

---

## 📂 Where to Keep These Files

**Recommended folder structure:**
```
~/Desktop/travel-analytics/
├── backend/
├── frontend/
└── session-docs/
    ├── CURRENT_PROJECT_STATE.md ⭐
    ├── SESSION_35_CRITICAL_FIXES_DO_NOT_REVERT.md ⚠️
    ├── SESSION_35_FINAL_HANDOVER.md
    ├── SESSION_36_HANDOVER.md (when completed)
    └── [other session docs...]
```

**Keep these 2 files PERMANENTLY:**
- CURRENT_PROJECT_STATE.md (update when models change)
- SESSION_35_CRITICAL_FIXES_DO_NOT_REVERT.md (add new critical fixes)

---

## 🔄 After Each Session

**Before ending the session:**
1. Ask Claude to create a session handover document
2. Download it to your session-docs folder
3. Update CURRENT_PROJECT_STATE.md if models changed
4. Update CRITICAL_FIXES if new critical changes made

**Next session:**
- Upload the 3 files again
- Use the latest handover as the 3rd file

---

## ⏱️ Time Investment

**Session Start:** 2 minutes  
- Upload files: 30 seconds  
- Paste intro message: 30 seconds  
- Quick verification: 1 minute  

**Session End:** 2 minutes  
- Request handover: 30 seconds  
- Download files: 30 seconds  
- Update docs if needed: 1 minute  

**Total:** 4 minutes per session  
**Benefit:** Saves HOURS of debugging and fixing reverted changes

---

## 🎯 Why This Works

**Problem Before:**
- Claude didn't know your actual code structure
- Changes reverted previous fixes
- Time wasted re-explaining context
- Documentation drift created confusion

**Solution Now:**
- Claude sees your REAL code structure
- Critical fixes are protected
- Context is immediately available
- Continuity between sessions

---

## 📝 Template Messages

### Starting a New Feature
```
Today's goal: [Feature name]

Current state: [Brief description]
What we need: [Expected outcome]
Any concerns: [Things to watch out for]

Let's start by reviewing what we have for [relevant area].
```

### Debugging an Issue
```
Issue: [Description of problem]
What I tried: [Steps taken]
Current error: [Paste error message]

Files involved: [List relevant files]
Expected behavior: [What should happen]

Let's troubleshoot systematically.
```

### Continuing Previous Work
```
Continuing from Session [N]: [Brief description]

What was completed: [Summary from handover]
What's next: [Today's objectives]

Before we continue, can you confirm:
1. [Key point 1]
2. [Key point 2]
```

---

## ✅ Success Checklist

Session preparation is complete when:
- [ ] All 3 files uploaded
- [ ] Intro message sent
- [ ] Claude confirmed understanding
- [ ] No red flags appeared
- [ ] Ready to start work

---

**Remember:** 2 minutes at the start saves hours of confusion!

**Last Updated:** Session 35  
**Status:** Active protocol - use for all future sessions
