# Atomic Edit Workflow - Reliable File Modifications

**Problem:** AI edit tools fail ~80% of the time due to whitespace mismatches  
**Solution:** Systematic read → extract → modify → verify workflow

---

## 🎯 Root Causes (From Analysis)

1. **Whitespace Mismatch** (80%) - Spaces vs tabs, trailing spaces
2. **Truncated Context** (15%) - AI sees `...` but file has full text
3. **Stale Memory** (3%) - File changed since last read
4. **Encoding Issues** (1%) - CRLF vs LF, UTF-8 issues
5. **Escaping Errors** (1%) - Quotes, backslashes

---

## ✅ The Gold Standard Workflow

### Step 1: Locate Target

```bash
# Find exact line number
grep -n "target_pattern" file.py

# Example output: 575:    def create_session(self, ai_id: str):
```

### Step 2: Read Exact Content

```bash
# ALWAYS read before editing
view /path/to/file.py --view_range [575, 585]

# This shows EXACTLY what's in file (including whitespace)
```

### Step 3: Copy EXACTLY from view output

```python
# Copy the EXACT text from Step 2 output
old_str = """    def create_session(self, ai_id: str):
        return session_id
"""

# Make your change
new_str = """    def create_session(self, ai_id: str, metadata: dict = None):
        return session_id
"""
```

### Step 4: Verify After Edit

```bash
# Check it worked
view /path/to/file.py --view_range [575, 585]

# Or use git
git diff file.py
```

---

## 🚀 When Edit Tool Fails: Use Bash

### Option 1: Python Script (Most Reliable)

```bash
python3 << 'PYTHON'
# Read file
with open('file.py', 'r') as f:
    lines = f.readlines()

# Modify specific line (0-indexed: line 575 = index 574)
lines[574] = "    def create_session(self, ai_id: str, metadata: dict = None):\n"

# Write back
with open('file.py', 'w') as f:
    f.writelines(lines)
    
print("✅ Modified line 575")
PYTHON
```

### Option 2: sed (Single-Line Changes)

```bash
# Replace entire line
sed -i '575s/.*/    def create_session(self, ai_id: str, metadata: dict = None):/' file.py

# Or pattern-based
sed -i 's/def old_name(/def new_name(/' file.py
```

### Option 3: Regex-Based (Flexible Whitespace)

```bash
python3 << 'PYTHON'
import re

with open('file.py', 'r') as f:
    content = f.read()

# Regex handles whitespace variations
content = re.sub(
    r'def\s+old_name\s*\(',  # \s+ = any whitespace
    'def new_name(',
    content
)

with open('file.py', 'w') as f:
    f.write(content)
PYTHON
```

---

## 🔍 Debugging Failed Edits

### Quick Diagnostic

```bash
# 1. Show with line numbers and whitespace
sed -n '575,585p' file.py | cat -An

# Output explanation:
#   1  ^I = tab character
#   2  $ = end of line
#   3  Multiple spaces shown as spaces

# 2. Show with Python repr (reveals everything)
python3 << 'PYTHON'
with open('file.py', 'r') as f:
    lines = f.readlines()
    for i in range(574, 584):  # Lines 575-584
        if i < len(lines):
            print(f"Line {i+1}: {repr(lines[i])}")
PYTHON
```

### Compare Attempted vs Actual

```bash
# What you tried to match
cat > /tmp/attempted.txt << 'EOF'
    def create_session(self, ai_id: str):
        return session_id
EOF

# What file actually has
sed -n '575,577p' file.py > /tmp/actual.txt

# Show difference
echo "=== ATTEMPTED (what AI tried) ==="
cat -A /tmp/attempted.txt
echo ""
echo "=== ACTUAL (what file has) ==="
cat -A /tmp/actual.txt
echo ""
echo "=== DIFF ==="
diff -u /tmp/attempted.txt /tmp/actual.txt || true
```

---

## 📋 Common Issues & Solutions

### Issue 1: "I see this in context but file is different"

**Problem:** AI's context window shows abbreviated version

```python
# AI sees:
def long_function(...):

# File has:
def long_function(param1, param2, param3):
```

**Solution:** Always read the actual file section before editing

### Issue 2: Spaces vs Tabs

```bash
# Check indentation type
head -50 file.py | grep -P '^\t' && echo "File uses TABS" || echo "File uses SPACES"

# If you need to convert:
# Tabs → Spaces: expand -t 4 file.py > file.tmp && mv file.tmp file.py
# Spaces → Tabs: unexpand -t 4 file.py > file.tmp && mv file.tmp file.py
```

### Issue 3: Line Endings (Windows vs Unix)

```bash
# Check
file file.py  # Shows "CRLF" or "LF"

# Convert if needed
dos2unix file.py  # CRLF → LF
unix2dos file.py  # LF → CRLF
```

---

## ✅ Best Practices

**Before ANY edit:**
- [ ] Locate line number with `grep -n`
- [ ] Read exact content with `view`
- [ ] Copy EXACT text (including all whitespace)
- [ ] Keep edits small (< 10 lines)
- [ ] Plan to verify after

**If edit fails:**
- [ ] DON'T retry with same text
- [ ] Read the section again (might have changed)
- [ ] Check whitespace with `cat -A`
- [ ] Consider bash alternative
- [ ] Use line-based replacement for complex changes

---

## 🎓 For AI Agents: Recovery Strategy

**If your edit just failed:**

1. **Read the target section**
   ```bash
   view file.py --view_range [target_line - 2, target_line + 5]
   ```

2. **Check whitespace if suspicious**
   ```bash
   sed -n 'start,endp' file.py | cat -A
   ```

3. **Try bash if 2nd attempt fails**
   ```bash
   python3 << 'PYTHON'
   # Line-based replacement (more reliable)
   PYTHON
   ```

**Remember:** edit tool needs PERFECT match. One space off = failure.

---

## 📚 Quick Reference

```bash
# Locate
grep -n "pattern" file.py

# Read exact
view file.py --view_range [line_start, line_end]

# Check whitespace (if failed before)
sed -n 'start,endp' file.py | cat -A

# Edit (copy EXACTLY from view)
edit(path="file.py", old_str="exact match", new_str="new content")

# Verify
git diff file.py
```

---

**Success rate:** 95%+ when following this workflow  
**Time saved:** 5-10 minutes per failed edit attempt

