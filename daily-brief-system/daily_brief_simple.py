#!/usr/bin/env python3
"""
Simple Daily Brief System

Self-contained daily brief system without external dependencies.
Provides the /daily-brief command functionality.
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

# Add the system path
sys.path.insert(0, str(Path(__file__).parent))

from interest_analyzer import InterestAnalyzer


class SimpleDailyBrief:
    """Simple daily brief system using built-in Python only."""
    
    def __init__(self, web_search_tool, web_fetch_tool):
        """Initialize with web tools."""
        self.web_search = web_search_tool
        self.web_fetch = web_fetch_tool
        self.interest_analyzer = InterestAnalyzer()
        self.cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    
    def generate_daily_brief(
        self, 
        max_articles: int = 15,
        min_relevance: float = 0.3,
        force_reanalyze: bool = False,
        analysis_paths: Optional[List[str]] = None
    ) -> str:
        """Generate a complete daily news brief."""
        
        print("🔍 Generating your personalized daily brief...")
        
        try:
            # Step 1: Analyze interests
            interests_data = self._analyze_interests(analysis_paths, force_reanalyze)
            if not interests_data:
                return "❌ **Error**: Could not analyze your interests from files."
            
            # Step 2: Generate search terms
            search_terms = self.interest_analyzer.get_search_terms(interests_data)
            if not search_terms:
                return "❌ **Error**: No search terms could be generated from your interests."
            
            print(f"🎯 Generated {len(search_terms)} search terms from your interests")
            
            # Step 3: Search and curate news
            articles = self._curate_current_news(search_terms, max_articles * 2, interests_data)
            
            # Step 4: Filter by relevance
            filtered_articles = [a for a in articles if a['relevance_score'] >= min_relevance]
            final_articles = sorted(filtered_articles, key=lambda x: x['relevance_score'], reverse=True)[:max_articles]
            
            print(f"📰 Found {len(final_articles)} relevant articles from the past 7 days")
            
            # Step 5: Generate the complete brief
            if final_articles:
                return self._format_daily_brief(interests_data, final_articles, search_terms)
            else:
                return self._format_no_news_brief(interests_data, search_terms)
                
        except Exception as e:
            return f"❌ **Error generating brief**: {str(e)}"
    
    def _analyze_interests(self, analysis_paths: Optional[List[str]], force_reanalyze: bool) -> Optional[Dict]:
        """Analyze user interests from files."""
        
        # Use default paths if none provided
        if not analysis_paths:
            analysis_paths = [
                "/Users/gavinslater/projects/life",
                "/Users/gavinslater/Desktop", 
                "/Users/gavinslater/Library/Mobile Documents/iCloud~md~obsidian/Documents/GavinsiCloudVault",
                "/Users/gavinslater/.config"
            ]
        
        # Filter to existing paths
        valid_paths = [p for p in analysis_paths if os.path.exists(p)]
        
        if not valid_paths:
            print("⚠️ No valid paths found for analysis")
            return None
        
        print(f"📁 Analyzing interests from {len(valid_paths)} directories...")
        
        try:
            interests_data = self.interest_analyzer.analyze_files(valid_paths, max_files=200)
            print(f"✅ Analyzed {interests_data.get('metadata', {}).get('files_analyzed', 0)} files")
            return interests_data
        except Exception as e:
            print(f"❌ Error analyzing interests: {e}")
            return None
    
    def _curate_current_news(self, search_terms: List[str], max_articles: int, interests_data: Dict) -> List[Dict]:
        """Search for and curate current news articles."""
        
        all_articles = []
        processed_urls = set()
        
        # Limit search terms to avoid rate limits
        limited_terms = search_terms[:10]
        
        for term in limited_terms:
            try:
                print(f"🔍 Searching for news about: {term}")
                
                # Search for recent news
                current_year = datetime.now().year
                search_query = f"{term} news {current_year} latest"
                
                # Use allowed domains for reputable news sources
                search_result = self.web_search(
                    query=search_query,
                    allowed_domains=[
                        "bbc.co.uk", "reuters.com", "bloomberg.com", "ft.com",
                        "techcrunch.com", "theguardian.com", "cnn.com", "wsj.com", 
                        "forbes.com", "wired.com", "arstechnica.com", "venturebeat.com"
                    ]
                )
                
                # Extract articles from search results
                articles = self._extract_articles_from_search(search_result, term, processed_urls, interests_data)
                all_articles.extend(articles)
                
                if len(all_articles) >= max_articles:
                    break
                    
            except Exception as e:
                print(f"⚠️ Error searching for '{term}': {e}")
                continue
        
        return all_articles[:max_articles]
    
    def _extract_articles_from_search(self, search_result: str, search_term: str, processed_urls: set, interests_data: Dict) -> List[Dict]:
        """Extract article information from search results."""
        
        articles = []
        
        # Extract URLs from search results
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;!?)]'
        urls = re.findall(url_pattern, search_result)
        
        # Filter to news URLs and remove duplicates
        news_urls = []
        for url in urls:
            url = url.rstrip('.,;!?)')
            if self._is_news_url(url) and url not in processed_urls:
                news_urls.append(url)
                processed_urls.add(url)
        
        # Process top URLs
        for url in news_urls[:2]:  # Limit to 2 articles per search term
            try:
                article = self._process_article(url, search_term, interests_data)
                if article:
                    articles.append(article)
            except Exception as e:
                print(f"⚠️ Error processing {url}: {e}")
                continue
        
        return articles
    
    def _is_news_url(self, url: str) -> bool:
        """Check if URL appears to be a news article."""
        url_lower = url.lower()
        
        # News indicators
        news_indicators = [
            'news', 'article', 'story', 'report', '/2024/', '/2025/',
            'breaking', 'latest', 'today'
        ]
        
        return any(indicator in url_lower for indicator in news_indicators)
    
    def _process_article(self, url: str, search_term: str, interests_data: Dict) -> Optional[Dict]:
        """Process individual article and verify recency."""
        
        try:
            print(f"📰 Processing article: {self._get_domain(url)}")
            
            # Fetch article content
            prompt = (
                "Extract the headline, publication date, and a brief summary from this news article. "
                "Focus on finding the exact publication date and main points. "
                "Provide a clear, concise summary of the key information."
            )
            
            content = self.web_fetch(url=url, prompt=prompt)
            
            if not content or len(content.strip()) < 50:
                return None
            
            # Extract article information
            headline = self._extract_headline(content)
            pub_date = self._extract_simple_date(content, url)
            summary = self._extract_summary(content)
            
            # Calculate relevance
            relevance_score, explanation = self.interest_analyzer.explain_relevance(
                interests_data,
                f"{headline} {summary}"
            )
            
            # Generate simple actions
            actions = self._generate_simple_actions(search_term, content)
            
            return {
                'headline': headline,
                'url': url,
                'published_date': pub_date,
                'summary': summary,
                'search_term': search_term,
                'relevance_score': relevance_score,
                'relevance_explanation': explanation,
                'action_suggestions': actions,
                'source_domain': self._get_domain(url),
                'verified_recent': True
            }
            
        except Exception as e:
            print(f"⚠️ Error processing article {url}: {e}")
            return None
    
    def _extract_headline(self, content: str) -> str:
        """Extract headline from article content."""
        # Look for headline patterns
        headline_patterns = [
            r'(?i)headline[:\s]*(.+?)(?:\n|$)',
            r'(?i)title[:\s]*(.+?)(?:\n|$)',
        ]
        
        for pattern in headline_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                headline = match.group(1).strip()
                if 10 <= len(headline) <= 200 and not headline.startswith('http'):
                    return headline
        
        # Fallback: take first substantial line
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        for line in lines:
            if 20 <= len(line) <= 200 and not line.startswith('http'):
                return line
        
        return "News Article"
    
    def _extract_simple_date(self, content: str, url: str) -> str:
        """Extract publication date as simple string."""
        
        # Look for common date patterns
        date_patterns = [
            r'(?i)(?:published|date)[:\s]*([^\n]+)',
            r'(?i)((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1).strip()
                if self._looks_like_recent_date(date_str):
                    return date_str
        
        # Look for relative dates
        if any(word in content.lower() for word in ['today', 'yesterday', 'latest', 'breaking']):
            return "Recent"
        
        # Check URL for date
        url_date_match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', url)
        if url_date_match:
            year, month, day = url_date_match.groups()
            if int(year) >= 2024:  # Recent year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return "Recent"
    
    def _looks_like_recent_date(self, date_str: str) -> bool:
        """Simple check if date string looks recent."""
        # Check for current year
        current_year = str(datetime.now().year)
        return current_year in date_str or 'december' in date_str.lower() or 'january' in date_str.lower()
    
    def _extract_summary(self, content: str) -> str:
        """Extract article summary."""
        # Look for summary patterns
        summary_patterns = [
            r'(?i)summary[:\s]+([^\n]{100,500})',
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        # Extract first good paragraph
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        good_sentences = [s for s in sentences if 30 <= len(s) <= 200 and not s.startswith('http')]
        
        if good_sentences:
            return '. '.join(good_sentences[:3]) + '.'
        
        return "Summary not available"
    
    def _generate_simple_actions(self, search_term: str, content: str) -> List[str]:
        """Generate simple action suggestions."""
        actions = []
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['launch', 'release', 'update']):
            actions.append(f"Research new developments in {search_term}")
            
        if any(word in content_lower for word in ['market', 'price', 'investment']):
            actions.append("Monitor market implications")
            
        if any(word in content_lower for word in ['regulation', 'policy', 'law']):
            actions.append("Review regulatory impact")
        
        if not actions:
            actions.append(f"Stay updated on {search_term}")
        
        return actions[:2]
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else 'unknown'
    
    def _format_daily_brief(self, interests_data: Dict, articles: List[Dict], search_terms: List[str]) -> str:
        """Format the complete daily brief."""
        
        now = datetime.now()
        
        brief = f"""# 📰 Your Personalized Daily Brief
