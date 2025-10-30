"""
Interest Analyzer Subagent

Analyzes personal files to identify interests, professional focus areas,
and topics that matter for personalized news curation.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
from datetime import datetime


class InterestAnalyzer:
    """Analyzes files to identify personal interests and professional focus areas."""
    
    def __init__(self):
        self.interests = {}
        self.professional_terms = {}
        self.personal_terms = {}
        self.locations = set()
        self.companies = set()
        self.technologies = set()
        
        # Define categories for interest classification
        self.tech_keywords = {
            'artificial intelligence', 'ai', 'machine learning', 'ml', 'python', 'javascript',
            'react', 'node.js', 'docker', 'kubernetes', 'aws', 'azure', 'google cloud',
            'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'web3', 'api', 'rest',
            'graphql', 'microservices', 'devops', 'ci/cd', 'automation', 'cloud computing',
            'data science', 'analytics', 'big data', 'neural networks', 'deep learning',
            'natural language processing', 'nlp', 'computer vision', 'robotics',
            'cybersecurity', 'security', 'encryption', 'privacy', 'gdpr', 'compliance'
        }
        
        self.business_keywords = {
            'fintech', 'financial services', 'banking', 'insurance', 'payments',
            'risk management', 'compliance', 'audit', 'accounting', 'finance',
            'consulting', 'strategy', 'business analysis', 'project management',
            'agile', 'scrum', 'lean', 'transformation', 'digital transformation',
            'innovation', 'startup', 'venture capital', 'investment', 'ipo',
            'mergers', 'acquisitions', 'market analysis', 'competitors'
        }
        
        self.health_keywords = {
            'health', 'fitness', 'running', 'exercise', 'nutrition', 'diet',
            'weight management', 'sleep', 'wellness', 'mental health',
            'quantified self', 'tracking', 'biometrics', 'apple watch',
            'parkrun', 'marathon', 'training', 'recovery'
        }
        
        self.location_patterns = [
            r'\b(London|Surrey|Esher|UK|United Kingdom|New York|Minnesota|Marcell)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})\b',  # City, State/Country
        ]
        
        self.company_patterns = [
            r'\b(ICBC|Standard Bank|Arthur Andersen|Bright Slate|FreeAgent)\b',
            r'\b([A-Z][a-zA-Z]*\s+(?:Ltd|Limited|Inc|Corporation|Corp|Bank|Group))\b'
        ]
    
    def analyze_files(self, paths: List[str], max_files: int = 100) -> Dict:
        """
        Analyze files in given paths to extract interests and topics.
        
        Args:
            paths: List of directory paths to analyze
            max_files: Maximum number of files to analyze per path
            
        Returns:
            Dictionary containing categorized interests and metadata
        """
        all_text = ""
        file_count = 0
        analyzed_files = []
        
        for path in paths:
            if not os.path.exists(path):
                continue
                
            path_obj = Path(path)
            
            # Get all readable text files
            text_files = self._get_text_files(path_obj, max_files)
            
            for file_path in text_files:
                try:
                    content = self._read_file_safely(file_path)
                    if content:
                        all_text += content + " "
                        analyzed_files.append(str(file_path))
                        file_count += 1
                except Exception as e:
                    continue
        
        # Analyze the collected text
        interests = self._extract_interests(all_text)
        
        return {
            'interests': interests,
            'metadata': {
                'files_analyzed': file_count,
                'analyzed_files': analyzed_files[:10],  # Sample of files
                'analysis_date': datetime.now().isoformat(),
                'total_text_length': len(all_text)
            }
        }
    
    def _get_text_files(self, path: Path, max_files: int) -> List[Path]:
        """Get list of readable text files from path."""
        text_extensions = {'.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', 
                          '.csv', '.log', '.conf', '.cfg', '.ini'}
        
        files = []
        
        if path.is_file() and path.suffix.lower() in text_extensions:
            return [path]
        
        if path.is_dir():
            try:
                for file_path in path.rglob('*'):
                    if (file_path.is_file() and 
                        file_path.suffix.lower() in text_extensions and
                        not any(part.startswith('.') for part in file_path.parts) and
                        len(files) < max_files):
                        files.append(file_path)
            except (PermissionError, OSError):
                pass
        
        return files
    
    def _read_file_safely(self, file_path: Path) -> str:
        """Safely read file content with encoding detection."""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                    # Skip very large files (>1MB)
                    if len(content) > 1_000_000:
                        return content[:100_000]  # Take first 100KB
                    return content
            except (UnicodeError, OSError):
                continue
        
        return ""
    
    def _extract_interests(self, text: str) -> Dict:
        """Extract and categorize interests from text."""
        text_lower = text.lower()
        
        # Extract different categories
        technology_interests = self._score_keywords(text_lower, self.tech_keywords)
        business_interests = self._score_keywords(text_lower, self.business_keywords)
        health_interests = self._score_keywords(text_lower, self.health_keywords)
        
        # Extract entities
        locations = self._extract_locations(text)
        companies = self._extract_companies(text)
        
        # Extract frequent terms that might be interests
        custom_interests = self._extract_custom_terms(text_lower)
        
        return {
            'technology': dict(technology_interests.most_common(15)),
            'business': dict(business_interests.most_common(15)),
            'health_fitness': dict(health_interests.most_common(10)),
            'locations': list(locations)[:10],
            'companies': list(companies)[:10],
            'custom_terms': dict(custom_interests.most_common(20)),
            'top_interests': self._get_top_interests(
                technology_interests, business_interests, 
                health_interests, custom_interests
            )
        }
    
    def _score_keywords(self, text: str, keywords: Set[str]) -> Counter:
        """Score keywords based on frequency in text."""
        scores = Counter()
        
        for keyword in keywords:
            # Count exact matches and variations
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE))
            if count > 0:
                scores[keyword] = count
        
        return scores
    
    def _extract_locations(self, text: str) -> Set[str]:
        """Extract location names from text."""
        locations = set()
        
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text)
            locations.update(matches)
        
        return locations
    
    def _extract_companies(self, text: str) -> Set[str]:
        """Extract company names from text."""
        companies = set()
        
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text)
            companies.update(matches)
        
        return companies
    
    def _extract_custom_terms(self, text: str) -> Counter:
        """Extract frequently mentioned terms that could be interests."""
        # Remove common words
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'being',
            'been', 'be', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
            'doing', 'a', 'an', 'the', 'as', 'if', 'each', 'how', 'which', 'who',
            'when', 'where', 'why', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just',
            'should', 'now', 'get', 'could', 'would', 'one', 'two', 'first', 'may',
            'use', 'work', 'new', 'way', 'also', 'make', 'good', 'look', 'help',
            'go', 'great', 'right', 'still', 'around', 'here', 'where', 'much',
            'well', 'back', 'see', 'come', 'time', 'know', 'want', 'think', 'take',
            'need', 'find', 'give', 'day', 'year', 'place', 'part', 'end', 'life'
        }
        
        # Extract multi-word terms (2-3 words)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Count 2-word and 3-word phrases
        terms = Counter()
        
        for i in range(len(words) - 1):
            if words[i] not in common_words and words[i+1] not in common_words:
                bigram = f"{words[i]} {words[i+1]}"
                terms[bigram] += 1
        
        for i in range(len(words) - 2):
            if (words[i] not in common_words and 
                words[i+1] not in common_words and 
                words[i+2] not in common_words):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                terms[trigram] += 1
        
        # Filter out terms that appear less than 3 times
        return Counter({term: count for term, count in terms.items() if count >= 3})
    
    def _get_top_interests(self, *counters) -> List[Tuple[str, int]]:
        """Combine all counters and get top interests overall."""
        combined = Counter()
        
        for counter in counters:
            combined.update(counter)
        
        return combined.most_common(20)
    
    def get_search_terms(self, interests_data: Dict) -> List[str]:
        """
        Convert interest analysis into search terms for news curation.
        
        Args:
            interests_data: Output from analyze_files()
            
        Returns:
            List of search terms optimized for news search
        """
        search_terms = []
        
        # Add top interests from each category
        for category, items in interests_data['interests'].items():
            if isinstance(items, dict):
                # Take top 5 from each category
                for term, score in list(items.items())[:5]:
                    if score >= 2:  # Only include terms mentioned multiple times
                        search_terms.append(term)
        
        # Add company names for business news
        companies = interests_data['interests'].get('companies', [])
        search_terms.extend(companies[:5])
        
        # Add location-based search terms
        locations = interests_data['interests'].get('locations', [])
        for location in locations[:3]:
            search_terms.append(f"{location} business")
            search_terms.append(f"{location} technology")
        
        # Remove duplicates and return
        return list(set(search_terms))[:25]  # Limit to 25 search terms
    
    def explain_relevance(self, interests_data: Dict, news_item: str) -> Tuple[float, str]:
        """
        Explain why a news item is relevant based on analyzed interests.
        
        Args:
            interests_data: Output from analyze_files()
            news_item: News article text or headline
            
        Returns:
            Tuple of (relevance_score, explanation)
        """
        relevance_score = 0.0
        explanations = []
        
        news_lower = news_item.lower()
        
        # Check against each interest category
        for category, items in interests_data['interests'].items():
            if isinstance(items, dict):
                for term, score in items.items():
                    if term.lower() in news_lower:
                        category_score = min(score * 0.1, 1.0)  # Cap at 1.0
                        relevance_score += category_score
                        explanations.append(
                            f"Matches your {category} interest in '{term}' (mentioned {score} times in your files)"
                        )
        
        # Check companies
        companies = interests_data['interests'].get('companies', [])
        for company in companies:
            if company.lower() in news_lower:
                relevance_score += 0.8
                explanations.append(f"Mentions {company}, which appears in your files")
        
        # Check locations
        locations = interests_data['interests'].get('locations', [])
        for location in locations:
            if location.lower() in news_lower:
                relevance_score += 0.5
                explanations.append(f"Related to {location}, a location in your context")
        
        # Normalize score to 0-1 range
        relevance_score = min(relevance_score, 1.0)
        
        explanation = "; ".join(explanations[:3]) if explanations else "General relevance based on your interests"
        
        return relevance_score, explanation