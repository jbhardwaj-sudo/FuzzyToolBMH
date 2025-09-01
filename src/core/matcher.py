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
        """Calculate similarity using Soundex phonetic algorithm."""
        try:
            return 100 if soundex(str1) == soundex(str2) else 0
        except:
            return 0

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
        set1 = self._get_word_set(str1)
        set2 = self._get_word_set(str2)
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return self._normalize_score(intersection / union if union > 0 else 0)

    def _cosine_similarity(self, str1: str, str2: str) -> float:
        """Calculate Cosine similarity between two strings using TF-IDF."""
        try:
            vectorizer = TfidfVectorizer(lowercase=True)
            tfidf_matrix = vectorizer.fit_transform([str1, str2])
            similarity = 1 - cosine(tfidf_matrix.toarray()[0], tfidf_matrix.toarray()[1])
            return self._normalize_score(similarity)
        except:
            return 0

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
        scores = {
            'levenshtein': fuzz.ratio(str1, str2),
            'jaro_winkler': self._jaro_winkler_similarity(str1, str2),
            'jaccard': self._jaccard_similarity(str1, str2),
            'cosine': self._cosine_similarity(str1, str2),
            'soundex': self._soundex_similarity(str1, str2)
        }
        
        total_weight = sum(algorithm_weights.values())
        if total_weight == 0:
            return 0.0
            
        weighted_sum = sum(
            scores[algo] * weight 
            for algo, weight in algorithm_weights.items() 
            if algo in scores
        )
        
        return weighted_sum / total_weight

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
        
        for field, weight in weights.items():
            if field in record1 and field in record2:
                field_score = self._calculate_similarity(str(record1[field]), str(record2[field]))
                total_score += (field_score * weight)
        
        return total_score / total_weight if total_weight > 0 else 0.0

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