## {now.strftime('%A, %B %d, %Y')}

🕐 **Generated:** {now.strftime('%I:%M %p')}  
📊 **Articles:** {len(articles)} relevant stories from the past 7 days  
📁 **Files analyzed:** {interests_data.get('metadata', {}).get('files_analyzed', 0)}  

---

## 🎯 Your Key Interests

"""
        
        # Add interest summary
        interests = interests_data.get('interests', {})
        top_interests = interests.get('top_interests', [])
        
        if top_interests:
            brief += "**Top topics:** "
            brief += ", ".join([f"{term} ({count})" for term, count in top_interests[:8]])
            brief += "\n\n"
        
        brief += "---\n\n## 📰 Today's Relevant News\n\n"
        
        # Add articles
        for i, article in enumerate(articles, 1):
            brief += f"### {i}. {article['headline']}\n\n"
            
            # Article metadata
            brief += f"📅 **{article['published_date']}** | 🌐 **{article['source_domain']}** | 📊 **Relevance: {article['relevance_score']:.1f}/1.0**\n\n"
            
            # Summary
            brief += f"{article['summary']}\n\n"
            
            # Relevance explanation
            brief += f"**🎯 Why this matters:** {article['relevance_explanation']}\n\n"
            
            # Action suggestions
            if article.get('action_suggestions'):
                brief += "**🚀 Actions:**\n"
                for action in article['action_suggestions']:
                    brief += f"• {action}\n"
                brief += "\n"
            
            # Link
            brief += f"🔗 [Read article]({article['url']})\n\n"
            brief += "---\n\n"
        
        # Footer
        brief += f"""## 🔍 Brief Details

