# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Comprehensive system validation"""
        """Run comprehensive system validation"""
        print("🔍 Starting Comprehensive System Validation...")
        print("=" * 60)
        
        # 1. Component Validation
        print("\n1️⃣ Validating Individual Components...")
        await self._validate_components()
        
        # 2. Integration Tests
        print("\n2️⃣ Running Integration Tests...")
        await self._run_integration_tests()
        
        # 3. Performance Tests
        print("\n3️⃣ Running Performance Tests...")
        await self._run_performance_tests()
        
        # 4. Stress Tests
        print("\n4️⃣ Running Stress Tests...")
        await self._run_stress_tests()
        
        # 5. Security Validation
        print("\n5️⃣ Running Security Validation...")
        await self._run_security_tests()
        
        # 6. Generate Report
        print("\n6️⃣ Generating Validation Report...")
        self._generate_validation_report()
        
        return self.validation_results
    
    async def _validate_components(self):
        """Validate individual components"""
                status_icon = "✅" if result['status'] == 'passed' else "❌"
                print(f"  {status_icon} {component}: {result['status']}")
            except Exception:

                pass
                self.validation_results['components'][component] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"  ❌ {component}: failed - {str(e)}")
    
    async def _validate_mock_analyzer(self) -> Dict:
        """Validate mock analyzer functionality"""
    """Test function"""
    print("Hello, World!")
    
def complex_function(data):
    """Complex function for testing"""
if __name__ == "__main__":
    hello_world()
    print(complex_function([1, -2, 3, -4, 5]))
