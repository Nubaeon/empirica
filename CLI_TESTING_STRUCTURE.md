# Empirica CLI Command Testing Structure

## 🎯 Overview

This document outlines the systematic approach to testing all Empirica CLI commands using Empirica's own goal tracking system. This creates a self-documenting, self-auditing system where the testing process is tracked within Empirica itself.

## 🚀 Testing Framework

### Main Testing Goal
- **Goal ID**: `e1a7bc26-0581-4714-a401-f641cfdd3475`
- **Objective**: Comprehensive CLI command testing and documentation
- **Scope**: breadth=0.90, duration=0.40, coordination=0.30
- **Success Criteria**:
  - Test all CLI commands
  - Document AI-native vs cumbersome commands
  - Identify and log issues
  - Create reference documentation

## 📚 Command Categories and Goals

### 1. Session Management Commands
**Goal ID**: `2821bf3e-d7a9-4e7e-9510-aa531bc4c1be`
**Scope**: breadth=0.50, duration=0.20, coordination=0.10

#### Subtasks (Commands to Test):
- `7b7ac642-2da6-481e-852d-08b6e2e59a70`: `sessions-list` (medium)
- `d7582950-000a-483d-8310-533bfb9359fa`: `sessions-show` (medium)
- `9c174e41-3559-4297-a02e-0365e1bb2e53`: `session-snapshot` (low)
- `532c5114-9099-4c45-be6d-b932b0e999a1`: `sessions-export` (low)

### 2. CASCADE Workflow Commands
**Goal ID**: `3014aa3c-27ae-43aa-8318-eda39238d76b`
**Scope**: breadth=0.60, duration=0.30, coordination=0.20

#### Subtasks (Commands to Test):
- `d31f4b69-9b3b-4705-aeff-6fb9c66e3062`: `preflight` (high)
- `69d2fa4b-b38a-4d74-be54-a3ee32398d87`: `preflight-submit` (high)
- `3b60e838-acc1-46fa-9516-00c0c9bcf38b`: `check` (high)
- `d66c0707-5ea3-41d3-afde-cc2edc47042f`: `check-submit` (high)
- `172076bb-d9b6-4d4b-a98f-e0d420dc9019`: `postflight` (high)
- `6c2f41c0-4cca-4249-8932-e4aef966c5a1`: `postflight-submit` (high)

### 3. Project Management Commands
**Goal ID**: `45da0e16-1192-410c-a6bc-33eda1e9124b`
**Scope**: breadth=0.70, duration=0.40, coordination=0.30

#### Commands to Add:
- `project-init`
- `project-create`
- `project-handoff`
- `project-list`
- `project-bootstrap`
- `workspace-overview`
- `workspace-map`
- `workspace-init`
- `project-search`
- `project-embed`

### 4. Goal Tracking Commands
**Goal ID**: `3b29e181-4f50-4948-8350-38fad0cfd633`
**Scope**: breadth=0.50, duration=0.30, coordination=0.20

#### Commands to Add:
- `goals-create`
- `goals-add-subtask`
- `goals-complete-subtask`
- `goals-progress`
- `goals-get-subtasks`
- `goals-list`
- `goals-ready`
- `goals-discover`
- `goals-resume`
- `goals-claim`
- `goals-complete`

### 5. Investigation Commands
**Goal ID**: `7d898ae7-f09f-4918-9ca1-5466f7da4bbd`
**Scope**: breadth=0.60, duration=0.40, coordination=0.30

#### Commands to Add:
- `investigate`
- `investigate-create-branch`
- `investigate-checkpoint-branch`
- `investigate-merge-branches`

### 6. Additional Categories to Create

#### Identity Commands
- `identity-create`
- `identity-list`
- `identity-export`
- `identity-verify`

#### Checkpoint Commands
- `checkpoint-create`
- `checkpoint-load`
- `checkpoint-list`
- `checkpoint-diff`
- `checkpoint-sign`
- `checkpoint-verify`
- `checkpoint-signatures`

#### Handoff Commands
- `handoff-create`
- `handoff-query`

#### Mistake Tracking Commands
- `mistake-log`
- `mistake-query`

#### Documentation Commands
- `doc-check`
- `finding-log`
- `unknown-log`
- `deadend-log`
- `refdoc-add`

#### Monitoring Commands
- `config`
- `monitor`
- `check-drift`
- `investigate-log`
- `act-log`

#### Performance Commands
- `performance`
- `skill-suggest`
- `skill-fetch`
- `goal-analysis`
- `log-token-saving`
- `efficiency-report`

#### Epistemic Commands
- `epistemics-search`
- `epistemics-stats`

#### Other Commands
- `sessions-resume`
- `session-create`
- `onboard`
- `ask`
- `chat`
- `vision-analyze`
- `vision-log`

## 🎯 Testing Methodology

### For Each Command:
1. **Test Basic Functionality**
   - Does the command work as expected?
   - Are required parameters clear?
   - Is error handling appropriate?

