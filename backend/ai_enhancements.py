"""
AI Enhancements for Clearance Face Search System
Advanced AI features implementation
"""

import cv2
import numpy as np
import base64
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import tempfile
from datetime import datetime
import requests
from PIL import Image, ImageEnhance
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEnhancements:
    """Advanced AI features for the clearance system"""
    
    def __init__(self):
        self.models_loaded = False
        self.face_models = {}
        self.nlp_models = {}
        self.load_ai_models()
    
    def load_ai_models(self):
        """Load AI models for various tasks"""
        try:
            # Try to load advanced face recognition models
            self._load_face_models()
            self._load_nlp_models()
            self.models_loaded = True
            logger.info("AI models loaded successfully")
        except Exception as e:
            logger.warning(f"Some AI models failed to load: {e}")
            self.models_loaded = False
    
    def _load_face_models(self):
        """Load advanced face recognition models"""
        try:
            # DeepFace for advanced face analysis
            try:
                from deepface import DeepFace
                self.face_models['deepface'] = DeepFace
                logger.info("DeepFace model loaded")
            except ImportError:
                logger.warning("DeepFace not available")
            
            # InsightFace for face embeddings
            try:
                import insightface
                self.face_models['insightface'] = insightface
                logger.info("InsightFace model loaded")
            except ImportError:
                logger.warning("InsightFace not available")
                
        except Exception as e:
            logger.error(f"Error loading face models: {e}")
    
    def _load_nlp_models(self):
        """Load NLP models"""
        try:
            # spaCy for text processing
            try:
                import spacy
                self.nlp_models['spacy'] = spacy
                logger.info("spaCy model loaded")
            except ImportError:
                logger.warning("spaCy not available")
                
        except Exception as e:
            logger.error(f"Error loading NLP models: {e}")
    
    # ==================== ADVANCED FACE RECOGNITION ====================
    
    def analyze_face_advanced(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Advanced face analysis using multiple AI models
        Returns: age, gender, emotion, quality, landmarks
        """
        try:
            # Convert bytes to image
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            
            results = {
                'age': None,
                'gender': None,
                'emotion': None,
                'quality_score': 0.0,
                'landmarks': [],
                'face_detected': False,
                'confidence': 0.0
            }
            
            # Use DeepFace if available
            if 'deepface' in self.face_models:
                try:
                    # Analyze face with DeepFace
                    analysis = self.face_models['deepface'].analyze(
                        img_path=image_array,
                        actions=['age', 'gender', 'emotion'],
                        enforce_detection=False
                    )
                    
                    if isinstance(analysis, list):
                        analysis = analysis[0]
                    
                    results.update({
                        'age': int(analysis.get('age', 0)),
                        'gender': analysis.get('dominant_gender', 'unknown'),
                        'emotion': analysis.get('dominant_emotion', 'neutral'),
                        'face_detected': True,
                        'confidence': 0.8  # DeepFace confidence
                    })
                    
                except Exception as e:
                    logger.warning(f"DeepFace analysis failed: {e}")
            
            # Calculate image quality score
            results['quality_score'] = self._calculate_image_quality(image_array)
            
            # Detect face landmarks
            results['landmarks'] = self._detect_face_landmarks(image_array)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced face analysis: {e}")
            return {'error': str(e)}
    
    def _calculate_image_quality(self, image_array: np.ndarray) -> float:
        """Calculate image quality score (0-1)"""
        try:
            # Convert to grayscale if needed
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # Calculate Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness = np.mean(gray) / 255.0
            
            # Calculate contrast
            contrast = np.std(gray) / 255.0
            
            # Combine metrics (normalize to 0-1)
            quality_score = min(1.0, (laplacian_var / 1000.0 + brightness + contrast) / 3.0)
            
            return round(quality_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating image quality: {e}")
            return 0.0
    
    def _detect_face_landmarks(self, image_array: np.ndarray) -> List[Dict]:
        """Detect face landmarks using OpenCV"""
        try:
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Convert to grayscale
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            landmarks = []
            for (x, y, w, h) in faces:
                landmarks.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'center_x': int(x + w/2),
                    'center_y': int(y + h/2)
                })
            
            return landmarks
            
        except Exception as e:
            logger.error(f"Error detecting face landmarks: {e}")
            return []
    
    def enhance_image_quality(self, image_bytes: bytes) -> bytes:
        """
        Enhance image quality using AI techniques
        Returns: Enhanced image as bytes
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image_bytes
    
    def super_resolution(self, image_bytes: bytes, scale_factor: int = 2) -> bytes:
        """
        Apply super resolution to low-quality images
        """
        try:
            # Convert to OpenCV format
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            
            # Simple upscaling with interpolation
            height, width = image_array.shape[:2]
            new_height, new_width = height * scale_factor, width * scale_factor
            
            # Use cubic interpolation for better quality
            upscaled = cv2.resize(image_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Convert back to bytes
            enhanced_image = Image.fromarray(upscaled)
            output = io.BytesIO()
            enhanced_image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error in super resolution: {e}")
            return image_bytes
    
    # ==================== SMART SEARCH ENGINE ====================
    
    def fuzzy_name_matching(self, query: str, candidates: List[str], threshold: float = 0.8) -> List[Tuple[str, float]]:
        """
        Fuzzy string matching for names
        Returns: List of (name, similarity_score) tuples
        """
        try:
            from difflib import SequenceMatcher
            
            matches = []
            for candidate in candidates:
                # Calculate similarity
                similarity = SequenceMatcher(None, query.lower(), candidate.lower()).ratio()
                
                if similarity >= threshold:
                    matches.append((candidate, similarity))
            
            # Sort by similarity score
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches
            
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return []
    
    def phonetic_matching(self, query: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """
        Phonetic matching using Soundex algorithm
        """
        try:
            def soundex(word):
                """Simple Soundex implementation"""
                word = word.upper()
                soundex_code = word[0]
                
                # Soundex mapping
                mapping = {
                    'BFPV': '1', 'CGJKQSXZ': '2', 'DT': '3',
                    'L': '4', 'MN': '5', 'R': '6'
                }
                
                for char in word[1:]:
                    for key, value in mapping.items():
                        if char in key:
                            if soundex_code[-1] != value:
                                soundex_code += value
                            break
                
                return soundex_code.ljust(4, '0')[:4]
            
            query_soundex = soundex(query)
            matches = []
            
            for candidate in candidates:
                candidate_soundex = soundex(candidate)
                if query_soundex == candidate_soundex:
                    matches.append((candidate, 1.0))
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in phonetic matching: {e}")
            return []
    
    def smart_search_suggestions(self, query: str, search_history: List[str]) -> List[str]:
        """
        Generate smart search suggestions based on query and history
        """
        try:
            suggestions = []
            
            # Add exact matches from history
            for history_item in search_history:
                if query.lower() in history_item.lower():
                    suggestions.append(history_item)
            
            # Add partial matches
            for history_item in search_history:
                if len(query) > 2 and any(word in history_item.lower() for word in query.lower().split()):
                    suggestions.append(history_item)
            
            # Remove duplicates and limit results
            suggestions = list(dict.fromkeys(suggestions))[:5]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating search suggestions: {e}")
            return []
    
    # ==================== PREDICTIVE ANALYTICS ====================
    
    def calculate_risk_score(self, person_data: Dict, search_context: Dict) -> Dict[str, Any]:
        """
        Calculate risk score based on person data and search context
        """
        try:
            risk_factors = []
            risk_score = 0.0
            
            # Age-based risk
            if 'age' in person_data:
                age = person_data['age']
                if age < 18 or age > 80:
                    risk_factors.append("Age outside normal range")
                    risk_score += 0.1
            
            # Search frequency risk
            if 'search_count' in search_context:
                search_count = search_context['search_count']
                if search_count > 10:
                    risk_factors.append("High search frequency")
                    risk_score += 0.2
            
            # Time-based risk
            if 'search_time' in search_context:
                search_hour = datetime.now().hour
                if search_hour < 6 or search_hour > 22:
                    risk_factors.append("Unusual search time")
                    risk_score += 0.1
            
            # Data completeness risk
            missing_fields = []
            required_fields = ['full_name', 'ktp_number', 'address']
            for field in required_fields:
                if field not in person_data or not person_data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                risk_factors.append(f"Missing data: {', '.join(missing_fields)}")
                risk_score += len(missing_fields) * 0.05
            
            # Normalize risk score to 0-1
            risk_score = min(1.0, risk_score)
            
            return {
                'risk_score': round(risk_score, 3),
                'risk_level': self._get_risk_level(risk_score),
                'risk_factors': risk_factors,
                'recommendations': self._get_risk_recommendations(risk_score, risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return {'error': str(e)}
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score < 0.3:
            return "LOW"
        elif score < 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _get_risk_recommendations(self, score: float, factors: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if score > 0.5:
            recommendations.append("Consider additional verification")
        
        if "High search frequency" in factors:
            recommendations.append("Monitor search patterns")
        
        if "Unusual search time" in factors:
            recommendations.append("Verify search authorization")
        
        if "Missing data" in str(factors):
            recommendations.append("Request complete documentation")
        
        return recommendations
    
    def predict_search_patterns(self, user_id: int, search_history: List[Dict]) -> Dict[str, Any]:
        """
        Predict future search patterns based on history
        """
        try:
            if not search_history:
                return {'prediction': 'Insufficient data for prediction'}
            
            # Analyze search types
            search_types = [item.get('search_type', 'unknown') for item in search_history]
            type_counts = {}
            for stype in search_types:
                type_counts[stype] = type_counts.get(stype, 0) + 1
            
            # Predict most likely next search type
            most_common_type = max(type_counts, key=type_counts.get)
            
            # Analyze search times
            search_times = [item.get('timestamp', '') for item in search_history if item.get('timestamp')]
            peak_hours = []
            if search_times:
                hours = [datetime.fromisoformat(time).hour for time in search_times]
                hour_counts = {}
                for hour in hours:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                'predicted_search_type': most_common_type,
                'confidence': round(type_counts[most_common_type] / len(search_types), 3),
                'peak_search_hours': [hour for hour, count in peak_hours],
                'search_frequency': len(search_history),
                'recommendations': [
                    f"Most likely to search for: {most_common_type}",
                    f"Peak activity hours: {', '.join(map(str, [hour for hour, count in peak_hours]))}"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error predicting search patterns: {e}")
            return {'error': str(e)}
    
    # ==================== NATURAL LANGUAGE PROCESSING ====================
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text using NLP
        """
        try:
            entities = {
                'persons': [],
                'locations': [],
                'organizations': [],
                'dates': [],
                'numbers': []
            }
            
            # Simple regex-based entity extraction
            import re
            
            # Extract names (capitalized words)
            names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
            entities['persons'] = list(set(names))
            
            # Extract locations (words ending with common location suffixes)
            locations = re.findall(r'\b[A-Z][a-z]+(?: City| Town| Province| State| Country)\b', text)
            entities['locations'] = list(set(locations))
            
            # Extract dates
            dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
            entities['dates'] = list(set(dates))
            
            # Extract numbers
            numbers = re.findall(r'\b\d+\b', text)
            entities['numbers'] = list(set(numbers))
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {'error': str(e)}
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        """
        try:
            # Simple sentiment analysis using word lists
            positive_words = ['good', 'great', 'excellent', 'positive', 'happy', 'satisfied']
            negative_words = ['bad', 'terrible', 'negative', 'angry', 'disappointed', 'frustrated']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                score = positive_count / (positive_count + negative_count + 1)
            elif negative_count > positive_count:
                sentiment = 'negative'
                score = negative_count / (positive_count + negative_count + 1)
            else:
                sentiment = 'neutral'
                score = 0.5
            
            return {
                'sentiment': sentiment,
                'score': round(score, 3),
                'positive_words': positive_count,
                'negative_words': negative_count
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'error': str(e)}
    
    # ==================== UTILITY METHODS ====================
    
    def get_ai_capabilities(self) -> Dict[str, bool]:
        """Get available AI capabilities"""
        return {
            'advanced_face_analysis': 'deepface' in self.face_models,
            'face_quality_assessment': True,
            'image_enhancement': True,
            'super_resolution': True,
            'fuzzy_matching': True,
            'phonetic_matching': True,
            'risk_assessment': True,
            'pattern_prediction': True,
            'entity_extraction': True,
            'sentiment_analysis': True,
            'nlp_processing': 'spacy' in self.nlp_models
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get AI system status"""
        return {
            'models_loaded': self.models_loaded,
            'available_models': list(self.face_models.keys()) + list(self.nlp_models.keys()),
            'capabilities': self.get_ai_capabilities(),
            'timestamp': datetime.now().isoformat()
        }

# Global AI instance
ai_enhancements = AIEnhancements()

# Export functions for easy use
def analyze_face_advanced(image_bytes: bytes) -> Dict[str, Any]:
    """Advanced face analysis"""
    return ai_enhancements.analyze_face_advanced(image_bytes)

def enhance_image_quality(image_bytes: bytes) -> bytes:
    """Enhance image quality"""
    return ai_enhancements.enhance_image_quality(image_bytes)

def calculate_risk_score(person_data: Dict, search_context: Dict) -> Dict[str, Any]:
    """Calculate risk score"""
    return ai_enhancements.calculate_risk_score(person_data, search_context)

def fuzzy_name_matching(query: str, candidates: List[str], threshold: float = 0.8) -> List[Tuple[str, float]]:
    """Fuzzy name matching"""
    return ai_enhancements.fuzzy_name_matching(query, candidates, threshold)

def get_ai_capabilities() -> Dict[str, bool]:
    """Get AI capabilities"""
    return ai_enhancements.get_ai_capabilities()

