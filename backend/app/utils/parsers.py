"""
Text parsing utilities for extracting entities from user messages.

This module handles parsing of dates, team names, amounts, and other
entities from natural language input. It's designed to work alongside
our intent classification to extract structured data from user queries.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal

from ..core.logging import get_logger

logger = get_logger(__name__)


class EntityExtractor:
    """
    Extract structured entities from natural language text.
    
    This class handles parsing of common entities like dates, amounts,
    team names, and betting terms from user messages. It's designed to
    work with our sports betting domain.
    """
    
    def __init__(self):
        # Common team name patterns and aliases
        self.team_aliases = {
            "barca": "barcelona",
            "real": "real madrid", 
            "man u": "manchester united",
            "man city": "manchester city",
            "psg": "paris saint-germain",
            "bayern": "bayern munich",
            "juve": "juventus",
            "arsenal": "arsenal",
            "chelsea": "chelsea",
            "liverpool": "liverpool"
        }
        
        # Betting terms and their normalized forms
        self.betting_terms = {
            "1x2": "match_winner",
            "match winner": "match_winner",
            "win": "match_winner",
            "draw": "draw",
            "tie": "draw",
            "over": "over_under",
            "under": "over_under",
            "btts": "both_teams_score",
            "both teams to score": "both_teams_score",
            "handicap": "handicap",
            "spread": "handicap"
        }
        
        # Time-related patterns
        self.time_patterns = {
            "today": 0,
            "tomorrow": 1,
            "yesterday": -1,
            "this weekend": (5, 6),  # Saturday, Sunday
            "next week": 7,
            "tonight": 0
        }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from text.
        
        Returns a dictionary with extracted entities organized by type.
        """
        text_lower = text.lower()
        
        entities = {
            "amounts": self.extract_amounts(text),
            "dates": self.extract_dates(text_lower),
            "teams": self.extract_teams(text_lower),
            "betting_terms": self.extract_betting_terms(text_lower),
            "numbers": self.extract_numbers(text),
            "time_references": self.extract_time_references(text_lower)
        }
        
        # Remove empty lists
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from text."""
        amounts = []
        
        # Pattern for amounts with currency symbols
        currency_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $100, $50.00
            r'(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)',  # 100 dollars, 50 USD
            r'(\d+(?:\.\d{2})?)\s*(?:euros?|eur|€)',  # 100 euros, 50 EUR
            r'(\d+(?:\.\d{2})?)\s*(?:pounds?|gbp|£)',  # 100 pounds, 50 GBP
        ]
        
        for pattern in currency_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1) if match.group(1) else match.group(0)[1:]  # Remove currency symbol
                try:
                    amount = Decimal(amount_str)
                    currency = self._detect_currency(match.group(0))
                    amounts.append({
                        "amount": float(amount),
                        "currency": currency,
                        "raw_text": match.group(0)
                    })
                except (ValueError, IndexError):
                    continue
        
        return amounts
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract date references from text."""
        dates = []
        today = date.today()
        
        # Absolute date patterns
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',  # 12/31/2023, 31-12-23
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})',  # 31 Dec 2023
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4})',  # Dec 31, 2023
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    dates.append({
                        "date": parsed_date.isoformat(),
                        "relative_days": (parsed_date - today).days,
                        "raw_text": date_str
                    })
        
        # Relative date patterns
        for phrase, offset in self.time_patterns.items():
            if phrase in text:
                if isinstance(offset, tuple):
                    # Weekend case
                    days_until_saturday = (5 - today.weekday()) % 7
                    saturday = today + timedelta(days=days_until_saturday)
                    sunday = saturday + timedelta(days=1)
                    dates.extend([
                        {
                            "date": saturday.isoformat(),
                            "relative_days": (saturday - today).days,
                            "raw_text": phrase
                        },
                        {
                            "date": sunday.isoformat(),
                            "relative_days": (sunday - today).days,
                            "raw_text": phrase
                        }
                    ])
                else:
                    target_date = today + timedelta(days=offset)
                    dates.append({
                        "date": target_date.isoformat(),
                        "relative_days": offset,
                        "raw_text": phrase
                    })
        
        return dates
    
    def extract_teams(self, text: str) -> List[Dict[str, Any]]:
        """Extract team names from text."""
        teams = []
        
        # Check for team aliases first
        for alias, full_name in self.team_aliases.items():
            if alias in text:
                teams.append({
                    "name": full_name,
                    "alias": alias,
                    "confidence": 0.9
                })
        
        # Look for potential team names (capitalized words)
        team_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.finditer(team_pattern, text.title())
        
        for match in matches:
            team_name = match.group(1)
            # Skip common non-team words
            if team_name.lower() not in ['the', 'and', 'or', 'but', 'when', 'what', 'where', 'who']:
                teams.append({
                    "name": team_name.lower(),
                    "confidence": 0.6,
                    "raw_text": team_name
                })
        
        return teams
    
    def extract_betting_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract betting-related terms from text."""
        betting_terms = []
        
        for term, normalized in self.betting_terms.items():
            if term in text:
                betting_terms.append({
                    "term": normalized,
                    "raw_text": term,
                    "confidence": 0.8
                })
        
        return betting_terms
    
    def extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """Extract numbers from text (not amounts)."""
        numbers = []
        
        # Integer and decimal patterns
        number_patterns = [
            r'\b(\d+\.\d+)\b',  # Decimals like 2.5, 1.75
            r'\b(\d+)\b'        # Integers
        ]
        
        for pattern in number_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                number_str = match.group(1)
                try:
                    if '.' in number_str:
                        number = float(number_str)
                    else:
                        number = int(number_str)
                    
                    numbers.append({
                        "value": number,
                        "type": "float" if '.' in number_str else "int",
                        "raw_text": number_str
                    })
                except ValueError:
                    continue
        
        return numbers
    
    def extract_time_references(self, text: str) -> List[str]:
        """Extract time-related references."""
        time_refs = []
        
        time_keywords = [
            "today", "tomorrow", "yesterday", "tonight", "this evening",
            "this weekend", "next week", "this week", "next month",
            "morning", "afternoon", "evening", "night"
        ]
        
        for keyword in time_keywords:
            if keyword in text:
                time_refs.append(keyword)
        
        return time_refs
    
    def _detect_currency(self, amount_text: str) -> str:
        """Detect currency from amount text."""
        amount_lower = amount_text.lower()
        
        if '$' in amount_text or 'dollar' in amount_lower or 'usd' in amount_lower:
            return 'USD'
        elif '€' in amount_text or 'euro' in amount_lower or 'eur' in amount_lower:
            return 'EUR'
        elif '£' in amount_text or 'pound' in amount_lower or 'gbp' in amount_lower:
            return 'GBP'
        else:
            return 'USD'  # Default
    
    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse various date string formats."""
        date_formats = [
            '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
            '%m/%d/%y', '%d/%m/%y', '%m-%d-%y', '%d-%m-%y',
            '%d %b %Y', '%b %d, %Y', '%B %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None


# Global entity extractor instance
_entity_extractor: Optional[EntityExtractor] = None


def get_entity_extractor() -> EntityExtractor:
    """Get global entity extractor instance."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor


def extract_entities_from_text(text: str) -> Dict[str, Any]:
    """Convenience function to extract entities from text."""
    extractor = get_entity_extractor()
    return extractor.extract_entities(text)