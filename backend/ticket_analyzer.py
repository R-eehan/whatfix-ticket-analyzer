"""
Whatfix Support Ticket Analyzer - Complete Backend Solution
===========================================================
This module provides a complete solution for analyzing Whatfix support tickets,
summarizing issues, and determining diagnostics compatibility.

Author: Whatfix Platform Team
Version: 1.0.0
"""

import pandas as pd
import json
import logging
import re
import os
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
from collections import Counter
from abc import ABC, abstractmethod
import hashlib
import google.generativeai as genai
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Method to extract json from an LLM response
def extract_json_from_code_block(text: str) -> str:
    """
    Extract JSON string from a markdown code block.
    Handles ```json ... ``` or ``` ... ```
    """
    # Remove triple backticks and optional 'json' language tag
    code_block_pattern = r"```(?:json)?\\s*([\\s\\S]*?)\\s*```"
    match = re.search(code_block_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


# ============================================================================
# SECTION 1: LLM PROVIDERS
# ============================================================================

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    @abstractmethod
    def summarize_conversation(self, messages: List[str], system_prompt: str) -> str:
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider for conversation summarization"""
    def __init__(self, api_key: str, model: str = "gpt-4"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def summarize_conversation(self, messages: List[str], system_prompt: str) -> str:
        conversation = "\n\n".join([f"Comment {i+1}: {msg}" for i, msg in enumerate(messages)])
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for conversation summarization"""
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def summarize_conversation(self, messages: List[str], system_prompt: str) -> str:
        conversation = "\n\n".join([f"Comment {i+1}: {msg}" for i, msg in enumerate(messages)])
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": conversation}
            ]
        )
        
        return message.content[0].text


class MockProvider(LLMProvider):
    """Mock provider for testing without API calls"""
    def summarize_conversation(self, messages: List[str], system_prompt: str) -> str:
        # Simulate LLM analysis based on comment content
        issue = "User unable to display smart tip in preview mode"
        resolution = "Reselected the smart tip element and added necessary CSS selector"
        category = "Element Selection"
        resolution_type = "Reselection"
        
        # Simple pattern matching for mock categorization
        combined_text = " ".join(messages).lower()
        if "css" in combined_text or "selector" in combined_text:
            category = "CSS Selector"
            resolution_type = "CSS Addition"
        elif "visibility" in combined_text:
            category = "Visibility Rules"
            resolution_type = "Configuration Change"
        
        return json.dumps({
            "issue": issue,
            "resolution": resolution,
            "category": category,
            "resolution_type": resolution_type
        })
    
class GeminiAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")
    
    def summarize_conversation(self, messages: List[str], system_prompt: str) -> str:
        conversation = "\n\n".join([f"Comment {i+1}: {msg}" for i, msg in enumerate(messages)])
        
        # Combine system prompt and conversation
        full_prompt = f"{system_prompt}\n\nConversation:\n{conversation}"
        
        response = self.model.generate_content(
            full_prompt,
            generation_config= genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=10000,
            )
        )
        # Try to extract from candidates/parts if available
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content.parts:
                    result = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    #print("Cleaning LLM response....")
                    #cleaned_result = extract_json_from_code_block(result)
                    #print(cleaned_result)
                    return result
        # Fallback: return a message or empty string
        return "[No valid response from Gemini API]"


# ============================================================================
# SECTION 2: TICKET PROCESSOR
# ============================================================================

class TicketProcessor:
    """Enhanced ticket processor with comprehensive data extraction"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.system_prompt = """You are analyzing a support ticket conversation between a customer and support agent.
        
Please analyze the conversation and provide a response with the following structure AS A STRING:
    {
        "issue": "Precise description of the customer's problem",
        "resolution": "Exact steps taken by support to resolve the issue",
        "category": "Primary category of the issue (e.g., Element Selection, Content Visibility, Configuration, CSS Selector, Performance, etc.)",
        "resolution_type": "Type of resolution (e.g., Reselection, CSS Addition, Configuration Change, Bug Fix, User Education, etc.)"
    }

In your response, DO NOT add the term, prefix or wrap the above structure with "```json```". You should return the structure as a simple string.

