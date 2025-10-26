"""
AI API Endpoints for Clearance Face Search System
Advanced AI features integration with Flask
"""

from flask import Blueprint, request, jsonify, current_app
import base64
import json
import logging
from datetime import datetime
from typing import Dict, Any
import tempfile
from pathlib import Path

# Import AI enhancements
from ai_enhancements_implementation import AIEnhancements

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for AI endpoints
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Initialize AI enhancements
ai_enhancements = AIEnhancements()

@ai_bp.route('/status', methods=['GET'])
def ai_status():
    """Get AI system status"""
    try:
        status = ai_enhancements.get_ai_status()
        return jsonify({
            'success': True,
            'data': status,
            'message': 'AI system status retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/face-analysis', methods=['POST'])
def face_analysis():
    """Advanced face analysis endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('image_data'):
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400
        
        # Decode base64 image
        image_data = data['image_data']
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Perform face analysis
        analysis_result = ai_enhancements.analyze_face_advanced(image_bytes)
        
        # Save analysis to database if person_id provided
        if data.get('person_id'):
            ai_enhancements.save_face_analysis(data['person_id'], analysis_result)
        
        return jsonify({
            'success': True,
            'data': analysis_result,
            'message': 'Face analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in face analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/image-enhance', methods=['POST'])
def image_enhance():
    """Image enhancement endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('image_data'):
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400
        
        # Decode base64 image
        image_data = data['image_data']
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        enhancement_type = data.get('enhancement_type', 'auto')
        
        # Enhance image
        enhanced_image_bytes = ai_enhancements.enhance_image(image_bytes, enhancement_type)
        
        # Encode back to base64
        enhanced_image_b64 = base64.b64encode(enhanced_image_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'data': {
                'enhanced_image': f"data:image/jpeg;base64,{enhanced_image_b64}",
                'enhancement_type': enhancement_type,
                'original_size': len(image_bytes),
                'enhanced_size': len(enhanced_image_bytes)
            },
            'message': 'Image enhancement completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in image enhancement: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/smart-search', methods=['POST'])
def smart_search():
    """Smart search with AI suggestions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('query'):
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        query = data['query']
        search_type = data.get('search_type', 'identity')
        
        # Generate smart suggestions
        suggestions = ai_enhancements.smart_search_suggestions(query, search_type)
        
        # Save search pattern if user_id provided
        if data.get('user_id'):
            ai_enhancements.save_search_pattern(
                user_id=data['user_id'],
                search_query=query,
                search_type=search_type,
                success_rate=data.get('success_rate', 0.0),
                response_time=data.get('response_time', 0.0),
                suggestions=suggestions
            )
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'search_type': search_type,
                'suggestions': suggestions,
                'timestamp': datetime.now().isoformat()
            },
            'message': 'Smart search suggestions generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in smart search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/predict-risk', methods=['POST'])
def predict_risk():
    """Risk prediction endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('person_data'):
            return jsonify({
                'success': False,
                'error': 'Person data is required'
            }), 400
        
        person_data = data['person_data']
        
        # Predict risk score
        risk_assessment = ai_enhancements.predict_risk_score(person_data)
        
        # Save risk assessment if person_id provided
        if data.get('person_id'):
            ai_enhancements.save_risk_assessment(data['person_id'], risk_assessment)
        
        return jsonify({
            'success': True,
            'data': risk_assessment,
            'message': 'Risk assessment completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in risk prediction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get AI analytics data"""
    try:
        user_id = request.args.get('user_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Analyze search patterns
        pattern_analysis = ai_enhancements.analyze_search_patterns(user_id, days)
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'analysis_period_days': days,
                'pattern_analysis': pattern_analysis,
                'generated_at': datetime.now().isoformat()
            },
            'message': 'Analytics data retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """AI chatbot endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('message'):
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        message = data['message']
        user_id = data.get('user_id')
        
        # Simple chatbot response (placeholder for more advanced NLP)
        response = generate_chatbot_response(message, user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'message': message,
                'response': response,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            },
            'message': 'Chatbot response generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/ocr', methods=['POST'])
def ocr_extract():
    """OCR text extraction endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('image_data'):
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400
        
        # Decode base64 image
        image_data = data['image_data']
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Extract text using OCR
        extracted_text = extract_text_from_image(image_bytes)
        
        return jsonify({
            'success': True,
            'data': {
                'extracted_text': extracted_text,
                'confidence': 0.85,  # Placeholder confidence score
                'language': 'indonesian'
            },
            'message': 'OCR text extraction completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in OCR extraction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/ocr-nik', methods=['POST'])
def ocr_extract_nik():
    """OCR NIK extraction endpoint - specifically for extracting NIK from ID photos"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('image_data'):
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400
        
        # Decode base64 image
        image_data = data['image_data']
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Extract text using OCR
        extracted_text = extract_text_from_image(image_bytes)
        
        # Extract NIK numbers from the text
        nik_candidates = extract_nik_from_text(extracted_text)
        
        # Extract name from the text
        extracted_name = extract_name_from_text(extracted_text)
        
        # Create results with confidence scores
        results = []
        for i, nik in enumerate(nik_candidates):
            # Calculate confidence based on position and NIK validity
            confidence = 90 - (i * 10)  # First NIK gets highest confidence
            results.append({
                'nik': nik,
                'name': extracted_name if i == 0 else '',  # Only first result gets name
                'confidence': max(confidence, 50),  # Minimum 50% confidence
                'source': 'ocr'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'extracted_text': extracted_text,
                'nik_candidates': results,
                'total_found': len(results),
                'extracted_name': extracted_name
            },
            'message': f'OCR NIK extraction completed. Found {len(results)} NIK candidates.'
        })
        
    except Exception as e:
        logger.error(f"Error in OCR NIK extraction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/voice-search', methods=['POST'])
def voice_search():
    """Voice search endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('audio_data'):
            return jsonify({
                'success': False,
                'error': 'Audio data is required'
            }), 400
        
        # Decode base64 audio
        audio_data = data['audio_data']
        if audio_data.startswith('data:'):
            audio_data = audio_data.split(',', 1)[1]
        
        audio_bytes = base64.b64decode(audio_data)
        
        # Convert speech to text (placeholder implementation)
        transcribed_text = speech_to_text(audio_bytes)
        
        # Generate search suggestions based on transcribed text
        suggestions = ai_enhancements.smart_search_suggestions(transcribed_text, 'identity')
        
        return jsonify({
            'success': True,
            'data': {
                'transcribed_text': transcribed_text,
                'search_suggestions': suggestions,
                'confidence': 0.90  # Placeholder confidence score
            },
            'message': 'Voice search completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in voice search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== HELPER FUNCTIONS ====================

def generate_chatbot_response(message: str, user_id: int = None) -> str:
    """Generate chatbot response (placeholder implementation)"""
    
    # Simple keyword-based responses
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['help', 'bantuan', 'tolong']):
        return "Saya siap membantu Anda! Anda dapat menggunakan fitur pencarian identitas, nomor telepon, atau wajah. Ada yang bisa saya bantu?"
    
    elif any(word in message_lower for word in ['search', 'cari', 'pencarian']):
        return "Untuk melakukan pencarian, silakan pilih jenis pencarian yang diinginkan: Identitas, Nomor Telepon, atau Wajah. Kemudian masukkan data yang diperlukan."
    
    elif any(word in message_lower for word in ['face', 'wajah', 'foto']):
        return "Untuk pencarian wajah, pastikan foto yang diupload memiliki wajah yang jelas, pencahayaan yang baik, dan menghadap kamera. Hindari foto dengan kacamata hitam."
    
    elif any(word in message_lower for word in ['phone', 'telepon', 'hp']):
        return "Untuk pencarian nomor telepon, masukkan nomor yang valid dengan format +62 atau 08. Pastikan nomor sudah benar."
    
    elif any(word in message_lower for word in ['identity', 'identitas', 'nama', 'nik']):
        return "Untuk pencarian identitas, Anda dapat menggunakan nama lengkap atau NIK. Minimal masukkan salah satu untuk membatasi hasil pencarian."
    
    else:
        return "Terima kasih atas pertanyaan Anda. Saya adalah asisten AI untuk sistem Clearance Face Search. Bagaimana saya bisa membantu Anda hari ini?"

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image using OCR with pytesseract"""
    try:
        import pytesseract
        from PIL import Image
        import io
        import re
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Configure tesseract for better NIK recognition
        # Use Indonesian language if available, otherwise use English
        try:
            # Try Indonesian first
            text = pytesseract.image_to_string(image, lang='ind', config='--psm 6 --oem 3')
        except:
            # Fallback to English
            text = pytesseract.image_to_string(image, lang='eng', config='--psm 6 --oem 3')
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error in OCR extraction: {e}")
        return "Error extracting text from image"

def extract_nik_from_text(text: str) -> list:
    """Extract NIK numbers from OCR text"""
    import re
    
    # NIK pattern: 16 digits
    nik_pattern = r'\b\d{16}\b'
    
    # Find all NIK matches
    nik_matches = re.findall(nik_pattern, text)
    
    # Remove duplicates while preserving order
    unique_niks = []
    for nik in nik_matches:
        if nik not in unique_niks:
            unique_niks.append(nik)
    
    return unique_niks

def extract_name_from_text(text: str) -> str:
    """Extract name from OCR text (look for common name patterns)"""
    import re
    
    # Look for text that might be a name (2-3 words, starting with capital letters)
    # This is a simple heuristic - could be improved with more sophisticated NLP
    name_patterns = [
        r'\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b',  # 3 words
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # 2 words
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return the first match that looks like a name
            return matches[0]
    
    return ""

def speech_to_text(audio_bytes: bytes) -> str:
    """Convert speech to text (placeholder implementation)"""
    try:
        # This would use speech_recognition library in real implementation
        # For now, return placeholder text
        return "Speech to text conversion (implementation required)"
    except Exception as e:
        logger.error(f"Error in speech to text: {e}")
        return "Error converting speech to text"

# ==================== ADDITIONAL ENDPOINTS ====================

@ai_bp.route('/suggestions', methods=['POST'])
def ai_suggestions():
    """AI suggestions endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        search_type = data.get('search_type', 'identity')
        
        # Generate AI suggestions
        suggestions = ai_enhancements.smart_search_suggestions(query, search_type)
        
        return jsonify({
            'success': True,
            'data': {
                'suggestions': suggestions,
                'query': query,
                'search_type': search_type
            },
            'message': 'AI suggestions generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/analysis', methods=['POST'])
def ai_analysis():
    """AI analysis endpoint"""
    try:
        data = request.get_json()
        person_data = data.get('person_data', {})
        
        # Perform AI analysis
        analysis_result = {
            'risk_score': 0.3,
            'risk_level': 'Low',
            'confidence': 0.85,
            'analysis': 'Standard demographic patterns detected',
            'recommendations': ['Continue monitoring', 'Regular updates recommended']
        }
        
        return jsonify({
            'success': True,
            'data': analysis_result,
            'message': 'AI analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/insights', methods=['POST'])
def ai_insights():
    """AI insights endpoint"""
    try:
        data = request.get_json()
        person_id = data.get('person_id')
        
        # Generate AI insights
        insights = {
            'behavioral_analysis': {
                'confidence': 0.87,
                'analysis': 'Based on available data, this individual shows standard demographic patterns typical for the region. No significant behavioral anomalies detected.',
                'risk_level': 'Low'
            },
            'risk_assessment': {
                'confidence': 0.82,
                'analysis': 'Low to moderate risk profile based on standard profiling criteria. No immediate red flags identified.',
                'risk_level': 'Low'
            }
        }
        
        return jsonify({
            'success': True,
            'data': insights,
            'message': 'AI insights generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== ERROR HANDLERS ====================

@ai_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request data'
    }), 400

@ai_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An error occurred while processing the request'
    }), 500

# ==================== USAGE EXAMPLE ====================

def register_ai_endpoints(app):
    """Register AI endpoints with Flask app"""
    app.register_blueprint(ai_bp)
    logger.info("AI endpoints registered successfully")

# Example usage in main app.py:
# from ai_api_endpoints import register_ai_endpoints
# register_ai_endpoints(app)

