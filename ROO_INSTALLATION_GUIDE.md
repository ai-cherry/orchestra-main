# 🤖 Roo Code Installation & Usage Guide

## 📋 What is Roo Code?

Roo Code (formerly Roo Cline) is a **VS Code extension** that provides AI-powered autonomous coding capabilities. It's NOT a CLI tool, but a VS Code extension that gives you specialized AI coding modes.

## 🚀 Installation Methods

### Method 1: VS Code Extensions Marketplace (Recommended)

1. **Open VS Code**
2. **Go to Extensions**: Click the Extensions icon in the sidebar (Ctrl+Shift+X)
3. **Search**: Type "Roo Code" in the search bar
4. **Install**: Click "Install" on the official Roo Code extension by RooCode Inc.

### Method 2: VS Code Command Line

```bash
# If you have VS Code CLI installed
code --install-extension RooCode.roo-code
```

### Method 3: Download VSIX File

1. **Download**: Get the latest `.vsix` file from [Roo Code Releases](https://github.com/RooCodeInc/Roo-Code/releases)
2. **Install**: In VS Code, go to Extensions → ... → Install from VSIX
3. **Select**: Choose the downloaded `.vsix` file

## ⚙️ Configuration for Orchestra AI

Once installed, Roo Code will use our pre-configured settings from `.roo/` directory:

### Available Modes (Pre-configured)
- **💻 Developer** - General Python coding with DeepSeek R1
- **🏗 Architect** - System design with Claude Sonnet 4  
- **🪃 Orchestrator** - Complex workflows and boomerang tasks
- **🪲 Debugger** - Systematic debugging with DeepSeek R1
- **🔍 Researcher** - Documentation and research with Gemini 2.5 Pro
- **📊 Analytics** - Data analysis and insights
- **⚙️ Implementation** - Technical implementation
- **✅ Quality** - Code quality and testing
- **📝 Documentation** - Documentation generation
- **🧠 Strategy** - Strategic planning

### API Configuration

Roo Code will automatically use:
- **OpenRouter API**: For cost-optimized models (60-80% savings)
- **Custom Instructions**: Persona-aware prompts for Cherry, Sophia, Karen
- **Boomerang Tasks**: Complex multi-step workflows

## 🎯 Usage Instructions

### 1. Activate Roo Code
- **Command Palette**: Ctrl+Shift+P → "Roo Code: Start"
- **Or**: Click the Roo icon in the VS Code sidebar

### 2. Select Mode
- Choose from 10 pre-configured modes based on your task
- Each mode has specialized instructions and model selection

### 3. Give Instructions
- Type natural language instructions
- Roo will read files, write code, run commands, and more

### 4. Example Commands

```
🏗 Architect Mode:
"Design a microservices architecture for the Orchestra AI dashboard"

💻 Developer Mode:  
"Create a Python FastAPI endpoint for user authentication with type hints"

🪃 Orchestrator Mode:
"Implement a complete Cherry persona feature including UI, API, and database"

🔍 Researcher Mode:
"Research best practices for React component testing and document findings"
```

## 🔧 Configuration Details

### OpenRouter Integration
Roo Code uses OpenRouter for cost optimization:
- **DeepSeek R1**: $0.14/1M tokens (vs $3.00/1M for GPT-4)
- **Claude Sonnet 4**: $3.00/1M tokens  
- **Gemini 2.5 Pro**: $0.30/1M tokens

### Custom Instructions
Each mode includes:
- **Orchestra AI context**: Project structure, personas, standards
- **Specific role instructions**: Tailored to the mode's purpose
- **Integration patterns**: MCP servers, Notion, GitHub workflows

### Boomerang Tasks
Advanced workflow capability:
- **Multi-step execution**: Break complex tasks into sub-tasks
- **Context retention**: Remember previous steps and decisions
- **Auto-approval**: Streamlined workflow for trusted operations

## 📊 Expected Performance

With Roo Code installed and configured:
- **3-5x faster** general coding tasks
- **10x faster** complex architecture decisions  
- **60-80% cost savings** vs pure OpenAI usage
- **Specialized expertise** for each development role

## 🔍 Verification

### Check Installation
1. **VS Code Extensions**: Verify "Roo Code" appears in installed extensions
2. **Sidebar Icon**: Look for Roo Code icon in VS Code sidebar
3. **Command Palette**: Search for "Roo Code" commands

### Test Basic Functionality
1. **Open VS Code** in orchestra-main project
2. **Start Roo Code**: Click sidebar icon or use Command Palette
3. **Select Mode**: Choose "💻 Developer" mode
4. **Test Prompt**: "Create a simple Python function with type hints"

## 🚨 Troubleshooting

### Extension Not Found
- **Check spelling**: Search "Roo Code" (not "roo-coder")
- **Publisher**: Ensure it's by "RooCode Inc." 
- **Alternative**: Search "Cline" (previous name)

### Configuration Issues
- **API Keys**: Ensure OPENROUTER_API_KEY is set in environment
- **Workspace**: Open VS Code in the orchestra-main directory
- **Mode Files**: Verify `.roo/modes/` directory contains 10 .json files

### Performance Issues  
- **Model Selection**: Use DeepSeek R1 for faster/cheaper operations
- **Context Management**: Use Roo's built-in context condensing
- **Auto-approval**: Enable for trusted workflows

## 🎯 Next Steps After Installation

1. **Install Roo Code** VS Code extension
2. **Open orchestra-main** project in VS Code
3. **Test /ui command** in Continue.dev alongside Roo
4. **Try specialized modes** for different development tasks
5. **Deploy MCP servers** for enhanced context sharing

## 📚 Resources

- **Documentation**: https://docs.roocode.com/
- **GitHub**: https://github.com/RooCodeInc/Roo-Code
- **Discord**: Join for real-time help and discussions
- **Configuration**: All settings pre-configured in `.roo/` directory

---

**Status**: Roo Code is a VS Code extension with all Orchestra AI configurations ready. Install the extension and start coding with AI assistance! 