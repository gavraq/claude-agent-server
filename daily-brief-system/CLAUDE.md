# Daily Brief System

## Project Overview
AI-powered news curation system that analyzes Gavin's personal files for interests and delivers personalized daily briefings with relevant current events from the past 7 days. Integrated with Claude Code's WebSearch and WebFetch tools.

## System Architecture

### Core Components
- **`InterestAnalyzer`** - Scans 200+ personal files to identify interests and topics
- **`NewsSearcher`** - Searches current news (past 7 days only) from reputable sources
- **`SimpleDailyBrief`** - Main orchestration system with web tool integration

### File Structure
```
daily-brief-system/
├── daily_brief_simple.py       # Production system with web tools
├── interest_analyzer.py        # Personal file analysis for interests
├── news_curator.py            # News search and curation
├── daily_brief.py             # Core system orchestration
├── demo_daily_brief.py        # Testing without web tools
├── daily_brief.sh             # Shell wrapper (explains usage)
├── venv/                      # Python virtual environment
└── requirements.txt           # Dependencies
```

### Integration Points
- **Main Entry**: `/Users/gavinslater/projects/Life/daily_brief.py`
- **Import Source**: `daily-brief-system/daily_brief_simple.py`
- **Output Files**: `daily-brief-YYYY-MM-DD.md` in project root
- **Claude Code Integration**: Requires WebSearch and WebFetch tools

## Interest Analysis System

### Analysis Paths
Scans multiple directories for personal context:
```
default_paths = [
    "/Users/gavinslater/projects/life",      # This repository
    "/Users/gavinslater/Desktop",            # Current work files
    "/Users/gavinslater/Library/Mobile Documents/iCloud~md~obsidian/Documents/GavinsiCloudVault",  # Obsidian notes
    "/Users/gavinslater/.config"             # Configuration files
]
```

### File Types Analyzed
- **Text Files**: `.txt`, `.md`, `.py`, `.js`, `.json`, `.yaml`, `.csv`, `.log`
- **Processing**: 200+ files analyzed, 1M+ characters processed
- **Analysis Time**: 30-60 seconds for complete interest extraction

### Key Interest Categories Detected
- **Technology**: python (238 mentions), api (222), docker (220), ai (143)
- **Business**: risk management, finance, consulting, audit
- **Companies**: ICBC, Standard Bank, FreeAgent
- **Locations**: London, Surrey, New York

## News Curation Process

### Data Flow
1. **Interest Analysis**: Extract current interests and focus areas from personal files
2. **Search Term Generation**: Create targeted search queries from interest analysis
3. **Web Search**: Search for relevant articles using WebSearch tool
4. **Content Fetching**: Retrieve full article content using WebFetch tool
5. **Relevance Scoring**: Rate articles 0.0-1.0 based on alignment with interests
6. **Actionable Insights**: Generate specific suggestions for each relevant article
7. **Output Generation**: Format as comprehensive daily brief markdown

### News Sources
- **Primary**: BBC, Reuters, Bloomberg, Financial Times, TechCrunch, The Guardian
- **Search Scope**: Past 7 days only for current relevance
- **Article Processing**: 20-30 articles analyzed per briefing session

### Performance Characteristics
- **Analysis Phase**: 30-60 seconds (200+ files, 1M+ characters)
- **Curation Phase**: 2-4 minutes (10-12 web searches, 20-30 articles)
- **Total Time**: 3-5 minutes for complete personalized brief
- **Output**: 10-15 relevant articles with 0.3+ relevance scores

## Technical Implementation

### Primary Usage (Claude Code Environment)
```python
from daily_brief import daily_brief
result = daily_brief()
print(result)
```

### Virtual Environment Setup
```bash
cd daily-brief-system
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Testing Without Web Tools
```bash
cd daily-brief-system
python3 demo_daily_brief.py
```

### Dependencies
- **Core**: `requests`, `python-dateutil`, `beautifulsoup4`, `feedparser`
- **Web Integration**: Requires Claude Code's WebSearch and WebFetch tools
- **Platform**: Python 3.9+ (currently using 3.13)

## Configuration & Requirements

### Authentication
- **No API Keys Required**: Uses public web search only
- **Privacy First**: Personal files analyzed locally, not uploaded
- **Web Search Only**: Only search queries sent over network, not file contents

### File Processing
- **Local Analysis**: All personal file analysis happens locally
- **No Persistence**: No permanent storage of personal information
- **Security**: Personal files never leave the machine

### Output Format
```markdown
# Daily Brief - [Date]

## 🎯 Today's Relevance Focus
- Current priorities and focus areas

## 📰 High Relevance News (0.7+ score)
- [Article] - [Relevance reason] - [Actionable insight]

## 📄 Medium Relevance News (0.4-0.6 score)
- [Article] - [Brief description]

## 🚀 Action Items
- [Specific actions based on news analysis]
- [Connections to ongoing projects]
```

## Agent Integration

### Command Integration
- **Command**: `/daily-brief` via `.claude/commands/daily-brief.md`
- **Context Loading**: Auto-loads UFC context for personalization
- **Agent Support**: Daily Brief Agent (`daily-brief-agent`) for complex curation

### Context Awareness
- **Profile Integration**: Aligns with core identity and goals
- **Project Awareness**: Connects news to active projects (AI transition, etc.)
- **Progress Tracking**: Links news insights to quantified self objectives

## Error Handling & Troubleshooting

### Common Issues
- **"Web search tools not available"**: Must run in Claude Code environment, not standalone Python
- **"No relevant articles found"**: Lower `min_relevance` threshold or increase `max_articles`
- **"Could not analyze interests"**: Check file permissions in analysis paths

### Performance Optimization
- **Interest Caching**: Reuse interest analysis across multiple briefings
- **Search Efficiency**: Optimize search terms for better relevance
- **Content Processing**: Parallel processing of article analysis

### Debugging
- **Demo Mode**: Use `demo_daily_brief.py` for testing without web tools
- **Verbose Output**: Enable detailed logging for troubleshooting
- **Interest Validation**: Review extracted interests for accuracy

## Validation & Testing

### Testing Strategy
- **No Formal Test Suite**: Uses demo system for validation
- **Demo Testing**: `python3 daily-brief-system/demo_daily_brief.py`
- **Integration Testing**: Run `/daily-brief` command in Claude Code
- **Output Validation**: Check generated briefs in `daily-brief-*.md` files

### Quality Metrics
- **Relevance Accuracy**: Target 0.3+ relevance scores for included articles
- **Coverage**: 10-15 relevant articles per briefing
- **Actionability**: Each high-relevance article includes specific action suggestions
- **Timeliness**: Focus on past 7 days for current relevance

This system provides personalized, AI-powered news curation specifically tailored to Gavin's interests, goals, and current projects, integrated with his broader Personal AI Infrastructure.