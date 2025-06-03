# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Final comprehensive test for Orchestra AI system"""
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    
    async def test_weaviate_operations(self) -> Tuple[bool, str]:
        """Test Weaviate CRUD operations"""
                host="localhost",
                port=8080,
                grpc_port=50051
            )
            
            # Test connection
            if not client.is_ready():
                client.close()
                return False, "Weaviate not ready"
            
            # Get collections
            collections = list(client.collections.list_all().keys())
            logger.info(f"Found {len(collections)} collections: {collections}")
            
            # Test CRUD on Knowledge collection
            test_collection = client.collections.get("Knowledge")
            
            # Create test object
            test_data = {
                "title": "Final Integration Test",
                "content": "Testing Orchestra AI system end-to-end",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "final_test"
            }
            
            # Insert
            object_id = test_collection.data.insert(test_data)
            logger.info(f"Created object: {object_id}")
            
            # Read
            retrieved = test_collection.query.fetch_object_by_id(object_id)
            if not retrieved:
                client.close()
                return False, "Failed to retrieve created object"
            
            # Delete
            test_collection.data.delete_by_id(object_id)
            logger.info("Cleaned up test object")
            
            client.close()
            return True, f"Weaviate operational with {len(collections)} collections"
            
        except Exception:

            
            pass
            return False, f"Weaviate test failed: {str(e)}"
    
    async def test_mcp_servers(self) -> Tuple[bool, str]:
        """Test MCP server functionality"""
                return False, "No agents found"
            
            logger.info(f"Found {len(agents)} agents")
            
            # Test running a task
            test_agent = agents[0]
            result = await run_agent_task(
                test_agent["id"], 
                "health_check", 
                {"test": True}
            )
            
            if result.get("status") == "completed":
                return True, f"MCP servers operational with {len(agents)} agents"
            else:
                return False, f"Agent task failed: {result}"
                
        except Exception:

                
            pass
            return False, f"MCP server modules not found: {e}"
        except Exception:

            pass
            return False, f"MCP test failed: {str(e)}"
    
    async def test_database_connection(self) -> Tuple[bool, str]:
        """Test database connectivity"""
            os.environ["POSTGRES_HOST"] = "127.0.0.1"
            os.environ["POSTGRES_PORT"] = "5432"
            os.environ["POSTGRES_USER"] = "postgres"
            os.environ["POSTGRES_PASSWORD"] = ""
            os.environ["POSTGRES_DB"] = "orchestra"
            
            # Try multiple connection approaches
            connection_attempts = [
                # Try without password first
                {"user": "postgres", "password": "", "database": "orchestra"},
                {"user": "postgres", "password": "", "database": "postgres"},
                {"user": "orchestra", "password": "", "database": "orchestra"},
            ]
            
            conn = None
            for attempt in connection_attempts:
                try:

                    pass
                    conn = await asyncpg.connect(
                        host="127.0.0.1",  # Use IP instead of localhost
                        port=5432,
                        timeout=5,
                        **attempt
                    )
                    break
                except Exception:

                    pass
                    continue
            
            if conn:
                
                # Test query
                version = await conn.fetchval('SELECT version()')
                await conn.close()
                
                logger.info(f"PostgreSQL connected: {version.split(',')[0]}")
                
                # Now test UnifiedDatabase
                try:

                    pass
                    from shared.database import UnifiedDatabase
                    
                    # Initialize pool
                    await UnifiedDatabase.initialize_pool()
                    
                    # Test with context manager
                    async with UnifiedDatabase() as db:
                        result = await db.fetch_one("SELECT 1 as test")
                        if result and result.get("test") == 1:
                            return True, "Database fully operational"
                        else:
                            return True, "Database connected but query returned unexpected result"
                            
                except Exception:

                            
                    pass
                    return True, "PostgreSQL connected (UnifiedDatabase not available)"
                except Exception:

                    pass
                    return True, f"PostgreSQL connected (UnifiedDatabase error: {e})"
            else:
                return False, "PostgreSQL connection failed - all attempts exhausted"
                
        except Exception:

                
            pass
            return False, "asyncpg not installed"
        except Exception:

            pass
            return False, f"Database test failed: {str(e)}"
    
    async def test_api_endpoints(self) -> Tuple[bool, str]:
        """Test API accessibility"""
                ("http://localhost:8000/docs", "Orchestrator API Docs"),
                ("http://localhost:8001/docs", "MCP Server Docs"),
                ("http://localhost:8080/v1/meta", "Weaviate Meta"),
                ("http://localhost:8001/openapi.json", "OpenAPI Schema")
            ]
            
            async with httpx.AsyncClient() as client:
                for endpoint, name in test_endpoints:
                    endpoints_tested += 1
                    try:

                        pass
                        response = await client.get(endpoint, timeout=3.0)
                        if response.status_code in [200, 301, 302]:
                            endpoints_working += 1
                            logger.info(f"✅ {name}: {endpoint}")
                        else:
                            logger.warning(f"❌ {name}: {endpoint} (status: {response.status_code})")
                    except Exception:

                        pass
                        logger.warning(f"❌ {name}: {endpoint} (error: {e})")
            
            if endpoints_working == 0:
                return False, "No API endpoints accessible"
            elif endpoints_working < endpoints_tested:
                return True, f"Partial API access: {endpoints_working}/{endpoints_tested} endpoints working"
            else:
                return True, f"All {endpoints_working} API endpoints accessible"
                
        except Exception:

                
            pass
            return False, "httpx not installed"
        except Exception:

            pass
            return False, f"API test failed: {str(e)}"
    
    async def test_redis_connection(self) -> Tuple[bool, str]:
        """Test Redis connectivity"""
                    return True, f"Redis operational (version: {version})"
                else:
                    await client.close()
                    return False, "Redis ping failed"
                    
            except Exception:

                    
                pass
                # Fallback to sync redis
                import redis
                client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                
                if client.ping():
                    info = client.info()
                    version = info.get('redis_version', 'Unknown')
                    return True, f"Redis operational (sync mode, version: {version})"
                else:
                    return False, "Redis ping failed"
                    
        except Exception:

                    
            pass
            return False, "Redis library not installed"
        except Exception:

            pass
            return False, "Redis not running or not accessible"
        except Exception:

            pass
            return False, f"Redis test failed: {str(e)}"
    
    async def test_docker_services(self) -> Tuple[bool, str]:
        """Check Docker container status"""
                return False, "Docker command failed"
            
            containers = result.stdout.strip().split('\n')
            containers = [c for c in containers if c]  # Remove empty strings
            
            # Check for expected containers
            expected = ['weaviate', 'orchestra-test']
            found = [c for c in expected if any(c in container for container in containers)]
            
            if not containers:
                return False, "No Docker containers running"
            elif len(found) < len(expected):
                return True, f"Partial Docker services: {len(found)}/{len(expected)} expected containers running"
            else:
                return True, f"All Docker services running ({len(containers)} containers)"
                
        except Exception:

                
            pass
            return False, "Docker command timed out"
        except Exception:

            pass
            return False, f"Docker test failed: {str(e)}"
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Orchestra AI Final Integration Tests...")
        
        tests = [
            ("Docker Services", self.test_docker_services),
            ("Weaviate Operations", self.test_weaviate_operations),
            ("MCP Servers", self.test_mcp_servers),
            ("Database Connection", self.test_database_connection),
            ("API Endpoints", self.test_api_endpoints),
            ("Redis Cache", self.test_redis_connection)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Testing {test_name}...")
            try:

                pass
                success, message = await test_func()
                self.test_results["tests"][test_name] = {
                    "success": success,
                    "message": message
                }
                
                if success:
                    if "Partial" in message or "but" in message:
                        self.test_results["warnings"] += 1
                        logger.warning(f"⚠️  {test_name}: {message}")
                    else:
                        self.test_results["passed"] += 1
                        logger.info(f"✅ {test_name}: {message}")
                else:
                    self.test_results["failed"] += 1
                    logger.error(f"❌ {test_name}: {message}")
                    
            except Exception:

                    
                pass
                self.test_results["tests"][test_name] = {
                    "success": False,
                    "message": f"Unexpected error: {e}"
                }
                self.test_results["failed"] += 1
                logger.error(f"❌ {test_name}: Unexpected error: {e}")
    
    def generate_report(self) -> str:
        """Generate final test report"""
        total_tests = len(self.test_results["tests"])
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
------------------"""
        for test_name, result in self.test_results["tests"].items():
            status = "✅" if result["success"] else "❌"
            if result["success"] and ("Partial" in result["message"] or "but" in result["message"]):
                status = "⚠️"
            report += f"\n{status} {test_name}:\n   {result['message']}\n"
        
        # Add summary based on results
        if self.test_results["failed"] == 0:
            if self.test_results["warnings"] == 0:
                report += """
"""
                report += f"""
"""
            report += f"""
"""
            if not self.test_results["tests"].get("Docker Services", {}).get("success"):
                report += "1. Start Docker containers: docker-compose up -d\n"
            
            if not self.test_results["tests"].get("Database Connection", {}).get("success"):
                report += "2. Fix PostgreSQL: sudo systemctl start postgresql\n"
                report += "   Set credentials: export POSTGRES_PASSWORD=postgres\n"
            
            if not self.test_results["tests"].get("Weaviate Operations", {}).get("success"):
                report += "3. Check Weaviate: docker logs weaviate\n"
            
            if not self.test_results["tests"].get("Redis Cache", {}).get("success"):
                report += "4. Start Redis: sudo systemctl start redis\n"
            
            report += """
"""
    """Main test execution"""
    results_file = f"final_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    logger.info(f"\n📄 Results saved to: {results_file}")
    
    # Return appropriate exit code
    if tester.test_results["failed"] > 0:
        return 1
    elif tester.test_results["warnings"] > 0:
        return 0  # Warnings are acceptable
    else:
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)