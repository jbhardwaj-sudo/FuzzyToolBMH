from typing import Dict, Any, List

class AlgorithmWeights:
    """Class to manage algorithm weights for advanced hybrid matching"""
    
    def __init__(self):
        self._weights = {
            'levenshtein': 1.0,  # Basic edit distance
            'jaro_winkler': 1.0,  # Good for names
            'jaccard': 1.0,      # Word overlap
            'cosine': 1.0,       # Semantic similarity
            'soundex': 1.0       # Phonetic similarity
        }
        self._descriptions = {
            'levenshtein': "The Edit Counter - Best for typos and spelling mistakes",
            'jaro_winkler': "The Name Specialist - Best for person names and brands",
            'jaccard': "The Word Overlap Expert - Best for addresses and descriptions",
            'cosine': "The Context Understanding Master - Best for long text",
            'soundex': "The Sound-Alike Detective - Best for phonetic matches"
        }

    @property
    def algorithms(self) -> List[str]:
        """Get list of available algorithms"""
        return list(self._weights.keys())

    @property
    def descriptions(self) -> Dict[str, str]:
        """Get algorithm descriptions"""
        return self._descriptions.copy()

    def set_weight(self, algorithm: str, weight: float) -> None:
        """Set weight for a specific algorithm"""
        if algorithm not in self._weights:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        if weight < 0:
            raise ValueError("Weight must be non-negative")
        self._weights[algorithm] = weight

    def get_weight(self, algorithm: str) -> float:
        """Get weight for a specific algorithm"""
        return self._weights.get(algorithm, 0.0)

    def get_weights(self) -> Dict[str, float]:
        """Get all weights"""
        return self._weights.copy()
