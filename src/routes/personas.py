from flask import Blueprint, jsonify, request
from datetime import datetime
from typing import List, Dict, Any

personas_bp = Blueprint('personas', __name__)

# Enhanced persona configurations
PERSONAS = {
    'cherry': {
        'id': 'cherry',
        'name': 'Cherry',
        'description': 'Creative AI specialized in content creation, design, and innovation',
        'avatar': 'C',
        'color': '#ef4444',
        'gradient': 'from-red-500 to-pink-500',
        'communication_style': {
            'tone': 'friendly and enthusiastic',
            'approach': 'creative and innovative',
            'greeting': "Hi there! I'm Cherry, and I'm excited to help you with this creative challenge!"
        },
        'expertise': [
            'Content Creation',
            'Design & Visual Arts',
            'Innovation & Brainstorming',
            'Creative Writing',
            'Brand Development',
            'Marketing Campaigns'
        ],
        'knowledge_domains': [
            'Art & Design',
            'Content Marketing',
            'Creative Industries',
            'Innovation Management',
            'Brand Strategy',
            'Digital Media'
        ],
        'capabilities': [
            'Generate creative content',
            'Design concepts and mockups',
            'Brainstorm innovative solutions',
            'Create marketing materials',
            'Develop brand strategies',
            'Write compelling copy'
        ],
        'status': 'active',
        'created_at': '2025-01-01T00:00:00Z',
        'last_updated': datetime.now().isoformat()
    },
    'sophia': {
        'id': 'sophia',
        'name': 'Sophia',
        'description': 'Strategic AI focused on analysis, planning, and complex problem-solving',
        'avatar': 'S',
        'color': '#3b82f6',
        'gradient': 'from-blue-500 to-indigo-500',
        'communication_style': {
            'tone': 'analytical and comprehensive',
            'approach': 'strategic and data-driven',
            'greeting': "As your strategic AI assistant, I've conducted a comprehensive analysis and gathered relevant information."
        },
        'expertise': [
            'Strategic Analysis',
            'Data Insights',
            'Problem Solving',
            'Research & Analysis',
            'Business Intelligence',
            'Decision Support'
        ],
        'knowledge_domains': [
            'Business Strategy',
            'Data Analytics',
            'Market Research',
            'Competitive Intelligence',
            'Risk Assessment',
            'Performance Metrics'
        ],
        'capabilities': [
            'Analyze complex data',
            'Develop strategic plans',
            'Conduct market research',
            'Assess risks and opportunities',
            'Create business intelligence reports',
            'Provide decision support'
        ],
        'status': 'active',
        'created_at': '2025-01-01T00:00:00Z',
        'last_updated': datetime.now().isoformat()
    },
    'karen': {
        'id': 'karen',
        'name': 'Karen',
        'description': 'Operational AI focused on execution, automation, and workflow management',
        'avatar': 'K',
        'color': '#10b981',
        'gradient': 'from-green-500 to-emerald-500',
        'communication_style': {
            'tone': 'organized and efficient',
            'approach': 'practical and systematic',
            'greeting': "I'm Karen, your operational AI. Let me provide you with structured, actionable information."
        },
        'expertise': [
            'Workflow Automation',
            'Process Optimization',
            'Project Management',
            'Operations Excellence',
            'System Integration',
            'Quality Assurance'
        ],
        'knowledge_domains': [
            'Operations Management',
            'Process Engineering',
            'Automation Technologies',
            'Quality Management',
            'Project Management',
            'System Administration'
        ],
        'capabilities': [
            'Optimize workflows',
            'Automate processes',
            'Manage projects',
            'Ensure quality standards',
            'Integrate systems',
            'Monitor performance'
        ],
        'status': 'active',
        'created_at': '2025-01-01T00:00:00Z',
        'last_updated': datetime.now().isoformat()
    }
}

