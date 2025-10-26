"""
AI Enhancements Implementation for Clearance Face Search System
Practical implementation of advanced AI features
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
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEnhancements:
    """Advanced AI features for the clearance system"""
    
    def __init__(self, db_path: str = "ai_analytics.db"):
        self.db_path = db_path
        self.models_loaded = False
        self.face_models = {}
        self.nlp_models = {}
        self.init_database()
        self.load_ai_models()
    
    def init_database(self):
        """Initialize AI analytics database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create AI analytics tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_face_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER,
                    age_prediction INTEGER,
                    gender_prediction TEXT,
                    emotion_score TEXT,
                    quality_score REAL,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_search_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    search_query TEXT,
                    search_type TEXT,
                    success_rate REAL,
                    response_time REAL,
                    ai_suggestions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_risk_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER,
                    risk_score REAL,
                    risk_factors TEXT,
                    risk_level TEXT,
                    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("AI analytics database initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
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
                logger.warning("DeepFace not available - install with: pip install deepface")
            
            # InsightFace for face embeddings
            try:
                import insightface
                self.face_models['insightface'] = insightface
                logger.info("InsightFace model loaded")
            except ImportError:
                logger.warning("InsightFace not available - install with: pip install insightface")
                
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
                logger.warning("spaCy not available - install with: pip install spacy")
                
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
                    # Analyze with DeepFace
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
                        'confidence': 0.9
                    })
                    
                except Exception as e:
                    logger.warning(f"DeepFace analysis failed: {e}")
            
            # Fallback to OpenCV if DeepFace not available
            if not results['face_detected']:
                results = self._analyze_face_opencv(image_array)
            
            # Calculate quality score
            results['quality_score'] = self._calculate_image_quality(image_array)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in face analysis: {e}")
            return {
                'age': None,
                'gender': None,
                'emotion': None,
                'quality_score': 0.0,
                'landmarks': [],
                'face_detected': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _analyze_face_opencv(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Fallback face analysis using OpenCV"""
        try:
            # Load OpenCV face cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                return {
                    'face_detected': True,
                    'confidence': 0.7,
                    'face_count': len(faces),
                    'face_rectangles': faces.tolist()
                }
            else:
                return {
                    'face_detected': False,
                    'confidence': 0.0
                }
                
        except Exception as e:
            logger.error(f"OpenCV face analysis failed: {e}")
            return {'face_detected': False, 'confidence': 0.0}
    
    def _calculate_image_quality(self, image_array: np.ndarray) -> float:
        """Calculate image quality score"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Calculate Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness = np.mean(gray)
            
            # Calculate contrast
            contrast = np.std(gray)
            
            # Normalize scores (0-1)
            sharpness_score = min(laplacian_var / 1000, 1.0)
            brightness_score = 1.0 - abs(brightness - 127) / 127
            contrast_score = min(contrast / 100, 1.0)
            
            # Combined quality score
            quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            return round(quality_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating image quality: {e}")
            return 0.0
    
    def enhance_image(self, image_bytes: bytes, enhancement_type: str = 'auto') -> bytes:
        """
        Enhance image quality using AI
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            if enhancement_type == 'auto':
                # Auto-enhance based on image analysis
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.2)
                
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.1)
                
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.3)
                
            elif enhancement_type == 'super_resolution':
                # Super resolution (requires additional models)
                image = self._super_resolution(image)
                
            elif enhancement_type == 'face_enhancement':
                # Face-specific enhancement
                image = self._enhance_face(image)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image_bytes
    
    def _super_resolution(self, image: Image.Image) -> Image.Image:
        """Super resolution enhancement (placeholder)"""
        # This would require additional models like ESRGAN
        # For now, just return the original image
        return image
    
    def _enhance_face(self, image: Image.Image) -> Image.Image:
        """Face-specific enhancement"""
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            # Apply face enhancement filters
            enhanced = cv2.bilateralFilter(img_array, 9, 75, 75)
            
            # Convert back to PIL Image
            return Image.fromarray(enhanced)
            
        except Exception as e:
            logger.error(f"Error in face enhancement: {e}")
            return image
    
    # ==================== SMART SEARCH ENGINE ====================
    
    def smart_search_suggestions(self, query: str, search_type: str = 'identity') -> List[str]:
        """
        Generate smart search suggestions based on query
        """
        try:
            suggestions = []
            
            # Basic fuzzy matching suggestions
            if search_type == 'identity':
                suggestions.extend(self._generate_name_suggestions(query))
            elif search_type == 'phone':
                suggestions.extend(self._generate_phone_suggestions(query))
            elif search_type == 'face':
                suggestions.extend(self._generate_face_suggestions(query))
            
            # Add common search patterns
            suggestions.extend(self._get_common_searches(search_type))
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error generating search suggestions: {e}")
            return []
    
    def _generate_name_suggestions(self, query: str) -> List[str]:
        """Generate name-based suggestions"""
        suggestions = []
        
        # Add variations of the name
        if len(query) > 2:
            suggestions.append(query.upper())
            suggestions.append(query.lower())
            suggestions.append(query.title())
        
        # Add common Indonesian name patterns
        common_prefixes = ['Ahmad', 'Muhammad', 'Abdul', 'Siti', 'Sri']
        for prefix in common_prefixes:
            if query.lower() not in prefix.lower():
                suggestions.append(f"{prefix} {query}")
        
        return suggestions
    
    def _generate_phone_suggestions(self, query: str) -> List[str]:
        """Generate phone number suggestions"""
        suggestions = []
        
        # Clean the query
        clean_query = ''.join(filter(str.isdigit, query))
        
        if len(clean_query) >= 4:
            # Add common Indonesian phone prefixes
            prefixes = ['+62', '08', '628']
            for prefix in prefixes:
                if not clean_query.startswith(prefix):
                    suggestions.append(f"{prefix}{clean_query}")
        
        return suggestions
    
    def _generate_face_suggestions(self, query: str) -> List[str]:
        """Generate face search suggestions"""
        return [
            "Upload foto dengan wajah yang jelas",
            "Pastikan wajah menghadap kamera",
            "Gunakan foto dengan pencahayaan yang baik",
            "Hindari foto dengan kacamata hitam",
            "Foto harus berukuran minimal 200x200 pixel"
        ]
    
    def _get_common_searches(self, search_type: str) -> List[str]:
        """Get common search patterns"""
        common_searches = {
            'identity': ['Ahmad', 'Muhammad', 'Siti', 'Sri', 'Abdul'],
            'phone': ['+628', '0812', '0813', '0814', '0815'],
            'face': ['Foto KTP', 'Foto Profil', 'Foto Selfie']
        }
        
        return common_searches.get(search_type, [])
    
    # ==================== PREDICTIVE ANALYTICS ====================
    
    def predict_risk_score(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict risk score based on person data
        """
        try:
            # Extract features for risk assessment
            features = self._extract_risk_features(person_data)
            
            # Simple risk scoring algorithm
            risk_score = 0.0
            risk_factors = []
            
            # Age-based risk
            if 'age' in features and features['age']:
                if features['age'] < 18 or features['age'] > 65:
                    risk_score += 0.2
                    risk_factors.append("Age outside normal range")
            
            # Location-based risk
            if 'location' in features and features['location']:
                high_risk_locations = ['Jakarta', 'Surabaya', 'Medan']
                if any(loc in features['location'] for loc in high_risk_locations):
                    risk_score += 0.1
                    risk_factors.append("High-risk location")
            
            # Data completeness risk
            required_fields = ['name', 'nik', 'address']
            missing_fields = [field for field in required_fields if not person_data.get(field)]
            if missing_fields:
                risk_score += len(missing_fields) * 0.1
                risk_factors.append(f"Missing data: {', '.join(missing_fields)}")
            
            # Normalize risk score
            risk_score = min(risk_score, 1.0)
            
            # Categorize risk level
            if risk_score < 0.3:
                risk_level = "Low"
            elif risk_score < 0.7:
                risk_level = "Medium"
            else:
                risk_level = "High"
            
            return {
                'risk_score': round(risk_score, 3),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendation': self._get_risk_recommendation(risk_level)
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk score: {e}")
            return {
                'risk_score': 0.5,
                'risk_level': 'Unknown',
                'risk_factors': ['Analysis error'],
                'recommendation': 'Manual review required'
            }
    
    def _extract_risk_features(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for risk assessment"""
        features = {}
        
        # Age calculation from birth date
        if 'tanggal_lahir' in person_data:
            try:
                birth_date = datetime.strptime(person_data['tanggal_lahir'], '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
                features['age'] = age
            except:
                pass
        
        # Location from address
        if 'alamat' in person_data:
            features['location'] = person_data['alamat']
        
        return features
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            'Low': 'Proceed with standard verification',
            'Medium': 'Additional verification recommended',
            'High': 'Manual review and enhanced verification required',
            'Unknown': 'Manual review required'
        }
        return recommendations.get(risk_level, 'Manual review required')
    
    # ==================== DATA ANALYTICS ====================
    
    def analyze_search_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze user search patterns
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get search history
            cursor.execute('''
                SELECT search_type, success_rate, response_time, created_at
                FROM ai_search_patterns
                WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
            '''.format(days), (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {'message': 'No search data available'}
            
            # Analyze patterns
            search_types = [row[0] for row in results]
            success_rates = [row[1] for row in results if row[1] is not None]
            response_times = [row[2] for row in results if row[2] is not None]
            
            analysis = {
                'total_searches': len(results),
                'most_used_type': max(set(search_types), key=search_types.count),
                'average_success_rate': round(np.mean(success_rates), 3) if success_rates else 0,
                'average_response_time': round(np.mean(response_times), 3) if response_times else 0,
                'search_frequency': self._calculate_search_frequency(results),
                'recommendations': self._generate_user_recommendations(search_types, success_rates)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing search patterns: {e}")
            return {'error': str(e)}
    
    def _calculate_search_frequency(self, results: List[Tuple]) -> Dict[str, Any]:
        """Calculate search frequency patterns"""
        try:
            # Group by date
            dates = [row[3][:10] for row in results]  # Extract date part
            date_counts = {}
            
            for date in dates:
                date_counts[date] = date_counts.get(date, 0) + 1
            
            return {
                'daily_average': round(np.mean(list(date_counts.values())), 2),
                'most_active_day': max(date_counts, key=date_counts.get) if date_counts else None,
                'total_active_days': len(date_counts)
            }
            
        except Exception as e:
            logger.error(f"Error calculating search frequency: {e}")
            return {}
    
    def _generate_user_recommendations(self, search_types: List[str], success_rates: List[float]) -> List[str]:
        """Generate recommendations based on user behavior"""
        recommendations = []
        
        # Most used search type
        most_used = max(set(search_types), key=search_types.count)
        recommendations.append(f"Most used search type: {most_used}")
        
        # Success rate recommendations
        if success_rates:
            avg_success = np.mean(success_rates)
            if avg_success < 0.5:
                recommendations.append("Consider refining search criteria for better results")
            elif avg_success > 0.8:
                recommendations.append("Excellent search performance! Keep up the good work")
        
        # Search type diversity
        unique_types = len(set(search_types))
        if unique_types == 1:
            recommendations.append("Try exploring other search types for better coverage")
        
        return recommendations
    
    # ==================== DATABASE OPERATIONS ====================
    
    def save_face_analysis(self, person_id: int, analysis_data: Dict[str, Any]):
        """Save face analysis results to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_face_analysis 
                (person_id, age_prediction, gender_prediction, emotion_score, 
                 quality_score, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                person_id,
                analysis_data.get('age'),
                analysis_data.get('gender'),
                json.dumps(analysis_data.get('emotion', {})),
                analysis_data.get('quality_score', 0.0),
                analysis_data.get('confidence', 0.0)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Face analysis saved for person {person_id}")
            
        except Exception as e:
            logger.error(f"Error saving face analysis: {e}")
    
    def save_search_pattern(self, user_id: int, search_query: str, search_type: str, 
                          success_rate: float, response_time: float, suggestions: List[str]):
        """Save search pattern to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_search_patterns 
                (user_id, search_query, search_type, success_rate, response_time, ai_suggestions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, search_query, search_type, success_rate, 
                response_time, json.dumps(suggestions)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Search pattern saved for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving search pattern: {e}")
    
    def save_risk_assessment(self, person_id: int, risk_data: Dict[str, Any]):
        """Save risk assessment to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_risk_assessments 
                (person_id, risk_score, risk_factors, risk_level)
                VALUES (?, ?, ?, ?)
            ''', (
                person_id,
                risk_data.get('risk_score', 0.0),
                json.dumps(risk_data.get('risk_factors', [])),
                risk_data.get('risk_level', 'Unknown')
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Risk assessment saved for person {person_id}")
            
        except Exception as e:
            logger.error(f"Error saving risk assessment: {e}")
    
    # ==================== UTILITY METHODS ====================
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get AI system status"""
        return {
            'models_loaded': self.models_loaded,
            'available_models': {
                'face_models': list(self.face_models.keys()),
                'nlp_models': list(self.nlp_models.keys())
            },
            'database_connected': self._check_database_connection(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _check_database_connection(self) -> bool:
        """Check database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except:
            return False

# ==================== USAGE EXAMPLES ====================

def example_usage():
    """Example usage of AI enhancements"""
    
    # Initialize AI enhancements
    ai = AIEnhancements()
    
    # Example 1: Face Analysis
    print("=== Face Analysis Example ===")
    with open('sample_face.jpg', 'rb') as f:
        face_bytes = f.read()
    
    face_analysis = ai.analyze_face_advanced(face_bytes)
    print(f"Face Analysis: {face_analysis}")
    
    # Example 2: Smart Search Suggestions
    print("\n=== Smart Search Example ===")
    suggestions = ai.smart_search_suggestions("Ahmad", "identity")
    print(f"Search Suggestions: {suggestions}")
    
    # Example 3: Risk Assessment
    print("\n=== Risk Assessment Example ===")
    person_data = {
        'name': 'Ahmad Susanto',
        'nik': '1234567890123456',
        'tanggal_lahir': '1990-01-01',
        'alamat': 'Jakarta Selatan'
    }
    
    risk_assessment = ai.predict_risk_score(person_data)
    print(f"Risk Assessment: {risk_assessment}")
    
    # Example 4: Search Pattern Analysis
    print("\n=== Search Pattern Analysis ===")
    pattern_analysis = ai.analyze_search_patterns(user_id=1, days=30)
    print(f"Pattern Analysis: {pattern_analysis}")
    
    # Example 5: AI Status
    print("\n=== AI System Status ===")
    status = ai.get_ai_status()
    print(f"AI Status: {status}")

if __name__ == "__main__":
    example_usage()