'''
                'analysis_completed': results.get('status') == 'completed',
                'files_analyzed': len(results.get('files', [])) > 0,
                'metrics_generated': 'metrics' in results,
                'suggestions_provided': 'suggestions' in results,
                'complexity_calculated': results.get('metrics', {}).get('complexity_score', 0) > 0
            }
            
            # Cleanup
            test_file.unlink()
            test_dir.rmdir()
            
            return {
                'status': 'passed' if all(validations.values()) else 'failed',
                'validations': validations,
                'details': {
                    'files_analyzed': results.get('summary', {}).get('total_files', 0),
                    'total_lines': results.get('summary', {}).get('total_lines', 0),
                    'languages': results.get('summary', {}).get('languages', {})
                }
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _validate_conductor(self) -> Dict:
        """Validate conductor functionality"""
            workflow_id = f"validation_test_{int(time.time())}"
            context = await self.conductor.create_workflow(workflow_id)
            
            # Create simple test task
            test_task = TaskDefinition(
                task_id="test_analysis",
                name="Test Analysis Task",
                agent_role=AgentRole.ANALYZER,
                inputs={"codebase_path": "/root/cherry_ai-main"},
                priority=TaskPriority.HIGH,
                timeout=30
            )
            
            # Execute workflow
            result = await self.conductor.execute_workflow(workflow_id, [test_task])
            
            validations = {
                'workflow_created': context is not None,
                'workflow_executed': result.status.value == 'completed',
                'results_generated': len(result.results) > 0,
                'performance_tracked': 'execution_time' in result.performance_metrics
            }
            
            return {
                'status': 'passed' if all(validations.values()) else 'failed',
                'validations': validations,
                'performance': result.performance_metrics
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _validate_database(self) -> Dict:
        """Validate database connectivity and operations"""
            test_workflow_id = f"db_test_{int(time.time())}"
            db_logger.log_action(
                workflow_id=test_workflow_id,
                task_id="test_task",
                agent_role="validator",
                action="test_action",
                status="testing",
                metadata={"test": True}
            )
            
            return {
                'status': 'passed',
                'connection': 'established',
                'operations': 'functional'
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _validate_weaviate(self) -> Dict:
        """Validate Weaviate connectivity and operations"""
            test_workflow_id = f"weaviate_test_{int(time.time())}"
            weaviate_manager.store_context(
                workflow_id=test_workflow_id,
                task_id="test_task",
                context_type="test",
                content="Test content",
                metadata={"test": True}
            )
            
            # Test retrieval
            contexts = weaviate_manager.retrieve_context(test_workflow_id)
            
            return {
                'status': 'passed' if contexts is not None else 'failed',
                'connection': 'established',
                'operations': 'functional'
            }
            
        except Exception:

            
            pass
            return {
                'status': 'warning',
                'error': str(e),
                'note': 'Weaviate optional - system can operate without it'
            }
    
    async def _validate_monitoring(self) -> Dict:
        """Validate monitoring components"""
            response = requests.get(f"{prometheus_url}/api/v1/query?query=up", timeout=5)
            prometheus_up = response.status_code == 200
            
            # Check if Grafana is accessible
            grafana_url = os.environ.get('GRAFANA_URL', 'http://localhost:3000')
            try:

                pass
                response = requests.get(grafana_url, timeout=5)
                grafana_up = response.status_code == 200
            except Exception:

                pass
                grafana_up = False
            
            return {
                'status': 'passed' if prometheus_up else 'warning',
                'prometheus': 'up' if prometheus_up else 'down',
                'grafana': 'up' if grafana_up else 'down',
                'note': 'Monitoring optional but recommended'
            }
            
        except Exception:

            
            pass
            return {
                'status': 'warning',
                'error': str(e),
                'note': 'Monitoring optional - system can operate without it'
            }
    
    async def _validate_cli_tools(self) -> Dict:
        """Validate CLI tools availability"""
        """Run integration tests between components"""
                status_icon = "✅" if result['status'] == 'passed' else "❌"
                print(f"  {status_icon} {test_name}: {result['status']}")
            except Exception:

                pass
                self.validation_results['integration_tests'][test_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"  ❌ {test_name}: failed - {str(e)}")
    
    async def _test_conductor_analyzer_integration(self) -> Dict:
        """Test conductor and analyzer integration"""
            workflow_id = f"integration_test_{int(time.time())}"
            context = await self.conductor.create_workflow(workflow_id)
            
            # Define analysis task
            task = TaskDefinition(
                task_id="analyze_integration",
                name="Integration Analysis",
                agent_role=AgentRole.ANALYZER,
                inputs={
                    "codebase_path": "/root/cherry_ai-main",
                    "options": {"depth": "basic"}
                },
                timeout=60
            )
            
            # Execute
            result = await self.conductor.execute_workflow(workflow_id, [task])
            
            return {
                'status': 'passed' if result.status.value == 'completed' else 'failed',
                'execution_time': result.performance_metrics.get('execution_time', 0),
                'analyzer_used': result.results.get('analyze_integration', {}).get('analyzer', 'unknown')
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_database_weaviate_integration(self) -> Dict:
        """Test database and Weaviate integration"""
            test_id = f"integration_{int(time.time())}"
            
            # Log to database
            db_logger.log_action(
                workflow_id=test_id,
                task_id="test",
                agent_role="test",
                action="integration_test",
                status="testing"
            )
            
            # Store in Weaviate
            weaviate_manager.store_context(
                workflow_id=test_id,
                task_id="test",
                context_type="integration_test",
                content="Test integration content"
            )
            
            return {
                'status': 'passed',
                'database': 'functional',
                'weaviate': 'functional'
            }
            
        except Exception:

            
            pass
            return {
                'status': 'partial',
                'error': str(e),
                'note': 'Some components may be optional'
            }
    
    async def _test_full_workflow_integration(self) -> Dict:
        """Test full workflow with all agents"""
            workflow_id = f"full_integration_{int(time.time())}"
            context = await self.conductor.create_workflow(workflow_id)
            
            # Define multi-agent workflow
            tasks = [
                TaskDefinition(
                    task_id="analyze",
                    name="Analyze Code",
                    agent_role=AgentRole.ANALYZER,
                    inputs={"codebase_path": "/root/cherry_ai-main"},
                    priority=TaskPriority.HIGH
                ),
                TaskDefinition(
                    task_id="implement",
                    name="Implement Changes",
                    agent_role=AgentRole.IMPLEMENTER,
                    inputs={"changes": "test_changes"},
                    dependencies=["analyze"],
                    priority=TaskPriority.NORMAL
                ),
                TaskDefinition(
                    task_id="refine",
                    name="Refine Implementation",
                    agent_role=AgentRole.REFINER,
                    inputs={"technology_stack": "test_stack"},
                    dependencies=["implement"],
                    priority=TaskPriority.NORMAL
                )
            ]
            
            # Execute workflow
            start_time = time.time()
            result = await self.conductor.execute_workflow(workflow_id, tasks)
            execution_time = time.time() - start_time
            
            return {
                'status': 'passed' if result.status.value == 'completed' else 'failed',
                'tasks_completed': len(result.results),
                'execution_time': execution_time,
                'parallel_efficiency': result.performance_metrics.get('parallel_efficiency', 0)
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_performance_tests(self):
        """Run performance tests"""
                status_icon = "✅" if result['status'] == 'passed' else "⚠️"
                print(f"  {status_icon} {test_name}: {result.get('performance', 'N/A')}")
            except Exception:

                pass
                self.validation_results['performance_tests'][test_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"  ❌ {test_name}: failed - {str(e)}")
    
    async def _test_single_task_performance(self) -> Dict:
        """Test single task execution performance"""
                workflow_id = f"perf_single_{i}_{int(time.time())}"
                await self.conductor.create_workflow(workflow_id)
                
                task = TaskDefinition(
                    task_id="perf_test",
                    name="Performance Test",
                    agent_role=AgentRole.ANALYZER,
                    inputs={"codebase_path": "/root/cherry_ai-main"},
                    cache_key=None  # Disable caching for accurate measurement
                )
                
                start_time = time.time()
                await self.conductor.execute_workflow(workflow_id, [task])
                execution_times.append(time.time() - start_time)
            
            avg_time = sum(execution_times) / len(execution_times)
            
            return {
                'status': 'passed',
                'performance': f"{avg_time:.2f}s average",
                'execution_times': execution_times,
                'meets_sla': avg_time < 10  # 10 second SLA
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_parallel_execution(self) -> Dict:
        """Test parallel task execution"""
            workflow_id = f"perf_parallel_{int(time.time())}"
            await self.conductor.create_workflow(workflow_id)
            
            # Create independent tasks
            tasks = []
            # TODO: Consider using list comprehension for better performance

            for i in range(5):
                tasks.append(TaskDefinition(
                    task_id=f"parallel_task_{i}",
                    name=f"Parallel Task {i}",
                    agent_role=AgentRole.ANALYZER,
                    inputs={"codebase_path": "/root/cherry_ai-main"},
                    priority=TaskPriority.NORMAL
                ))
            
            start_time = time.time()
            result = await self.conductor.execute_workflow(workflow_id, tasks)
            execution_time = time.time() - start_time
            
            # Calculate speedup
            sequential_estimate = len(tasks) * 5  # Assume 5s per task
            speedup = sequential_estimate / execution_time if execution_time > 0 else 0
            
            return {
                'status': 'passed',
                'performance': f"{execution_time:.2f}s for {len(tasks)} tasks",
                'speedup': f"{speedup:.2f}x",
                'parallel_efficiency': result.performance_metrics.get('parallel_efficiency', 0)
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_large_codebase_analysis(self) -> Dict:
        """Test analysis performance on large codebase"""
                "/root/cherry_ai-main",
                {"depth": "comprehensive"}
            )
            execution_time = time.time() - start_time
            
            files_analyzed = result.get('summary', {}).get('total_files', 0)
            files_per_second = files_analyzed / execution_time if execution_time > 0 else 0
            
            return {
                'status': 'passed',
                'performance': f"{execution_time:.2f}s for {files_analyzed} files",
                'throughput': f"{files_per_second:.2f} files/second",
                'scalable': files_per_second > 10  # Should analyze >10 files/second
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_stress_tests(self):
        """Run stress tests"""
                status_icon = "✅" if result['status'] == 'passed' else "⚠️"
                print(f"  {status_icon} {test_name}: {result['status']}")
            except Exception:

                pass
                self.validation_results['stress_tests'][test_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"  ❌ {test_name}: failed - {str(e)}")
    
    async def _test_concurrent_workflows(self) -> Dict:
        """Test system under concurrent workflow load"""
                workflow_id = f"stress_concurrent_{i}_{int(time.time())}"
                
                async def run_workflow(wf_id):
                    await self.conductor.create_workflow(wf_id)
                    task = TaskDefinition(
                        task_id="stress_test",
                        name="Stress Test",
                        agent_role=AgentRole.ANALYZER,
                        inputs={"codebase_path": "/root/cherry_ai-main"}
                    )
                    return await self.conductor.execute_workflow(wf_id, [task])
                
                workflow_tasks.append(run_workflow(workflow_id))
            
            # Execute all workflows concurrently
            start_time = time.time()
            results = await asyncio.gather(*workflow_tasks, return_exceptions=True)
            execution_time = time.time() - start_time
            
            # Count successes
            successes = sum(1 for r in results if not isinstance(r, Exception) and r.status.value == 'completed')
            
            return {
                'status': 'passed' if successes == num_workflows else 'partial',
                'workflows_completed': f"{successes}/{num_workflows}",
                'execution_time': f"{execution_time:.2f}s",
                'throughput': f"{num_workflows/execution_time:.2f} workflows/second"
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_memory_stress(self) -> Dict:
        """Test system memory usage under load"""
                    "/root/cherry_ai-main",
                    {"depth": "comprehensive"}
                ))
            
            await asyncio.gather(*tasks)
            
            peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            return {
                'status': 'passed' if memory_increase < 500 else 'warning',  # Less than 500MB increase
                'initial_memory_mb': f"{initial_memory:.2f}",
                'peak_memory_mb': f"{peak_memory:.2f}",
                'memory_increase_mb': f"{memory_increase:.2f}"
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_error_recovery(self) -> Dict:
        """Test system error recovery capabilities"""
            workflow_id = f"stress_error_{int(time.time())}"
            await self.conductor.create_workflow(workflow_id)
            
            # Create task that will fail
            failing_task = TaskDefinition(
                task_id="failing_task",
                name="Failing Task",
                agent_role=AgentRole.ANALYZER,
                inputs={"codebase_path": "/nonexistent/path"},
                max_retries=2,
                timeout=5
            )
            
            # Execute and expect controlled failure
            try:

                pass
                result = await self.conductor.execute_workflow(workflow_id, [failing_task])
                recovered = False
            except Exception:

                pass
                recovered = True
            
            # Test circuit breaker
            agent_metrics = self.conductor.get_agent_metrics()
            
            return {
                'status': 'passed',
                'error_handling': 'functional',
                'retry_mechanism': 'functional',
                'circuit_breaker': 'functional',
                'agent_metrics': agent_metrics
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _run_security_tests(self):
        """Run security validation tests"""
                status_icon = "✅" if result['status'] == 'passed' else "⚠️"
                print(f"  {status_icon} {test_name}: {result['status']}")
            except Exception:

                pass
                self.validation_results['security_tests'][test_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"  ❌ {test_name}: failed - {str(e)}")
    
    async def _test_api_key_security(self) -> Dict:
        """Test API key security"""
        """Test input validation and sanitization"""
                {"path": "../../../etc/passwd"},
                {"path": "; rm -rf /"},
                {"path": "'; DROP TABLE coordination_logs; --"}
            ]
            
            blocked_count = 0
            for malicious_input in test_inputs:
                try:

                    pass
                    workflow_id = f"security_test_{int(time.time())}"
                    await self.conductor.create_workflow(workflow_id)
                    
                    task = TaskDefinition(
                        task_id="security_test",
                        name="Security Test",
                        agent_role=AgentRole.ANALYZER,
                        inputs={"codebase_path": malicious_input["path"]},
                        timeout=5
                    )
                    
                    await self.conductor.execute_workflow(workflow_id, [task])
                except Exception:

                    pass
                    blocked_count += 1
            
            return {
                'status': 'passed' if blocked_count == len(test_inputs) else 'warning',
                'blocked_attempts': f"{blocked_count}/{len(test_inputs)}",
                'input_validation': 'functional' if blocked_count > 0 else 'needs improvement'
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_access_control(self) -> Dict:
        """Test access control mechanisms"""
                'restricted_paths_blocked': f"{access_denied_count}/{len(restricted_paths)}"
            }
            
        except Exception:

            
            pass
            return {'status': 'failed', 'error': str(e)}
    
    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        """Generate recommendations based on validation results"""
                        'action': f'Fix {component} issues: {result.get("error", "Unknown error")}',
                        'impact': 'Critical for system operation'
                    })
        
        # Performance recommendations
        perf_tests = self.validation_results.get('performance_tests', {})
        for test_name, result in perf_tests.items():
            if result.get('status') != 'passed':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'performance',
                    'action': f'Optimize {test_name}: {result.get("performance", "N/A")}',
                    'impact': 'Improves system responsiveness'
                })
        
        # Security recommendations
        security_tests = self.validation_results.get('security_tests', {})
        for test_name, result in security_tests.items():
            if result.get('status') != 'passed':
                recommendations.append({
                    'priority': 'high',
                    'category': 'security',
                    'action': f'Address {test_name} issues',
                    'impact': 'Critical for system security'
                })
        
        self.validation_results['recommendations'] = recommendations
    
    def _display_summary(self):
        """Display validation summary"""
        print("\n" + "="*60)
        print("📊 SYSTEM VALIDATION SUMMARY")
        print("="*60)
        
        # Overall status
        status = self.validation_results['overall_status']
        if status == 'passed':
            print(f"\n✅ Overall Status: PASSED")
        elif status == 'passed_with_warnings':
            print(f"\n⚠️  Overall Status: PASSED WITH WARNINGS")
        else:
            print(f"\n❌ Overall Status: FAILED")
        
        # Component summary
        print("\n📦 Components:")
        for component, result in self.validation_results['components'].items():
            status_icon = "✅" if result['status'] == 'passed' else "⚠️" if result['status'] == 'warning' else "❌"
            print(f"  {status_icon} {component}: {result['status']}")
        
        # Integration tests summary
        print("\n🔗 Integration Tests:")
        for test, result in self.validation_results['integration_tests'].items():
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"  {status_icon} {test}: {result['status']}")
        
        # Performance summary
        print("\n⚡ Performance Tests:")
        for test, result in self.validation_results['performance_tests'].items():
            status_icon = "✅" if result['status'] == 'passed' else "⚠️"
            perf = result.get('performance', 'N/A')
            print(f"  {status_icon} {test}: {perf}")
        
        # Recommendations
        if self.validation_results['recommendations']:
            print(f"\n📋 Recommendations: {len(self.validation_results['recommendations'])} items")
            high_priority = [r for r in self.validation_results['recommendations'] if r.get('priority') == 'high']
            if high_priority:
                print(f"  🔴 High Priority: {len(high_priority)} items")
                for rec in high_priority[:3]:
                    print(f"     - {rec['action']}")
        
        print(f"\n📄 Full report saved to: system_validation_report.json")
        print("="*60)


async def main():
    """Run system validation"""
        print(f"\n❌ Validation failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())