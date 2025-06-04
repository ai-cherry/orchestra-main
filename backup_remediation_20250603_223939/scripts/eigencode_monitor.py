# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Monitors EigenCode availability across multiple sources"""
            "https://www.eigencode.dev/stable/latest/linux/eigencode.tar.gz",
            "https://api.eigencode.dev/v1/health",
            "https://download.eigencode.dev/latest/eigencode-linux-amd64.tar.gz",
            
            # GitHub API endpoints
            "https://api.github.com/repos/eigencode/eigencode/releases/latest",
            "https://api.github.com/repos/eigencode/cli/releases/latest",
            "https://api.github.com/repos/eigencode-dev/eigencode/releases/latest",
            
            # Package manager APIs
            "https://registry.npmjs.org/eigencode",
            "https://pypi.org/pypi/eigencode/json",
            "https://crates.io/api/v1/crates/eigencode"
        ]
        
        # Notification settings
        self.notification_config = {
            "email": {
                "enabled": os.environ.get("EIGENCODE_MONITOR_EMAIL_ENABLED", "false").lower() == "true",
                "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
                "from_email": os.environ.get("MONITOR_FROM_EMAIL"),
                "to_email": os.environ.get("MONITOR_TO_EMAIL"),
                "password": os.environ.get("SMTP_PASSWORD")
            },
            "slack": {
                "enabled": os.environ.get("EIGENCODE_MONITOR_SLACK_ENABLED", "false").lower() == "true",
                "webhook_url": os.environ.get("SLACK_WEBHOOK_URL")
            }
        }
    
    async def check_url_availability(self, url: str) -> Dict:
        """Check if a URL is available and returns relevant info"""
            "url": url,
            "available": False,
            "status_code": None,
            "content_type": None,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
        
        try:

        
            pass
            response = requests.head(url, timeout=10, allow_redirects=True)
            result["status_code"] = response.status_code
            result["content_type"] = response.headers.get("content-type", "")
            
            if response.status_code == 200:
                result["available"] = True
                
                # For GitHub API, check if there are actual releases
                if "api.github.com" in url:
                    full_response = requests.get(url, timeout=10)
                    data = full_response.json()
                    if "assets" in data and len(data["assets"]) > 0:
                        result["github_assets"] = [
                            {
                                "name": asset["name"],
                                "size": asset["size"],
                                "download_url": asset["browser_download_url"]
                            }
                            for asset in data["assets"]
                            if any(platform in asset["name"].lower() 
                                  for platform in ["linux", "amd64", "x86_64"])
                        ]
                
        except Exception:

                
            pass
            result["error"] = str(e)
        except Exception:

            pass
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result
    
    async def check_all_sources(self) -> Dict:
        """Check all configured sources for EigenCode availability"""
            "check_id": f"check_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "check_count": self.check_count,
            "sources": {},
            "summary": {
                "any_available": False,
                "available_count": 0,
                "total_checked": len(self.urls_to_check)
            }
        }
        
        # Check each URL
        for url in self.urls_to_check:
            result = await self.check_url_availability(url)
            source_type = self._categorize_url(url)
            
            if source_type not in results["sources"]:
                results["sources"][source_type] = []
            
            results["sources"][source_type].append(result)
            
            if result["available"]:
                results["summary"]["available_count"] += 1
                results["summary"]["any_available"] = True
        
        # Log to database
        self.db_logger.log_action(
            workflow_id="eigencode_monitor",
            task_id=results["check_id"],
            agent_role="monitor",
            action="availability_check",
            status="completed",
            metadata=results
        )
        
        # Store in Weaviate
        self.weaviate_manager.store_context(
            workflow_id="eigencode_monitor",
            task_id=results["check_id"],
            context_type="availability_check",
            content=json.dumps(results),
            metadata={
                "timestamp": results["timestamp"],
                "available": results["summary"]["any_available"]
            }
        )
        
        return results
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL by source type"""
        if "github.com" in url:
            return "github"
        elif "npmjs.org" in url:
            return "npm"
        elif "pypi.org" in url:
            return "pypi"
        elif "crates.io" in url:
            return "cargo"
        elif "api." in url:
            return "api"
        else:
            return "direct_download"
    
    async def send_notifications(self, results: Dict):
        """Send notifications if EigenCode becomes available"""
        if results["summary"]["any_available"] and self.last_status is False:
            message = self._format_notification_message(results)
            
            # Send email notification
            if self.notification_config["email"]["enabled"]:
                await self._send_email_notification(message)
            
            # Send Slack notification
            if self.notification_config["slack"]["enabled"]:
                await self._send_slack_notification(message)
            
            # Log notification sent
            self.db_logger.log_action(
                workflow_id="eigencode_monitor",
                task_id=f"notification_{int(time.time())}",
                agent_role="monitor",
                action="notification_sent",
                status="completed",
                metadata={
                    "available_sources": results["summary"]["available_count"],
                    "notification_types": self._get_enabled_notifications()
                }
            )
    
    def _format_notification_message(self, results: Dict) -> str:
        """Format notification message"""
        message = "🎉 EigenCode is now available!\n\n"
        message += f"Detected at: {results['timestamp']}\n"
        message += f"Available sources: {results['summary']['available_count']}\n\n"
        
        for source_type, sources in results["sources"].items():
            available_sources = [s for s in sources if s["available"]]
            if available_sources:
                message += f"\n{source_type.upper()}:\n"
                for source in available_sources:
                    message += f"  ✓ {source['url']}\n"
                    if "github_assets" in source:
                        for asset in source["github_assets"]:
                            message += f"    - {asset['name']} ({asset['size']} bytes)\n"
        
        message += "\n\nRun the installer to set up EigenCode:\n"
        message += "python3 scripts/eigencode_installer.py\n"
        
        return message
    
    async def _send_email_notification(self, message: str):
        """Send email notification"""
            msg['From'] = self.notification_config["email"]["from_email"]
            msg['To'] = self.notification_config["email"]["to_email"]
            msg['Subject'] = "EigenCode is Now Available!"
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(
                self.notification_config["email"]["smtp_server"],
                self.notification_config["email"]["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.notification_config["email"]["from_email"],
                    self.notification_config["email"]["password"]
                )
                server.send_message(msg)
                
        except Exception:

                
            pass
            print(f"Failed to send email notification: {e}")
    
    async def _send_slack_notification(self, message: str):
        """Send Slack notification"""
            webhook_url = self.notification_config["slack"]["webhook_url"]
            
            payload = {
                "text": message,
                "username": "EigenCode Monitor",
                "icon_emoji": ":rocket:"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"Failed to send Slack notification: {response.text}")
                
        except Exception:

                
            pass
            print(f"Failed to send Slack notification: {e}")
    
    def _get_enabled_notifications(self) -> List[str]:
        """Get list of enabled notification types"""
        if self.notification_config["email"]["enabled"]:
            enabled.append("email")
        if self.notification_config["slack"]["enabled"]:
            enabled.append("slack")
        return enabled
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        print(f"Starting EigenCode availability monitoring...")
        print(f"Check interval: {self.check_interval} seconds")
        print(f"Notifications enabled: {self._get_enabled_notifications()}")
        
        while True:
            try:

                pass
                # Check availability
                results = await self.check_all_sources()
                
                # Print summary
                print(f"\n[{datetime.now()}] Check #{self.check_count}")
                print(f"Available sources: {results['summary']['available_count']}/{results['summary']['total_checked']}")
                
                # Send notifications if status changed
                if self.last_status is not None:
                    await self.send_notifications(results)
                
                # Update last status
                self.last_status = results["summary"]["any_available"]
                
                # Generate monitoring report
                if self.check_count % 24 == 0:  # Every 24 checks (daily if hourly)
                    await self.generate_monitoring_report()
                
            except Exception:

                
                pass
                print(f"Error during monitoring: {e}")
                self.db_logger.log_action(
                    workflow_id="eigencode_monitor",
                    task_id=f"error_{int(time.time())}",
                    agent_role="monitor",
                    action="monitoring_error",
                    status="failed",
                    error=str(e)
                )
            
            # Wait for next check
            await asyncio.sleep(self.check_interval)
    
    async def generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
            "eigencode_monitor",
            limit=100
        )
        
        report = {
            "report_id": f"report_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "total_checks": self.check_count,
            "monitoring_duration_hours": (self.check_count * self.check_interval) / 3600,
            "availability_timeline": [],
            "source_reliability": {},
            "recommendations": []
        }
        
        # Analyze availability timeline
        for check in recent_checks:
            content = json.loads(check.get("content", "{}"))
            report["availability_timeline"].append({
                "timestamp": content.get("timestamp"),
                "available": content.get("summary", {}).get("any_available", False),
                "sources_available": content.get("summary", {}).get("available_count", 0)
            })
        
        # Calculate source reliability
        source_stats = {}
        for check in recent_checks:
            content = json.loads(check.get("content", "{}"))
            for source_type, sources in content.get("sources", {}).items():
                if source_type not in source_stats:
                    source_stats[source_type] = {"total": 0, "available": 0}
                
                for source in sources:
                    source_stats[source_type]["total"] += 1
                    if source.get("available"):
                        source_stats[source_type]["available"] += 1
        
        for source_type, stats in source_stats.items():
            if stats["total"] > 0:
                report["source_reliability"][source_type] = {
                    "reliability_percentage": (stats["available"] / stats["total"]) * 100,
                    "total_checks": stats["total"],
                    "successful_checks": stats["available"]
                }
        
        # Generate recommendations
        if not any(check["available"] for check in report["availability_timeline"]):
            report["recommendations"].append(
                "EigenCode remains unavailable. Consider implementing enhanced fallback mechanisms."
            )
        
        # Store report
        self.weaviate_manager.store_context(
            workflow_id="eigencode_monitor",
            task_id=report["report_id"],
            context_type="monitoring_report",
            content=json.dumps(report),
            metadata={
                "timestamp": report["timestamp"],
                "total_checks": report["total_checks"]
            }
        )
        
        # Save to file
        with open(f"eigencode_monitoring_report_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nMonitoring report generated: {report['report_id']}")


async def main():
    """Main monitoring function"""
    parser = argparse.ArgumentParser(description="Monitor EigenCode availability")
    parser.add_argument("--interval", type=int, default=3600, 
                       help="Check interval in seconds (default: 3600)")
    parser.add_argument("--once", action="store_true", 
                       help="Run once and exit")
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = EigenCodeMonitor(check_interval=args.interval)
    
    if args.once:
        # Run single check
        results = await monitor.check_all_sources()
        print(json.dumps(results, indent=2))
        
        # Save results
        with open("eigencode_availability_check.json", 'w') as f:
            json.dump(results, f, indent=2)
    else:
        # Run continuous monitoring
        await monitor.run_continuous_monitoring()


if __name__ == "__main__":
    asyncio.run(main())