Focus on:
1. What exactly wasn't working from the customer's perspective
2. What specific technical actions the support agent took
3. Whether the issue was truly resolved
4. The root technical cause (not just symptoms)"""

    def clean_comment_body(self, body: str) -> str:
        """Clean and normalize comment body text"""
        if pd.isna(body):
            return ""
        
        # Remove metadata blocks
        body = str(body)
        body = re.sub(r'Message sent:.*?(?=\n\n|\Z)', '', body, flags=re.DOTALL)
        body = re.sub(r'(Email|Phone|IP|User Agent|Country|City|URL|Chat ID):\s*[^\n]+\n?', '', body)
        
        # Remove excessive whitespace
        body = re.sub(r'\s+', ' ', body)
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        # Remove image placeholders
        body = re.sub(r'!\[.*?\]\(.*?\)', '[Image]', body)
        
        # Remove URLs in markdown format
        body = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', body)
        
        return body.strip()

    def identify_comment_type(self, comment_body: str, position: int) -> str:
        """Identify if comment is from customer or support agent"""
        comment_lower = comment_body.lower()
        
        # Support agent indicators
        agent_indicators = [
            'thank you for reaching out',
            'whatfix support team',
            'regards,',
            'i\'ve reselected',
            'i\'ve checked',
            'please check on your end',
            'i\'ll close this thread',
            'happy to assist'
        ]
        
        # Customer indicators
        customer_indicators = [
            'hi, i added',
            'i cannot',
            'please help',
            'any help would be',
            'i\'m trying to',
            'thanks for your help'
        ]
        
        agent_score = sum(1 for indicator in agent_indicators if indicator in comment_lower)
        customer_score = sum(1 for indicator in customer_indicators if indicator in comment_lower)
        
        if agent_score > customer_score:
            return 'agent'
        elif customer_score > agent_score:
            return 'customer'
        else:
            # Use position as fallback - first comment usually from customer
            return 'customer' if position == 0 else 'agent'

    def process_ticket_comments(self, comments_df: pd.DataFrame) -> Dict:
        """Process all comments for a single ticket"""
        # Sort comments by ID to maintain chronological order
        comments_df = comments_df.sort_values('Zendesk Comments ID')
        
        # Extract and clean comment bodies with metadata
        cleaned_comments = []
        comment_metadata = []
        
        for idx, (_, row) in enumerate(comments_df.iterrows()):
            cleaned_body = self.clean_comment_body(row['Zendesk Comments Body'])
            if cleaned_body and len(cleaned_body) > 10:
                cleaned_comments.append(cleaned_body)
                comment_type = self.identify_comment_type(cleaned_body, idx)
                comment_metadata.append({
                    'type': comment_type,
                    'position': idx + 1,
                    'comment_id': row['Zendesk Comments ID']
                })
        
        return {
            'ticket_id': comments_df.iloc[0]['Zendesk Tickets ID'],
            'ent_id': comments_df.iloc[0]['Zendesk Tickets Ent ID'],
            'subject': comments_df.iloc[0]['Zendesk Tickets Subject'],
            'original_category': comments_df.iloc[0].get('Support Ticket Output Gpt Subcategory', 'Unknown'),
            'original_root_cause': comments_df.iloc[0]['Zendesk Tickets Root Cause'],
            'comments': cleaned_comments,
            'comment_metadata': comment_metadata,
            'comment_count': len(cleaned_comments),
            'total_exchanges': len(comments_df)
        }

    def summarize_ticket(self, ticket_data: Dict) -> Dict:
        """Summarize a single ticket using LLM"""
        try:
            # Get LLM summary
            summary_json = self.llm_provider.summarize_conversation(
                ticket_data['comments'],
                self.system_prompt
            )
            
            # Parse the JSON response
            try:
                summary = json.loads(summary_json)
                #print("Entering try block, printing summary of the tickets")
                #print(summary)
            except json.JSONDecodeError:
                print("Entering except block, something went wrong...")
                summary = {
                    "issue": "Failed to parse LLM response",
                    "resolution": summary_json,
                    "category": "Unknown",
                    "resolution_type": "Unknown"
                }
            
            # Combine with ticket metadata
            result = {
                'ticket_id': ticket_data['ticket_id'],
                'ent_id': ticket_data['ent_id'],
                'subject': ticket_data['subject'],
                'issue_summary': summary.get('issue', ''),
                'resolution_summary': summary.get('resolution', ''),
                'derived_category': summary.get('category', ''),
                'resolution_type': summary.get('resolution_type', ''),
                'original_category': ticket_data['original_category'],
                'original_root_cause': ticket_data['original_root_cause'],
                'comment_count': ticket_data['comment_count'],
                'conversation_metadata': {
                    'total_exchanges': ticket_data['total_exchanges'],
                    'customer_messages': sum(1 for m in ticket_data['comment_metadata'] if m['type'] == 'customer'),
                    'agent_messages': sum(1 for m in ticket_data['comment_metadata'] if m['type'] == 'agent')
                }
            }
            
            print(result)
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing ticket {ticket_data['ticket_id']}: {str(e)}")
            return {
                'ticket_id': ticket_data['ticket_id'],
                'ent_id': ticket_data['ent_id'],
                'subject': ticket_data['subject'],
                'issue_summary': f"Error: {str(e)}",
                'resolution_summary': '',
                'derived_category': 'Error',
                'resolution_type': 'Error',
                'original_category': ticket_data['original_category'],
                'original_root_cause': ticket_data['original_root_cause'],
                'comment_count': ticket_data['comment_count']
            }


# ============================================================================
# SECTION 3: DIAGNOSTICS ANALYZER
# ============================================================================

class DiagnosticsAnalyzer:
    """Analyze tickets for diagnostics compatibility"""
    
    def __init__(self):
        # Define patterns that indicate diagnostics compatibility
        self.diagnostics_patterns = {
            'element_not_found': [
                'element', 'selector', 'css', 'xpath', 'not found', 
                'cannot find', 'unable to locate', 'reselect'
            ],
            'visibility_issues': [
                'not showing', 'not visible', 'hidden', 'display', 
                'visibility rule', 'not appearing'
            ],
            'content_failure': [
                'flow fail', 'step fail', 'broken', 'not working',
                'error', 'failure'
            ],
            'configuration': [
                'configuration', 'settings', 'rule', 'condition',
                'advanced code', 'custom code'
            ]
        }
        
        self.simple_resolutions = [
            'reselect', 'css selector', 'visibility rule',
            'element property', 'configuration change'
        ]

    def check_diagnostics_compatibility(self, ticket_summary: Dict) -> Dict:
        """Detailed check if a specific ticket could be resolved with diagnostics"""
        
        diagnostics_checks = {
            'element_detection': False,
            'visibility_rules': False,
            'simple_css_fix': False,
            'configuration_issue': False,
            'requires_code_change': False,
            'requires_human_analysis': False
        }
        
        issue = ticket_summary['issue_summary'].lower()
        resolution = ticket_summary['resolution_summary'].lower()
        
        # Check various patterns
        for pattern_name, keywords in self.diagnostics_patterns.items():
            if any(keyword in issue for keyword in keywords):
                if pattern_name == 'element_not_found':
                    diagnostics_checks['element_detection'] = True
                elif pattern_name == 'visibility_issues':
                    diagnostics_checks['visibility_rules'] = True
                elif pattern_name == 'configuration':
                    diagnostics_checks['configuration_issue'] = True
        
        # Check resolution patterns
        if any(res in resolution for res in self.simple_resolutions):
            diagnostics_checks['simple_css_fix'] = True
        
        if any(term in resolution for term in ['custom code', 'javascript', 'advanced']):
            diagnostics_checks['requires_code_change'] = True
        
        # Complex issues requiring human analysis
        if ticket_summary['comment_count'] > 6:
            diagnostics_checks['requires_human_analysis'] = True
        
        # Calculate compatibility score
        positive_indicators = sum([
            diagnostics_checks['element_detection'],
            diagnostics_checks['visibility_rules'],
            diagnostics_checks['simple_css_fix'],
            diagnostics_checks['configuration_issue']
        ])
        
        negative_indicators = sum([
            diagnostics_checks['requires_code_change'],
            diagnostics_checks['requires_human_analysis']
        ])
        
        compatibility_score = positive_indicators - negative_indicators
        is_compatible = compatibility_score > 0
        
        return {
            'ticket_id': ticket_summary['ticket_id'],
            'is_diagnostics_compatible': is_compatible,
            'compatibility_score': compatibility_score,
            'checks': diagnostics_checks,
            'recommendation': 'Can be automated with diagnostics' if is_compatible else 'Requires human support',
            'author_email': ticket_summary.get('author_email', 'Not available')
        }

    def analyze_all_tickets(self, ticket_summaries: List[Dict]) -> Dict:
        """Analyze all tickets for patterns and diagnostics opportunities"""
        
        # Initialize counters
        category_counts = Counter()
        resolution_type_counts = Counter()
        diagnostics_compatible = []
        complex_issues = []
        
        # Process each ticket
        for ticket in ticket_summaries:
            # Count categories and resolution types
            category_counts[ticket['derived_category']] += 1
            resolution_type_counts[ticket['resolution_type']] += 1
            
            # Check diagnostics compatibility
            compatibility = self.check_diagnostics_compatibility(ticket)
            
            if compatibility['is_diagnostics_compatible']:
                diagnostics_compatible.append(compatibility)
            elif ticket['comment_count'] > 5:
                complex_issues.append({
                    'ticket_id': ticket['ticket_id'],
                    'issue': ticket['issue_summary'],
                    'comment_count': ticket['comment_count']
                })
        
        # Calculate statistics
        total_tickets = len(ticket_summaries)
        diagnostics_percentage = (len(diagnostics_compatible) / total_tickets * 100) if total_tickets > 0 else 0
        
        return {
            'summary': {
                'total_tickets': total_tickets,
                'diagnostics_compatible_count': len(diagnostics_compatible),
                'diagnostics_compatible_percentage': f"{diagnostics_percentage:.1f}%",
                'complex_issues_count': len(complex_issues)
            },
            'category_distribution': dict(category_counts),
            'resolution_type_distribution': dict(resolution_type_counts),
            'diagnostics_compatible_tickets': diagnostics_compatible,
            'complex_issues': complex_issues,
            'recommendations': self._generate_recommendations(
                dict(category_counts), 
                diagnostics_compatible,
                diagnostics_percentage
            )
        }

    def _generate_recommendations(self, category_distribution: Dict, 
                                 compatible_tickets: List[Dict], 
                                 compatibility_percentage: float) -> List[Dict]:
        """Generate specific recommendations for diagnostics improvements"""
        recommendations = []
        
        # Top categories recommendation
        top_categories = sorted(
            category_distribution.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        recommendations.append({
            'type': 'Focus Area',
            'recommendation': f"Prioritize diagnostics for: {', '.join([cat[0] for cat in top_categories])}",
            'reason': 'These are the most common issue categories'
        })
        
        # High impact recommendation
        if compatibility_percentage > 50:
            recommendations.append({
                'type': 'High Impact',
                'recommendation': 'Diagnostics could potentially resolve majority of tickets automatically',
                'reason': f"{compatibility_percentage:.1f}% of tickets match diagnostics patterns"
            })
        
        # Pattern-specific recommendations
        all_patterns = []
        for ticket in compatible_tickets:
            for check_name, is_true in ticket['checks'].items():
                if is_true and check_name not in ['requires_code_change', 'requires_human_analysis']:
                    all_patterns.append(check_name)
        
        pattern_counts = Counter(all_patterns)
        for pattern, count in pattern_counts.most_common(3):
            recommendations.append({
                'type': 'Feature Enhancement',
                'recommendation': f"Enhance diagnostics for '{pattern.replace('_', ' ')}' issues",
                'reason': f"Appears in {count} compatible tickets"
            })
        
        return recommendations


# ============================================================================
# SECTION 4: MAIN ORCHESTRATOR
# ============================================================================

class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class WhatfixTicketAnalyzer:
    """Main class that orchestrates the entire ticket analysis process"""
    
    def __init__(self, llm_provider: str = 'mock', api_key: Optional[str] = None):
        """
        Initialize the analyzer with specified LLM provider
        
        Args:
            llm_provider: 'openai', 'anthropic', or 'mock'
            api_key: API key for the LLM provider (not needed for mock)
        """
        # Initialize LLM provider
        if llm_provider == 'openai':
            if not api_key:
                api_key = os.environ.get('OPENAI_API_KEY')
            self.llm_provider = OpenAIProvider(api_key)
        elif llm_provider == 'anthropic':
            if not api_key:
                api_key = os.environ.get('ANTHROPIC_API_KEY')
            self.llm_provider = AnthropicProvider(api_key)
        elif llm_provider == 'gemini':
            if not api_key:
                api_key = os.environ.get('GOOGLE_API_KEY')
            self.llm_provider = GeminiAIProvider(api_key)
        else:
            self.llm_provider = MockProvider()
        
        # Initialize components
        self.processor = TicketProcessor(self.llm_provider)
        self.diagnostics_analyzer = DiagnosticsAnalyzer()
        
        logger.info(f"Initialized WhatfixTicketAnalyzer with {llm_provider} provider")

    def analyze_csv(self, csv_path: str, output_dir: Optional[str] = None) -> Dict:
        """
        Main method to analyze a CSV file of support tickets
        
        Args:
            csv_path: Path to the CSV file
            output_dir: Optional directory to save results
            
        Returns:
            Dictionary containing complete analysis results
        """
        logger.info(f"Starting analysis of {csv_path}")
        
        # Validate CSV exists
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Read and validate CSV
        df = pd.read_csv(csv_path)
        self._validate_csv_columns(df)
        
        # Clean data
        df = self._clean_dataframe(df)
        
        # Process tickets
        ticket_summaries = self._process_all_tickets(df)
        
        # Analyze for diagnostics compatibility
        diagnostics_analysis = self.diagnostics_analyzer.analyze_all_tickets(ticket_summaries)
        
        # Compile final results
        results = {
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'file_path': csv_path,
                'llm_provider': type(self.llm_provider).__name__,
                'total_raw_rows': len(df),
                'unique_tickets': len(df['Zendesk Tickets ID'].unique())
            },
            'ticket_summaries': ticket_summaries,
            'diagnostics_analysis': diagnostics_analysis,
            'author_outreach_list': self._compile_outreach_list(
                ticket_summaries, 
                diagnostics_analysis['diagnostics_compatible_tickets']
            )
        }
        
        # Save results if output directory specified
        if output_dir:
            self._save_results(results, output_dir)
        
        logger.info("Analysis complete!")
        return results

    def _validate_csv_columns(self, df: pd.DataFrame):
        """Validate required columns exist"""
        required_columns = [
            'Zendesk Tickets ID',
            'Zendesk Comments ID', 
            'Zendesk Comments Body',
            'Zendesk Tickets Ent ID',
            'Zendesk Tickets Subject'
        ]
        
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the dataframe"""
        # Handle missing values
        df['Zendesk Comments Body'] = df['Zendesk Comments Body'].fillna('')
        df['Zendesk Tickets Subject'] = df['Zendesk Tickets Subject'].fillna('No Subject')
        df['Zendesk Tickets Root Cause'] = df['Zendesk Tickets Root Cause'].fillna('Not Specified')
        
        # Remove duplicate comment IDs
        df = df.drop_duplicates(subset=['Zendesk Comments ID'], keep='first')
        
        # Convert IDs to integers
        df['Zendesk Tickets ID'] = pd.to_numeric(df['Zendesk Tickets ID'], errors='coerce')
        df['Zendesk Comments ID'] = pd.to_numeric(df['Zendesk Comments ID'], errors='coerce')
        
        # Remove invalid rows
        df = df.dropna(subset=['Zendesk Tickets ID', 'Zendesk Comments ID'])
        
        return df

    def _process_all_tickets(self, df: pd.DataFrame) -> List[Dict]:
        """Process all tickets in the dataframe"""
        # Group by ticket ID
        grouped = df.groupby('Zendesk Tickets ID')
        
        summaries = []
        total_tickets = len(grouped)
        
        for i, (ticket_id, ticket_comments) in enumerate(grouped):
            logger.info(f"Processing ticket {i+1}/{total_tickets}: {ticket_id}")
            
            # Process comments
            ticket_data = self.processor.process_ticket_comments(ticket_comments)
            
            # Summarize with LLM
            summary = self.processor.summarize_ticket(ticket_data)
            
            # Try to extract author email from comments
            summary['author_email'] = self._extract_author_email(ticket_comments)
            
            summaries.append(summary)
        
        return summaries

    def _extract_author_email(self, ticket_df: pd.DataFrame) -> str:
        """Extract author email from ticket comments"""
        for _, row in ticket_df.iterrows():
            body = str(row['Zendesk Comments Body'])
            # Look for email pattern
            email_match = re.search(r'Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', body)
            if email_match:
                return email_match.group(1)
        return 'Not available'

    def _compile_outreach_list(self, summaries: List[Dict], compatible_tickets: List[Dict]) -> List[Dict]:
        """Compile list of authors to reach out to about diagnostics"""
        outreach_list = []
        compatible_ids = {t['ticket_id'] for t in compatible_tickets}
        print("Printing summaries from compile_outreach_list method")
        print(summaries)
        for summary in summaries:
            if summary['ticket_id'] in compatible_ids and summary['author_email'] != 'Not available':
                outreach_list.append({
                    'ticket_id': summary['ticket_id'],
                    'author_email': summary['author_email'],
                    'issue_summary': summary['issue_summary'],
                    'resolution_summary': summary['resolution_summary'],
                    'derived_category': summary['derived_category'],
                    'resolution_type': summary['resolution_type'],
                    'could_use_diagnostics': True
                })
        
        return outreach_list

    def _save_results(self, results: Dict, output_dir: str):
        """Save analysis results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete results
        results_file = output_path / f'ticket_analysis_{timestamp}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, cls=NumpyEncoder)
        logger.info(f"Saved complete results to {results_file}")
        
        # Save summary report
        report = {
            'summary': results['diagnostics_analysis']['summary'],
            'recommendations': results['diagnostics_analysis']['recommendations'],
            'author_outreach_count': len(results['author_outreach_list'])
        }
        
        report_file = output_path / f'summary_report_{timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, cls=NumpyEncoder)
        logger.info(f"Saved summary report to {report_file}")
        
        # Save outreach list as CSV for easy use
        if results['author_outreach_list']:
            outreach_df = pd.DataFrame(results['author_outreach_list'])
            outreach_file = output_path / f'diagnostics_outreach_{timestamp}.csv'
            outreach_df.to_csv(outreach_file, index=False)
            logger.info(f"Saved outreach list to {outreach_file}")


# ============================================================================
# SECTION 5: EXAMPLE USAGE AND TESTING
# ============================================================================

def main():
    """Example usage of the WhatfixTicketAnalyzer"""
    
    print("=== Whatfix Support Ticket Analyzer ===\n")
    
    # Initialize analyzer (using mock provider for demonstration)
    analyzer = WhatfixTicketAnalyzer(llm_provider='gemini')
    
    # Analyze the CSV file
    try:
        results = analyzer.analyze_csv(
            csv_path='/Users/reehanahmed/Downloads/zendesk_reselection_tickets_limited.csv',
            output_dir='ticket_analysis_output'
        )
        
        # Print summary
        print("\n=== Analysis Summary ===")
        print(f"Total tickets analyzed: {results['diagnostics_analysis']['summary']['total_tickets']}")
        print(f"Diagnostics compatible: {results['diagnostics_analysis']['summary']['diagnostics_compatible_count']} "
              f"({results['diagnostics_analysis']['summary']['diagnostics_compatible_percentage']})")
        print(f"Complex issues: {results['diagnostics_analysis']['summary']['complex_issues_count']}")
        
        # Print top categories
        print("\n=== Top Issue Categories ===")
        categories = results['diagnostics_analysis']['category_distribution']
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"- {category}: {count} tickets")
        
        # Print recommendations
        print("\n=== Diagnostics Recommendations ===")
        for i, rec in enumerate(results['diagnostics_analysis']['recommendations'], 1):
            print(f"\n{i}. {rec['type']}: {rec['recommendation']}")
            print(f"   Reason: {rec['reason']}")
        
        # Print sample compatible ticket
        if results['diagnostics_analysis']['diagnostics_compatible_tickets']:
            sample = results['diagnostics_analysis']['diagnostics_compatible_tickets'][0]
            print("\n=== Sample Diagnostics-Compatible Ticket ===")
            print(f"Ticket ID: {sample['ticket_id']}")
            print(f"Compatibility Score: {sample['compatibility_score']}")
            print(f"Recommendation: {sample['recommendation']}")
        
        # Print outreach summary
        print(f"\n=== Author Outreach ===")
        print(f"Authors to contact about diagnostics: {len(results['author_outreach_list'])}")
        
        print("\n✓ Analysis complete! Check 'ticket_analysis_output' directory for detailed results.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()