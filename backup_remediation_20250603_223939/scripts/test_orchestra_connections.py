# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Tests all Cherry AI connections and integrations"""
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    async def test_weaviate_connection(self) -> Tuple[bool, str]:
        """Test Weaviate vector database connection with v4 client"""
                host="localhost",
                port=8080,
                grpc_port=50051
            )
            
            # Test connection
            if client.is_ready():
                # Get schema/collections
                collections = list(client.collections.list_all().keys())
                client.close()
                return True, f"Connected. Found {len(collections)} collections"
            else:
                client.close()
                return False, "Weaviate not ready"
                
        except Exception:

                
            pass
            return False, "weaviate-client not installed or wrong version"
        except Exception:

            pass
            return False, f"Connection failed: {str(e)}"
    
    async def test_postgresql_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL database connection"""
                    return True, f"Connected as {creds['user']}. Version: {version.split(',')[0]}"
                except Exception:

                    pass
                    continue
            
            return False, "All credential combinations failed"
            
        except Exception:

            
            pass
            return False, "asyncpg not installed"
        except Exception:

            pass
            return False, f"Connection failed: {str(e)}"
    
    async def test_redis_connection(self) -> Tuple[bool, str]:
        """Test Redis cache connection"""
                    return True, f"Connected. Redis version: {redis_version}"
                else:
                    await redis_client.close()
                    return False, "Redis ping failed"
                    
            except Exception:

                    
                pass
                # Fallback to sync redis
                import redis
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                result = redis_client.ping()
                if result:
                    info = redis_client.info()
                    redis_version = info.get('redis_version', 'Unknown')
                    return True, f"Connected (sync). Redis version: {redis_version}"
                else:
                    return False, "Redis ping failed"
            
        except Exception:

            
            pass
            return False, "redis library not installed"
        except Exception:

            pass
            return False, f"Connection failed: {str(e)}"
    
    async def test_mcp_servers(self) -> Dict[str, Tuple[bool, str]]:
        """Test MCP server connections with correct endpoints"""
                response = await client.get("http://localhost:8001/mcp/weaviate_direct/health", timeout=5.0)
                if response.status_code == 200:
                    mcp_results["weaviate_direct"] = (True, "MCP server responding")
                elif response.status_code == 500:
                    mcp_results["weaviate_direct"] = (False, "Internal server error - check logs")
                else:
                    mcp_results["weaviate_direct"] = (False, f"Status: {response.status_code}")
        except Exception:

            pass
            mcp_results["weaviate_direct"] = (False, f"Connection failed: {str(e)}")
        
        # Test other endpoints
        endpoints = {
            "api_docs": "http://localhost:8001/docs",
            "openapi": "http://localhost:8001/openapi.json",
            "tools": "http://localhost:8001/mcp/weaviate_direct/tools"
        }
        
        for name, endpoint in endpoints.items():
            try:

                pass
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(endpoint, timeout=5.0)
                    if response.status_code in [200, 301, 302]:
                        mcp_results[name] = (True, f"Accessible at {endpoint}")
                    else:
                        mcp_results[name] = (False, f"Status: {response.status_code}")
            except Exception:

                pass
                mcp_results[name] = (False, "Not accessible")
        
        return mcp_results
    
    async def test_conductor_api(self) -> Tuple[bool, str]:
        """Test conductor API with correct endpoints"""
                "http://localhost:8001/docs",
                "http://localhost:8001/openapi.json",
                "http://localhost:8001/mcp/weaviate_direct/tools"
            ]
            
            async with httpx.AsyncClient() as client:
                working_endpoints = []
                for endpoint in endpoints:
                    try:

                        pass
                        response = await client.get(endpoint, timeout=5.0)
                        if response.status_code in [200, 301, 302]:
                            working_endpoints.append(endpoint)
                    except Exception:

                        pass
                        continue
                
                if working_endpoints:
                    return True, f"API accessible. Working endpoints: {len(working_endpoints)}"
                else:
                    return False, "No endpoints accessible"
            
        except Exception:

            
            pass
            return False, f"Test failed: {str(e)}"
    
    async def test_unified_database(self) -> Tuple[bool, str]:
        """Test UnifiedDatabase module"""
            return True, "UnifiedDatabase module imported successfully"
        except Exception:

            pass
            return False, "UnifiedDatabase module not found"
        except Exception:

            pass
            return False, f"Error: {str(e)}"
    
    async def test_docker_services(self) -> Tuple[bool, str]:
        """Test Docker container status"""
                return True, f"Docker running. {len(running_containers)} containers active"
            else:
                return False, "Docker command failed"
                
        except Exception:

                
            pass
            return False, f"Docker test failed: {str(e)}"
    
    async def run_all_tests(self):
        """Run all connection tests"""
        logger.info("Starting Cherry AI connection tests...")
        
        # Test Docker services first
        logger.info("Testing Docker services...")
        docker_result = await self.test_docker_services()
        self.test_results["tests"]["docker"] = {
            "passed": docker_result[0],
            "message": docker_result[1]
        }
        
        # Test Weaviate
        logger.info("Testing Weaviate connection...")
        weaviate_result = await self.test_weaviate_connection()
        self.test_results["tests"]["weaviate"] = {
            "passed": weaviate_result[0],
            "message": weaviate_result[1]
        }
        
        # Test PostgreSQL
        logger.info("Testing PostgreSQL connection...")
        pg_result = await self.test_postgresql_connection()
        self.test_results["tests"]["postgresql"] = {
            "passed": pg_result[0],
            "message": pg_result[1]
        }
        
        # Test Redis
        logger.info("Testing Redis connection...")
        redis_result = await self.test_redis_connection()
        self.test_results["tests"]["redis"] = {
            "passed": redis_result[0],
            "message": redis_result[1]
        }
        
        # Test MCP servers
        logger.info("Testing MCP servers...")
        mcp_results = await self.test_mcp_servers()
        for server, result in mcp_results.items():
            self.test_results["tests"][f"mcp_{server}"] = {
                "passed": result[0],
                "message": result[1]
            }
        
        # Test conductor API
        logger.info("Testing conductor API...")
        api_result = await self.test_conductor_api()
        self.test_results["tests"]["conductor_api"] = {
            "passed": api_result[0],
            "message": api_result[1]
        }
        
        # Test UnifiedDatabase
        logger.info("Testing UnifiedDatabase module...")
        db_result = await self.test_unified_database()
        self.test_results["tests"]["unified_database"] = {
            "passed": db_result[0],
            "message": db_result[1]
        }
        
        # Calculate summary
        self.test_results["summary"]["total"] = len(self.test_results["tests"])
        self.test_results["summary"]["passed"] = sum(
            1 for test in self.test_results["tests"].values() if test["passed"]
        )
        self.test_results["summary"]["failed"] = (
            self.test_results["summary"]["total"] - 
            self.test_results["summary"]["passed"]
        )
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = f"""
"""
        for test_name, result in self.test_results["tests"].items():
            status = "✅" if result["passed"] else "❌"
            report += f"\n{status} {test_name.upper()}:\n"
            report += f"   {result['message']}\n"
        
        report += """
"""
        if not self.test_results["tests"].get("weaviate", {}).get("passed", False):
            report += "\n• Weaviate: Update to weaviate-client v4\n"
            report += "  pip install 'weaviate-client>=4.0.0'\n"
        
        if not self.test_results["tests"].get("postgresql", {}).get("passed", False):
            report += "\n• PostgreSQL: Set proper credentials\n"
            report += "  export POSTGRES_PASSWORD=your_password\n"
        
        if not self.test_results["tests"].get("mcp_weaviate_direct", {}).get("passed", False):
            report += "\n• MCP Server: Fix persona configuration\n"
            report += "  Check persona configs have required 'id' and 'system_prompt' fields\n"
        
        report += """
"""
    """Main test function"""
    results_file = f"connection_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    logger.info(f"Results saved to: {results_file}")
    
    # Return exit code based on results
    if tester.test_results["summary"]["failed"] == 0:
        logger.info("✅ All tests passed!")
        return 0
    else:
        logger.warning(f"⚠️  {tester.test_results['summary']['failed']} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)