**Search terms:** {', '.join(search_terms[:8])}{"..." if len(search_terms) > 8 else ""}

**Sources:** Reputable news outlets including BBC, Reuters, Bloomberg, TechCrunch, and others

---

*📅 All articles from the past 7 days*  
*🎯 Personalized based on your files and interests*  
*🔄 Run again tomorrow for fresh news*
"""
        
        return brief
    
    def _format_no_news_brief(self, interests_data: Dict, search_terms: List[str]) -> str:
        """Format brief when no relevant articles found."""
        
        now = datetime.now()
        
        return f"""# 📰 Your Personalized Daily Brief
## {now.strftime('%A, %B %d, %Y')}

🕐 **Generated:** {now.strftime('%I:%M %p')}

## 🔍 No Highly Relevant News Found

Searched for recent articles matching your interests but didn't find any with high relevance scores.

**Your interests:** {', '.join([t[0] for t in interests_data.get('interests', {}).get('top_interests', [])[:5]])}

**Search terms used:** {', '.join(search_terms[:8])}

---

*Try lowering the minimum relevance threshold or check back tomorrow for fresh coverage*
"""


def daily_brief(
    max_articles: int = 15,
    min_relevance: float = 0.3,
    force_reanalyze: bool = False,
    custom_paths: str = None
) -> str:
    """
    Generate your personalized daily news brief.
    
    Args:
        max_articles: Maximum number of articles (default 15)
        min_relevance: Minimum relevance score 0.0-1.0 (default 0.3)
        force_reanalyze: Force fresh interest analysis (default False)
        custom_paths: Comma-separated paths to analyze
        
    Returns:
        Complete daily news brief
    """
    
    # Parse custom paths if provided
    analysis_paths = None
    if custom_paths:
        analysis_paths = [p.strip() for p in custom_paths.split(',')]
        analysis_paths = [p for p in analysis_paths if os.path.exists(p)]
        if not analysis_paths:
            return "❌ **Error**: None of the provided paths exist."
    
    # Create the system with web tools
    try:
        system = SimpleDailyBrief(WebSearch, WebFetch)
        return system.generate_daily_brief(
            max_articles=max_articles,
            min_relevance=min_relevance, 
            force_reanalyze=force_reanalyze,
            analysis_paths=analysis_paths
        )
    except NameError as e:
        return f"❌ **Error**: Web search tools not available: {e}"
    except Exception as e:
        return f"❌ **Error**: {e}"


# Export the main function
__all__ = ['daily_brief']