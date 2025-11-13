# 🖥️ TMux Debugging Protocol for AI Collaboration

## Core Principle
**Never duplicate pane output in main interface** - we both see the tmux panes

## Pane Allocation
- **Pane 0 (cli)**: Main rovodev interface 
- **Pane 1 (monitor)**: Unit testing, component validation
- **Pane 2 (debug)**: Integration testing, debugging output
- **Interface**: Clean summaries only (✅/❌ status)

## MCP Integration
When MCP servers are loaded, AI will automatically know to:
- Use tmux panes for detailed work
- Follow code-guidance MCP principles
- Validate components systematically
- Report clean status to interface

## Component Debugging Pattern
1. **Pane 1**: Unit test individual components
2. **Pane 2**: Integration test full workflows  
3. **Interface**: Summary status only

This enables efficient collaboration without token waste on duplicate output.