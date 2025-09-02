from fuzzywuzzy import fuzz
from typing import List, Dict, Any, Tuple, Callable
import pandas as pd
import numpy as np
from jellyfish import jaro_winkler_similarity, soundex, metaphone
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine
import re

class FuzzyMatcher:
    """
    Enhanced fuzzy matching engine with multiple algorithms and scoring methods.
    """
    def __init__(self, algorithm: str = 'ratio', threshold: float = 80, max_matches: int = 5):
        """
        Initialize the FuzzyMatcher with configurable parameters.
        
        Args:
            algorithm: The fuzzy matching algorithm to use
            threshold: Minimum score threshold (0-100)
            max_matches: Maximum number of matches to return per record
        """
        self.algorithm = algorithm
        self.threshold = threshold
        self.max_matches = max_matches
        self._initialize_algorithms()
        # Initialize TF-IDF vectorizer once
        self.vectorizer = TfidfVectorizer(lowercase=True)
        
    def _initialize_algorithms(self):
        """Initialize the mapping of algorithm names to their implementations."""
        self._algorithm_map = {
            # Main algorithms
            'levenshtein': fuzz.ratio,
            'jaro_winkler': self._jaro_winkler_similarity,
            'jaccard': self._jaccard_similarity,
            'cosine': self._cosine_similarity,
            'soundex': self._soundex_similarity,
            'weighted': self.calculate_weighted_algorithms,
            
            # Additional FuzzyWuzzy algorithms
            'partial_ratio': fuzz.partial_ratio,
            'token_sort_ratio': fuzz.token_sort_ratio,
            'token_set_ratio': fuzz.token_set_ratio,
            'token_set_partial': fuzz.partial_token_set_ratio,
            'token_sort_partial': fuzz.partial_token_sort_ratio,
            
            # Custom implementations
            'ngram': self._ngram_similarity,
            'hybrid': self._hybrid_similarity
        }
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-100 range."""
        return min(100, max(0, score * 100))

    def _jaro_winkler_similarity(self, str1: str, str2: str) -> float:
        """Calculate Jaro-Winkler similarity between two strings."""
        return self._normalize_score(jaro_winkler_similarity(str1, str2))

    def _soundex_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity using Soundex phonetic algorithm with enhanced matching."""
        try:
            # Split into words and get best match for multi-word strings
            words1 = str(str1).lower().split()
            words2 = str(str2).lower().split()
            
            if not words1 or not words2:
                return 0.0
                
            # Calculate soundex codes for each word
            codes1 = [soundex(w) for w in words1 if w]
            codes2 = [soundex(w) for w in words2 if w]
            
            # If any codes match exactly, count as high similarity
            if any(c1 == c2 for c1 in codes1 for c2 in codes2):
                return 100.0
                
            # For partial matches, calculate similarity based on shared prefixes
            total_score = 0
            count = 0
            
            for c1 in codes1:
                for c2 in codes2:
                    # Calculate how many characters match from the start
                    match_length = 0
                    for i in range(min(len(c1), len(c2))):
                        if c1[i] == c2[i]:
                            match_length += 1
                        else:
                            break
                    # Score based on matching prefix length
                    score = (match_length / max(len(c1), len(c2))) * 100
                    total_score += score
                    count += 1
            
            return total_score / count if count > 0 else 0.0
        except:
            return 0.0

    def _metaphone_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity using Metaphone phonetic algorithm."""
        try:
            return 100 if metaphone(str1) == metaphone(str2) else 0
        except:
            return 0

    def _get_word_set(self, text: str) -> set:
        """Convert text to set of words."""
        return set(re.findall(r'\w+', text.lower()))

    def _jaccard_similarity(self, str1: str, str2: str) -> float:
        """Calculate Jaccard similarity between two strings."""
        try:
            # Convert to strings and normalize
            str1 = str(str1).lower().strip()
            str2 = str(str2).lower().strip()
            
            # Handle exact matches
            if str1 == str2:
                return 100.0
                
            # Clean and tokenize strings
            # Remove punctuation and split on whitespace
            words1 = set(re.findall(r'\w+', str1))
            words2 = set(re.findall(r'\w+', str2))
            
            if not words1 or not words2:
                return 0.0
                
            # Calculate intersection and union
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            # Calculate base Jaccard similarity score with a boost
            base_score = (intersection / union if union > 0 else 0) * 100
            
            # Boost the base score for significant word overlap
            if intersection > 0:
                # Boost based on percentage of matching words
                boost = (intersection / min(len(words1), len(words2))) * 30
                base_score = min(100, base_score + boost)
            
            # Look for partial matches even if we have some exact matches
            for word1 in words1:
                for word2 in words2:
                    # Check if words are substrings of each other
                    if len(word1) >= 3 and len(word2) >= 3:  # Only consider words of 3+ chars
                        if word1 in word2 or word2 in word1:
                            base_score = max(base_score, 70.0)  # Higher boost for partial matches
                        elif len(word1) > 4 and len(word2) > 4:
                            # For longer words, check character overlap
                            overlap = len(set(word1) & set(word2))
                            if overlap >= 3:  # If at least 3 characters match
                                overlap_ratio = overlap / max(len(word1), len(word2))
                                if overlap_ratio > 0.6:  # Reduced threshold
                                    base_score = max(base_score, 60.0)
            
            return base_score
        except:
            return 0.0

    def _cosine_similarity(self, str1: str, str2: str) -> float:
        """Calculate Cosine similarity between two strings using TF-IDF."""
        try:
            # Convert to strings and normalize
            str1 = str(str1).lower().strip()
            str2 = str(str2).lower().strip()
            
            # Handle exact matches
            if str1 == str2:
                return 100.0
                
            # Skip empty strings
            if not str1 or not str2:
                return 0.0
                
            # Clean and tokenize strings
            words1 = re.findall(r'\w+', str1)
            words2 = re.findall(r'\w+', str2)
            
            if not words1 or not words2:
                return 0.0
                
            # Create word frequency dictionaries
            word_freq1 = {}
            word_freq2 = {}
            
            # Calculate word frequencies
            unique_words = set(words1 + words2)
            for word in unique_words:
                # Add tf-idf like weighting - longer words get higher weight
                word_weight = 1.0 + (len(word) / 10.0 if len(word) > 3 else 0)
                word_freq1[word] = words1.count(word) * word_weight
                word_freq2[word] = words2.count(word) * word_weight
            
            # Calculate dot product and magnitudes
            dot_product = sum(word_freq1.get(word, 0) * word_freq2.get(word, 0) 
                            for word in unique_words)
            
            magnitude1 = (sum(freq * freq for freq in word_freq1.values())) ** 0.5
            magnitude2 = (sum(freq * freq for freq in word_freq2.values())) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            # Calculate base cosine similarity score
            base_score = (dot_product / (magnitude1 * magnitude2)) * 100
            
            # Enhanced partial matching
            if base_score < 30:  # Lower threshold for partial matching
                max_partial_score = 0
                for word1 in words1:
                    for word2 in words2:
                        if len(word1) >= 3 and len(word2) >= 3:
                            # Direct substring match
                            if word1 in word2 or word2 in word1:
                                max_partial_score = max(max_partial_score, 50.0)
                            # Character overlap for longer words
                            elif len(word1) > 4 and len(word2) > 4:
                                overlap = len(set(word1) & set(word2))
                                overlap_ratio = overlap / max(len(word1), len(word2))
                                if overlap_ratio > 0.7:
                                    max_partial_score = max(max_partial_score, 40.0)
                
                base_score = max(base_score, max_partial_score)
            
            return base_score
        except:
            return 0.0

    def _ngram_similarity(self, str1: str, str2: str, n: int = 2) -> float:
        """Calculate n-gram similarity between two strings."""
        def get_ngrams(text: str, n: int) -> set:
            return set(text[i:i+n] for i in range(len(text)-n+1))
        
        # Get n-grams
        ngrams1 = get_ngrams(str1.lower(), n)
        ngrams2 = get_ngrams(str2.lower(), n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
            
        # Calculate Dice coefficient
        intersection = len(ngrams1.intersection(ngrams2))
        total = len(ngrams1) + len(ngrams2)
        
        return self._normalize_score((2 * intersection) / total if total > 0 else 0)

    def _hybrid_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate hybrid similarity using multiple algorithms.
        Combines string similarity with phonetic matching.
        """
        # Calculate various similarity scores
        ratio_score = fuzz.ratio(str1, str2)
        jaro_score = self._jaro_winkler_similarity(str1, str2)
        token_score = fuzz.token_sort_ratio(str1, str2)
        
        # Check for phonetic matches
        phonetic_match = self._soundex_similarity(str1, str2) > 0 or \
                        self._metaphone_similarity(str1, str2) > 0
                        
        # Weight the scores (can be adjusted)
        weighted_score = (0.4 * ratio_score + 
                        0.3 * jaro_score + 
                        0.3 * token_score)
                        
        # Boost score if there's a phonetic match
        if phonetic_match:
            weighted_score = min(100, weighted_score * 1.2)
            
        return weighted_score

    def calculate_weighted_algorithms(self, str1: str, str2: str, algorithm_weights: Dict[str, float]) -> float:
        """
        Calculate similarity using weighted combination of specified algorithms.
        
        Args:
            str1: First string to compare
            str2: Second string to compare
            algorithm_weights: Dictionary mapping algorithm names to their weights
            
        Returns:
            Weighted similarity score (0-100)
        """
        try:
            # Early exit for empty strings
            if not str1 or not str2:
                return 0.0

            # Convert inputs to strings and normalize
            str1, str2 = str(str1).strip(), str(str2).strip()
            
            # Quick exact match check
            if str1 == str2:
                return 100.0

            # Calculate Levenshtein first as it's typically fastest
            if algorithm_weights.get('levenshtein', 0) > 0:
                lev_score = fuzz.ratio(str1, str2)
                # Early exit if perfect match found
                if lev_score == 100:
                    return 100.0
                # Early exit if score too low
                if lev_score < 30:  # Threshold for early termination
                    return lev_score
            
            scores = {}
            total_weight = 0.0
            
            # Sort algorithms by speed (fastest first)
            ordered_algorithms = [
                ('levenshtein', fuzz.ratio),
                ('jaro_winkler', self._jaro_winkler_similarity),
                ('soundex', self._soundex_similarity),
                ('jaccard', self._jaccard_similarity),
                ('cosine', self._cosine_similarity)
            ]
            
            # Only process algorithms with weights > 0
            for algo_name, algo_func in ordered_algorithms:
                weight = algorithm_weights.get(algo_name, 0)
                if weight > 0:
                    score = algo_func(str1, str2)
                    if score > 0:  # Only include non-zero scores
                        scores[algo_name] = score * weight
                        total_weight += weight
            
            if total_weight == 0:
                return 0.0
            
            return sum(scores.values()) / total_weight
        except:
            return 0.0

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings."""
        if not str1 or not str2:
            return 0.0
            
        try:
            if self.algorithm == 'weighted':
                # For weighted algorithm, get the current weights from the instance
                algorithm_weights = getattr(self, 'algorithm_weights', {
                    'levenshtein': 1.0,
                    'jaro_winkler': 1.0,
                    'jaccard': 1.0,
                    'cosine': 1.0,
                    'soundex': 1.0
                })
                return self._algorithm_map[self.algorithm](str1, str2, algorithm_weights)
            return self._algorithm_map[self.algorithm](str1, str2)
        except KeyError:
            # Fallback to Levenshtein if algorithm not found
            return self._algorithm_map['levenshtein'](str1, str2)

    def _calculate_weighted_score(self, record1: Dict[str, str], 
                                record2: Dict[str, str], 
                                weights: Dict[str, float]) -> float:
        """Calculate weighted similarity score across multiple fields."""
        total_score = 0.0
        total_weight = sum(weights.values())
        field_scores = {}
        
        # First calculate individual field scores
        for field, weight in weights.items():
            if field in record1 and field in record2:
                field_score = self._calculate_similarity(str(record1[field]), str(record2[field]))
                field_scores[field] = field_score
                total_score += (field_score * weight)
        
        weighted_avg = total_score / total_weight if total_weight > 0 else 0.0
        
        # Special handling for address matching
        if 'address' in weights:
            address_score = field_scores.get('address', 0)
            # If address score is high enough, boost the overall score
            if address_score >= self.threshold:
                other_fields_match = True
                # Check if other fields (city, state) are reasonable matches (>50%)
                for field in ['city', 'state']:
                    if field in weights and field_scores.get(field, 0) < 50:
                        other_fields_match = False
                        break
                if other_fields_match:
                    # Boost the score based on strong address match
                    return max(weighted_avg, address_score * 0.9)
        
        return weighted_avg

    def find_matches(self, source_df: pd.DataFrame, 
                    reference_df: pd.DataFrame, 
                    weights: Dict[str, float]) -> pd.DataFrame:
        """
        Find matches between source and reference datasets.
        
        Args:
            source_df: DataFrame containing source records
            reference_df: DataFrame containing reference records
            weights: Dictionary mapping field names to their weights
        
        Returns:
            DataFrame containing matched records with scores
        """
        matches = []
        
        for idx, source_record in source_df.iterrows():
            record_matches = []
            
            for ref_idx, ref_record in reference_df.iterrows():
                score = self._calculate_weighted_score(
                    source_record.to_dict(),
                    ref_record.to_dict(),
                    weights
                )
                
                if score >= self.threshold:
                    record_matches.append((ref_idx, score))
            
            # Sort matches by score and take top N
            record_matches.sort(key=lambda x: x[1], reverse=True)
            top_matches = record_matches[:self.max_matches]
            
            # Add matches to results
            for ref_idx, score in top_matches:
                matches.append({
                    'source_index': idx,
                    'reference_index': ref_idx,
                    'score': score,
                    **{f'source_{k}': source_record[k] for k in weights.keys()},
                    **{f'reference_{k}': reference_df.loc[ref_idx, k] for k in weights.keys()}
                })
        
        return pd.DataFrame(matches)

    def compare_lists(self, list1: List[str], list2: List[str]) -> pd.DataFrame:
        """
        Compare two lists of strings and return similarity scores.
        
        Args:
            list1: First list of strings
            list2: Second list of strings
        
        Returns:
            DataFrame containing paired records with their similarity scores
        """
        if len(list1) != len(list2):
            raise ValueError("Lists must be of equal length")
        
        results = []
        for str1, str2 in zip(list1, list2):
            score = self._calculate_similarity(str1, str2)
            results.append({
                'string1': str1,
                'string2': str2,
                'score': score
            })
        
        return pd.DataFrame(results)