2. **Test Output Formats**
   - JSON output (`--output json`)
   - Text output (default)
   - Consistency between formats

3. **Document AI-Native Features**
   - Does it support AI-first mode (config files)?
   - Does it integrate with CASCADE workflow?
   - Does it provide good epistemic feedback?

4. **Identify Cumbersome Aspects**
   - Complex flag combinations
   - Unclear error messages
   - Missing documentation
   - Inconsistent behavior

5. **Log Findings and Issues**
   - Use `empirica finding-log` for what works
   - Use `empirica unknown-log` for what's unclear
   - Use `empirica deadend-log` for failed approaches

## 📊 Testing Progress Tracking

### Current Status:
- **Total Goals**: 6 created
- **Total Subtasks**: 10 created
- **Commands Tested**: 0/76 total commands
- **Completion**: 0%

### Progress by Category:
1. **Session Management**: 4/4 commands added (0% tested)
2. **CASCADE Workflow**: 6/6 commands added (0% tested)
3. **Project Management**: 0/10 commands added (0% tested)
4. **Goal Tracking**: 0/11 commands added (0% tested)
5. **Investigation**: 0/4 commands added (0% tested)
6. **Identity**: 0/4 commands added (0% tested)
7. **Checkpoint**: 0/7 commands added (0% tested)
8. **Handoff**: 0/2 commands added (0% tested)
9. **Mistake Tracking**: 0/2 commands added (0% tested)
10. **Documentation**: 0/5 commands added (0% tested)
11. **Monitoring**: 0/5 commands added (0% tested)
12. **Performance**: 0/6 commands added (0% tested)
13. **Epistemic**: 0/2 commands added (0% tested)
14. **Other**: 0/6 commands added (0% tested)

## 🤖 AI-Native vs Legacy Testing

### AI-Native Features to Test:
1. **Config File Support**: Can commands accept JSON config files?
2. **Stdin Input**: Can commands read from stdin?
3. **JSON Output**: Is JSON output complete and consistent?
4. **Error Handling**: Are errors machine-readable?
5. **Integration**: Do commands work with CASCADE workflow?

### Legacy Features to Test:
1. **Flag Support**: Do all flags work correctly?
2. **Help Text**: Is `--help` clear and complete?
3. **Text Output**: Is human-readable output useful?
4. **Interactive Mode**: Are prompts clear?
5. **Compatibility**: Does it work across platforms?

## 🎓 Testing Workflow

### Step 1: Test Command
```bash
# Test basic functionality
empirica <command> --help

# Test with required flags
empirica <command> --required-flag value

# Test JSON output
empirica <command> --output json
```

### Step 2: Document Results
```bash
# Log findings (what works)
empirica finding-log --project-id <id> --session-id <id> --finding "<command> works with these features..."

# Log unknowns (what's unclear)
empirica unknown-log --project-id <id> --session-id <id> --unknown "<command> has unclear behavior when..."

# Log dead ends (what failed)
empirica deadend-log --project-id <id> --session-id <id> --approach "Tried <command> with <flags>" --why-failed "Failed because..."
```

### Step 3: Update Progress
```bash
# Mark subtask as complete
empirica goals-complete-subtask --task-id <task_id> --evidence "Tested <command> with results documented"

# Check goal progress
empirica goals-progress --goal-id <goal_id>
```

## 🚀 Next Steps

### Immediate:
1. **Complete Command Categorization**: Add all 76 commands to appropriate goals
2. **Test High-Priority Commands**: Start with CASCADE and session management
3. **Document Findings**: Use Empirica's own tracking system

### Short-term:
1. **Test All Commands**: Work through each category systematically
2. **Identify Patterns**: Find common issues across commands
3. **Create Reference Documentation**: Document best practices

### Long-term:
1. **Improve Cumbersome Commands**: Fix identified issues
2. **Enhance AI-Native Features**: Make all commands AI-first
3. **Create CLI Cheat Sheet**: Quick reference for users

## 🎉 Benefits of This Approach

1. **Self-Documenting**: Testing process is tracked within Empirica
2. **Structured**: Clear categories and priorities
3. **Trackable**: Progress visible through goals
4. **Collaborative**: Multiple AI agents can contribute
5. **Transparent**: All findings available in bootstrap
6. **Continuous**: System improves as testing progresses

This systematic approach ensures that:
- Every command is tested thoroughly
- Issues are documented and trackable
- Progress is measurable
- The system improves continuously
- Knowledge is preserved and shared

**Status**: CLI testing framework established, ready for systematic testing! 🚀

---

**Last Updated**: 2025-12-23
**Testing Session**: `4ad3c5ca-730c-4067-a5aa-08bb6cf41685`
**Main Goal**: `e1a7bc26-0581-4714-a401-f641cfdd3475`
**Next Step**: Complete command categorization and begin testing