@personas_bp.route('/personas', methods=['GET'])
def get_personas():
    """Get all available personas"""
    try:
        return jsonify({
            'personas': list(PERSONAS.values()),
            'total': len(PERSONAS),
            'active_personas': len([p for p in PERSONAS.values() if p['status'] == 'active']),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_bp.route('/personas/<persona_id>', methods=['GET'])
def get_persona(persona_id):
    """Get specific persona details"""
    try:
        if persona_id not in PERSONAS:
            return jsonify({'error': 'Persona not found'}), 404
        
        persona = PERSONAS[persona_id].copy()
        persona['last_accessed'] = datetime.now().isoformat()
        
        return jsonify({
            'persona': persona,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_bp.route('/personas/<persona_id>/capabilities', methods=['GET'])
def get_persona_capabilities(persona_id):
    """Get persona capabilities and expertise"""
    try:
        if persona_id not in PERSONAS:
            return jsonify({'error': 'Persona not found'}), 404
        
        persona = PERSONAS[persona_id]
        
        return jsonify({
            'persona_id': persona_id,
            'name': persona['name'],
            'expertise': persona['expertise'],
            'knowledge_domains': persona['knowledge_domains'],
            'capabilities': persona['capabilities'],
            'communication_style': persona['communication_style'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_bp.route('/personas/analytics/summary', methods=['GET'])
def get_persona_analytics():
    """Get persona usage analytics and summary"""
    try:
        analytics = {
            'total_personas': len(PERSONAS),
            'active_personas': len([p for p in PERSONAS.values() if p['status'] == 'active']),
            'persona_breakdown': {},
            'expertise_areas': {},
            'knowledge_domains': {},
            'total_capabilities': 0
        }
        
        # Analyze each persona
        for persona_id, persona in PERSONAS.items():
            analytics['persona_breakdown'][persona_id] = {
                'name': persona['name'],
                'status': persona['status'],
                'expertise_count': len(persona['expertise']),
                'domain_count': len(persona['knowledge_domains']),
                'capability_count': len(persona['capabilities'])
            }
            
            # Count expertise areas
            for expertise in persona['expertise']:
                analytics['expertise_areas'][expertise] = analytics['expertise_areas'].get(expertise, 0) + 1
            
            # Count knowledge domains
            for domain in persona['knowledge_domains']:
                analytics['knowledge_domains'][domain] = analytics['knowledge_domains'].get(domain, 0) + 1
            
            analytics['total_capabilities'] += len(persona['capabilities'])
        
        # Sort by frequency
        analytics['top_expertise'] = sorted(
            analytics['expertise_areas'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        analytics['top_domains'] = sorted(
            analytics['knowledge_domains'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        analytics['timestamp'] = datetime.now().isoformat()
        
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_bp.route('/personas/<persona_id>/domain-leanings', methods=['GET'])
def get_persona_domain_leanings(persona_id):
    """Get persona domain leanings and preferences"""
    try:
        if persona_id not in PERSONAS:
            return jsonify({'error': 'Persona not found'}), 404
        
        persona = PERSONAS[persona_id]
        
        # Calculate domain leanings based on expertise and knowledge domains
        domain_leanings = {}
        
        # Weight expertise areas higher
        for expertise in persona['expertise']:
            domain_leanings[expertise] = domain_leanings.get(expertise, 0) + 0.8
        
        # Add knowledge domains with lower weight
        for domain in persona['knowledge_domains']:
            domain_leanings[domain] = domain_leanings.get(domain, 0) + 0.6
        
        # Normalize scores
        max_score = max(domain_leanings.values()) if domain_leanings else 1
        normalized_leanings = {
            domain: score / max_score 
            for domain, score in domain_leanings.items()
        }
        
        return jsonify({
            'persona_id': persona_id,
            'name': persona['name'],
            'domain_leanings': normalized_leanings,
            'top_domains': sorted(
                normalized_leanings.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_bp.route('/personas/<persona_id>/domain-leanings', methods=['PUT'])
def update_persona_domain_leanings(persona_id):
    """Update persona domain leanings"""
    try:
        if persona_id not in PERSONAS:
            return jsonify({'error': 'Persona not found'}), 404
        
        data = request.get_json()
        if not data or 'leanings' not in data:
            return jsonify({'error': 'Domain leanings data is required'}), 400
        
        # In a real implementation, this would update the database
        # For now, we'll just return success
        
        return jsonify({
            'message': f'Domain leanings updated for {persona_id}',
            'persona_id': persona_id,
            'updated_leanings': data['leanings'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_bp.route('/personas/search', methods=['POST'])
def search_personas():
    """Search personas by capabilities, expertise, or domains"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query is required'}), 400
        
        query = data['query'].lower()
        matching_personas = []
        
        for persona_id, persona in PERSONAS.items():
            score = 0
            matches = []
            
            # Check name
            if query in persona['name'].lower():
                score += 10
                matches.append(f"Name: {persona['name']}")
            
            # Check description
            if query in persona['description'].lower():
                score += 8
                matches.append(f"Description match")
            
            # Check expertise
            for expertise in persona['expertise']:
                if query in expertise.lower():
                    score += 6
                    matches.append(f"Expertise: {expertise}")
            
            # Check knowledge domains
            for domain in persona['knowledge_domains']:
                if query in domain.lower():
                    score += 4
                    matches.append(f"Domain: {domain}")
            
            # Check capabilities
            for capability in persona['capabilities']:
                if query in capability.lower():
                    score += 5
                    matches.append(f"Capability: {capability}")
            
            if score > 0:
                matching_personas.append({
                    'persona': persona,
                    'relevance_score': score,
                    'matches': matches
                })
        
        # Sort by relevance score
        matching_personas.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return jsonify({
            'query': query,
            'results': matching_personas,
            'total_matches': len(matching_personas),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

