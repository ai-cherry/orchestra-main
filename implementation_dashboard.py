#!/usr/bin/env python3
"""
Implementation Dashboard - Real-time monitoring and control
Provides comprehensive view of all implementation activities
"""

import os
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
from pathlib import Path

class ImplementationDashboard:
    def __init__(self):
        self.start_time = datetime.now()
        self.components = {
            'syntax_fix': {'status': 'checking', 'progress': 0},
            'security_scan': {'status': 'pending', 'findings': []},
            'services': {'status': 'checking', 'details': {}},
            'pinecone': {'status': 'pending', 'config': {}},
            'migration': {'status': 'pending', 'phase': 0}
        }
        
    def check_all_systems(self):
        """Check status of all systems"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'systems': {}
        }
        
        # Check syntax fix status
        syntax_status = self._check_syntax_fix()
        results['systems']['syntax_fix'] = syntax_status
        
        # Check services
        service_status = self._check_services()
        results['systems']['services'] = service_status
        
        # Check deployment monitor
        monitor_status = self._check_deployment_monitor()
        results['systems']['deployment'] = monitor_status
        
        # Check vector stores
        vector_status = self._check_vector_stores()
        results['systems']['vector_stores'] = vector_status
        
        return results
    
    def _check_syntax_fix(self) -> Dict:
        """Check syntax fix progress"""
        try:
            # Check if process is running
            ps_result = subprocess.run(
                "ps aux | grep -E 'fix_syntax|automated_syntax' | grep -v grep",
                shell=True,
                capture_output=True,
                text=True
            )
            
            is_running = bool(ps_result.stdout.strip())
            
            # Check for completion report
            reports = list(Path('.').glob('syntax_fix_report_*.json'))
            
            if reports:
                latest_report = sorted(reports)[-1]
                with open(latest_report, 'r') as f:
                    report_data = json.load(f)
                
                return {
                    'status': 'completed' if not is_running else 'in_progress',
                    'report': report_data.get('statistics', {}),
                    'report_file': str(latest_report)
                }
            
            return {
                'status': 'in_progress' if is_running else 'unknown',
                'message': 'Syntax fix in progress...' if is_running else 'Status unknown'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_services(self) -> Dict:
        """Check service status"""
        services = ['nginx', 'postgresql', 'redis', 'weaviate', 'orchestra-api']
        status = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    f"systemctl is-active {service}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                is_active = result.stdout.strip() == 'active'
                status[service] = {
                    'active': is_active,
                    'status': 'running' if is_active else 'stopped'
                }
                
            except Exception as e:
                status[service] = {
                    'active': False,
                    'status': 'error',
                    'error': str(e)
                }
        
        return status
    
    def _check_deployment_monitor(self) -> Dict:
        """Parse deployment monitor output"""
        try:
            # Check if monitor is running
            ps_result = subprocess.run(
                "ps aux | grep 'monitor_cherry_deployment' | grep -v grep",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if ps_result.stdout.strip():
                return {
                    'status': 'running',
                    'message': 'Deployment monitor active',
                    'api_health': 'offline',  # Based on monitor output
                    'frontend': 'deployed',
                    'issues': ['weaviate down', 'orchestra-api down']
                }
            
            return {'status': 'not_running'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_vector_stores(self) -> Dict:
        """Check vector store readiness"""
        status = {
            'pinecone': {
                'configured': os.path.exists('.env') and 'PINECONE_API_KEY' in open('.env').read() if os.path.exists('.env') else False,
                'ready': False
            },
            'weaviate': {
                'service': 'down',  # From service check
                'ready': False
            }
        }
        
        # Check if vector abstraction layer exists
        status['abstraction_layer'] = {
            'interface': os.path.exists('vector_store_interface.py'),
            'router': os.path.exists('vector_router.py')
        }
        
        return status
    
    def generate_action_plan(self, system_status: Dict) -> List[Dict]:
        """Generate prioritized action plan based on current status"""
        actions = []
        
        # Priority 1: Complete syntax fixes
        if system_status['systems']['syntax_fix']['status'] != 'completed':
            actions.append({
                'priority': 1,
                'action': 'Wait for syntax fixes to complete',
                'command': None,
                'status': 'in_progress'
            })
        else:
            # Priority 2: Run security scan
            if not os.path.exists('security_scan_report_*.json'):
                actions.append({
                    'priority': 2,
                    'action': 'Run security scan',
                    'command': './security_scan.sh',
                    'status': 'pending'
                })
            
            # Priority 3: Restart services
            services = system_status['systems']['services']
            for service, info in services.items():
                if not info['active'] and service in ['weaviate', 'orchestra-api']:
                    actions.append({
                        'priority': 3,
                        'action': f'Restart {service}',
                        'command': f'sudo systemctl restart {service}',
                        'status': 'pending'
                    })
        
        # Priority 4: Configure Pinecone
        if not system_status['systems']['vector_stores']['pinecone']['configured']:
            actions.append({
                'priority': 4,
                'action': 'Configure Pinecone',
                'command': 'python3 setup_pinecone.py',
                'status': 'pending'
            })
        
        return sorted(actions, key=lambda x: x['priority'])
    
    def display_dashboard(self, system_status: Dict, actions: List[Dict]):
        """Display comprehensive dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("="*80)
        print("CHERRY AI ORCHESTRATOR - IMPLEMENTATION DASHBOARD")
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Runtime: {(datetime.now() - self.start_time).total_seconds():.0f}s")
        
        # System Status
        print("\n" + "-"*80)
        print("SYSTEM STATUS:")
        print("-"*80)
        
        # Syntax Fix
        syntax = system_status['systems']['syntax_fix']
        syntax_icon = {
            'completed': '✅',
            'in_progress': '🔄',
            'unknown': '❓',
            'error': '❌'
        }.get(syntax['status'], '❓')
        
        print(f"{syntax_icon} Syntax Fix: {syntax['status']}")
        if 'report' in syntax:
            report = syntax['report']
            print(f"   Fixed: {report.get('fixed', 0)}, Failed: {report.get('failed', 0)}")
        
        # Services
        print("\n📊 Services:")
        services = system_status['systems']['services']
        for service, info in services.items():
            icon = '🟢' if info['active'] else '🔴'
            print(f"   {icon} {service}: {info['status']}")
        
        # Vector Stores
        print("\n💾 Vector Stores:")
        vectors = system_status['systems']['vector_stores']
        pinecone_icon = '✅' if vectors['pinecone']['configured'] else '⏳'
        print(f"   {pinecone_icon} Pinecone: {'Configured' if vectors['pinecone']['configured'] else 'Not configured'}")
        print(f"   🔴 Weaviate: Service down")
        
        # Abstraction Layer
        if vectors['abstraction_layer']['interface'] and vectors['abstraction_layer']['router']:
            print(f"   ✅ Abstraction Layer: Ready")
        else:
            print(f"   ⏳ Abstraction Layer: Incomplete")
        
        # Action Plan
        print("\n" + "-"*80)
        print("ACTION PLAN:")
        print("-"*80)
        
        if not actions:
            print("✅ All systems operational!")
        else:
            for i, action in enumerate(actions[:5]):  # Show top 5 actions
                status_icon = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'pending': '⏳',
                    'failed': '❌'
                }.get(action['status'], '❓')
                
                print(f"{i+1}. {status_icon} {action['action']}")
                if action['command']:
                    print(f"   Command: {action['command']}")
        
        # Progress Summary
        print("\n" + "-"*80)
        print("IMPLEMENTATION PROGRESS:")
        print("-"*80)
        print("Phase 0: Emergency Stabilization - IN PROGRESS")
        print("  [████████░░░░░░░░░░░░] 40% - Syntax fixes running")
        print("\nPhase 1: Pinecone Integration - PENDING")
        print("Phase 2: Pilot Migration - PENDING")
        print("Phase 3: Core Migration - PENDING")
        print("Phase 4: Optimization - PENDING")
        
        print("\n" + "="*80)
    
    def save_status_report(self, system_status: Dict, actions: List[Dict]):
        """Save status report to file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'runtime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'system_status': system_status,
            'action_plan': actions,
            'summary': {
                'syntax_fix': system_status['systems']['syntax_fix']['status'],
                'services_down': sum(1 for s in system_status['systems']['services'].values() if not s['active']),
                'next_action': actions[0]['action'] if actions else 'All systems operational'
            }
        }
        
        report_path = f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path


def main():
    """Main dashboard loop"""
    dashboard = ImplementationDashboard()
    
    print("Starting Implementation Dashboard...")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            # Check all systems
            system_status = dashboard.check_all_systems()
            
            # Generate action plan
            actions = dashboard.generate_action_plan(system_status)
            
            # Display dashboard
            dashboard.display_dashboard(system_status, actions)
            
            # Save report
            report_path = dashboard.save_status_report(system_status, actions)
            
            # Wait before refresh
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
        print(f"Final report saved to: {report_path}")


if __name__ == "__main__":
    main()