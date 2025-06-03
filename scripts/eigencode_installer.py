# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Handles alternative installation methods for EigenCode"""
            "https://www.eigencode.dev",
            "https://api.eigencode.dev",
            "https://download.eigencode.dev",
            "https://cdn.eigencode.dev"
        ]
        self.versions = ["stable/latest", "v1", "latest", "stable"]
        self.platforms = ["linux", "linux-x64", "linux-amd64", "ubuntu"]
        
    def log_attempt(self, method: str, status: str, details: Dict):
        """Log installation attempt to database and Weaviate"""
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "status": status,
            "details": details
        }
        self.installation_attempts.append(attempt)
        
        # Log to PostgreSQL
        self.db_logger.log_action(
            workflow_id="eigencode_installation",
            task_id=f"install_attempt_{len(self.installation_attempts)}",
            agent_role="installer",
            action=f"installation_{method}",
            status=status,
            metadata=details,
            error=details.get("error")
        )
        
        # Store in Weaviate
        self.weaviate_manager.store_context(
            workflow_id="eigencode_installation",
            task_id=f"install_attempt_{len(self.installation_attempts)}",
            context_type="installation_attempt",
            content=json.dumps(attempt),
            metadata={"method": method, "status": status}
        )
    
    async def check_url_availability(self, url: str) -> Tuple[bool, int, Optional[str]]:
        """Check if a URL is available and return status"""
        """Attempt direct download from various URLs"""
        logger.info("Attempting direct download methods...")
        
        for base_url in self.base_urls:
            for version in self.versions:
                for platform in self.platforms:
                    # Try different URL patterns
                    urls = [
                        f"{base_url}/{version}/{platform}/eigencode.tar.gz",
                        f"{base_url}/{version}/eigencode-{platform}.tar.gz",
                        f"{base_url}/releases/{version}/eigencode-{platform}.tar.gz",
                        f"{base_url}/download/{version}/{platform}/eigencode",
                        f"{base_url}/binaries/{platform}/{version}/eigencode"
                    ]
                    
                    for url in urls:
                        available, status_code, content_type = await self.check_url_availability(url)
                        
                        if available and status_code == 200:
                            logger.info(f"Found available URL: {url}")
                            
                            # Attempt download
                            try:

                                pass
                                response = requests.get(url, timeout=30)
                                
                                # Save file
                                filename = url.split('/')[-1]
                                download_path = f"/tmp/{filename}"
                                
                                with open(download_path, 'wb') as f:
                                    f.write(response.content)
                                
                                # Verify file type
                                file_info = subprocess.run(
                                    ['file', download_path],
                                    capture_output=True,
                                    text=True
                                ).stdout
                                
                                self.log_attempt(
                                    "direct_download",
                                    "success",
                                    {
                                        "url": url,
                                        "file_size": len(response.content),
                                        "file_type": file_info,
                                        "content_type": content_type
                                    }
                                )
                                
                                # Try to extract/install
                                if await self.install_from_file(download_path):
                                    return True
                                    
                            except Exception:

                                    
                                pass
                                self.log_attempt(
                                    "direct_download",
                                    "failed",
                                    {"url": url, "error": str(e)}
                                )
                        else:
                            if status_code != 0 and status_code != 404:
                                self.log_attempt(
                                    "url_check",
                                    "interesting",
                                    {
                                        "url": url,
                                        "status_code": status_code,
                                        "available": available
                                    }
                                )
        
        return False
    
    async def install_from_file(self, file_path: str) -> bool:
        """Attempt to install from downloaded file"""
            install_dir = "/root/.eigencode/bin"
            os.makedirs(install_dir, exist_ok=True)
            
            if "gzip" in file_type or "tar" in file_type:
                # Extract tar.gz
                subprocess.run(['tar', '-xzf', file_path, '-C', install_dir], check=True)
            elif "executable" in file_type or "ELF" in file_type:
                # Copy executable
                subprocess.run(['cp', file_path, f"{install_dir}/eigencode"], check=True)
                subprocess.run(['chmod', '+x', f"{install_dir}/eigencode"], check=True)
            elif "Zip" in file_type:
                # Extract zip
                subprocess.run(['unzip', '-o', file_path, '-d', install_dir], check=True)
            else:
                logger.warning(f"Unknown file type: {file_type}")
                return False
            
            # Verify installation
            eigencode_path = f"{install_dir}/eigencode"
            if os.path.exists(eigencode_path):
                # Try to run version command
                result = subprocess.run(
                    [eigencode_path, 'version'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"EigenCode installed successfully: {result.stdout}")
                    return True
                    
        except Exception:

                    
            pass
            logger.error(f"Installation from file failed: {e}")
            
        return False
    
    async def check_package_managers(self) -> bool:
        """Check various package managers for EigenCode"""
        logger.info("Checking package managers...")
        
        package_managers = [
            {
                "name": "snap",
                "check": ["snap", "--version"],
                "search": ["snap", "search", "eigencode"],
                "install": ["sudo", "snap", "install", "eigencode"]
            },
            {
                "name": "apt",
                "check": ["apt", "--version"],
                "search": ["apt", "search", "eigencode"],
                "install": ["sudo", "apt", "install", "-y", "eigencode"]
            },
            {
                "name": "npm",
                "check": ["npm", "--version"],
                "search": ["npm", "search", "eigencode"],
                "install": ["npm", "install", "-g", "eigencode"]
            },
            {
                "name": "pip",
                "check": ["pip", "--version"],
                "search": ["pip", "search", "eigencode"],
                "install": ["pip", "install", "eigencode"]
            },
            {
                "name": "cargo",
                "check": ["cargo", "--version"],
                "search": ["cargo", "search", "eigencode"],
                "install": ["cargo", "install", "eigencode"]
            }
        ]
        
        for pm in package_managers:
            try:

                pass
                # Check if package manager exists
                check_result = subprocess.run(pm["check"], capture_output=True)
                if check_result.returncode != 0:
                    continue
                
                # Search for package
                search_result = subprocess.run(
                    pm["search"],
                    capture_output=True,
                    text=True
                )
                
                if "eigencode" in search_result.stdout.lower():
                    logger.info(f"Found eigencode in {pm['name']}")
                    
                    # Attempt installation
                    install_result = subprocess.run(
                        pm["install"],
                        capture_output=True,
                        text=True
                    )
                    
                    if install_result.returncode == 0:
                        self.log_attempt(
                            f"package_manager_{pm['name']}",
                            "success",
                            {"output": install_result.stdout}
                        )
                        return True
                    else:
                        self.log_attempt(
                            f"package_manager_{pm['name']}",
                            "failed",
                            {"error": install_result.stderr}
                        )
                        
            except Exception:

                        
                pass
                self.log_attempt(
                    f"package_manager_{pm['name']}",
                    "error",
                    {"error": str(e)}
                )
        
        return False
    
    async def contact_api_for_instructions(self) -> Optional[Dict]:
        """Contact EigenCode API for installation instructions"""
        logger.info("Contacting EigenCode API for instructions...")
        
        api_endpoints = [
            "/api/v1/installation/instructions",
            "/api/installation",
            "/v1/install",
            "/installation/linux"
        ]
        
        headers = {
            "User-Agent": "EigenCode-Installer/1.0",
            "Accept": "application/json",
            "X-Platform": "linux",
            "X-Architecture": "x64"
        }
        
        # Add API key if available
        api_key = os.environ.get('EIGENCODE_API_KEY')
        if api_key:
            headers['Authorization'] = f"Bearer {api_key}"
        
        for base_url in self.base_urls:
            for endpoint in api_endpoints:
                url = f"{base_url}{endpoint}"
                
                try:

                
                    pass
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        self.log_attempt(
                            "api_instructions",
                            "success",
                            {"url": url, "response": data}
                        )
                        
                        # Process installation instructions
                        if "download_url" in data:
                            download_response = requests.get(data["download_url"], timeout=30)
                            if download_response.status_code == 200:
                                file_path = "/tmp/eigencode_api_download"
                                with open(file_path, 'wb') as f:
                                    f.write(download_response.content)
                                
                                if await self.install_from_file(file_path):
                                    return data
                        
                        return data
                        
                except Exception:

                        
                    pass
                    self.log_attempt(
                        "api_contact",
                        "failed",
                        {"url": url, "error": str(e)}
                    )
        
        return None
    
    async def check_github_releases(self) -> bool:
        """Check GitHub for EigenCode releases"""
        logger.info("Checking GitHub releases...")
        
        github_repos = [
            "eigencode/eigencode",
            "eigencode/cli",
            "eigencode/eigencode-cli",
            "eigencode-dev/eigencode"
        ]
        
        for repo in github_repos:
            try:

                pass
                # Check releases API
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    release_data = response.json()
                    
                    # Look for Linux assets
                    for asset in release_data.get('assets', []):
                        name = asset['name'].lower()
                        if 'linux' in name or 'ubuntu' in name:
                            download_url = asset['browser_download_url']
                            
                            # Download asset
                            download_response = requests.get(download_url, timeout=30)
                            if download_response.status_code == 200:
                                file_path = f"/tmp/{asset['name']}"
                                with open(file_path, 'wb') as f:
                                    f.write(download_response.content)
                                
                                self.log_attempt(
                                    "github_release",
                                    "downloaded",
                                    {"repo": repo, "asset": asset['name']}
                                )
                                
                                if await self.install_from_file(file_path):
                                    return True
                                    
            except Exception:

                                    
                pass
                self.log_attempt(
                    "github_check",
                    "failed",
                    {"repo": repo, "error": str(e)}
                )
        
        return False
    
    async def run_all_methods(self) -> Dict:
        """Run all installation methods and return results"""
        logger.info("Starting EigenCode installation attempts...")
        
        methods = [
            ("Direct Download", self.attempt_direct_download),
            ("Package Managers", self.check_package_managers),
            ("API Instructions", self.contact_api_for_instructions),
            ("GitHub Releases", self.check_github_releases)
        ]
        
        results = {
            "success": False,
            "method_used": None,
            "attempts": []
        }
        
        for method_name, method_func in methods:
            logger.info(f"Trying method: {method_name}")
            
            try:

            
                pass
                result = await method_func()
                
                if result:
                    results["success"] = True
                    results["method_used"] = method_name
                    logger.info(f"Successfully installed using {method_name}")
                    break
                    
            except Exception:

                    
                pass
                logger.error(f"Method {method_name} failed with error: {e}")
                self.log_attempt(
                    method_name.lower().replace(" ", "_"),
                    "exception",
                    {"error": str(e)}
                )
        
        # Store final results
        results["attempts"] = self.installation_attempts
        results["timestamp"] = datetime.now().isoformat()
        
        # Store comprehensive results in Weaviate
        self.weaviate_manager.store_context(
            workflow_id="eigencode_installation",
            task_id="final_results",
            context_type="installation_summary",
            content=json.dumps(results),
            metadata={
                "success": results["success"],
                "attempts_count": len(self.installation_attempts)
            }
        )
        
        return results


async def main():
    """Main function"""
    print("\n" + "=" * 50)
    print("EigenCode Installation Summary")
    print("=" * 50)
    print(f"Success: {results['success']}")
    if results['success']:
        print(f"Method Used: {results['method_used']}")
    print(f"Total Attempts: {len(results['attempts'])}")
    
    # Save detailed report
    report_path = "eigencode_installation_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Performance analysis
    print("\nPerformance Analysis:")
    total_time = 0
    for attempt in results['attempts']:
        if 'duration' in attempt.get('details', {}):
            total_time += attempt['details']['duration']
    
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Average time per attempt: {total_time/len(results['attempts']):.2f} seconds")
    
    return results['success']


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)