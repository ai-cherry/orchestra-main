import subprocess
#!/usr/bin/env python3
"""
"""
    """Metrics used for scaling decisions"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"
    QUEUE_LENGTH = "queue_length"
    RESPONSE_TIME = "response_time"

@dataclass
class ScalingPolicy:
    """Defines scaling policies"""
    """Represents a Vultr compute instance"""
    """Client for Vultr API operations"""
        self.base_url = "https://api.vultr.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_instance(self, config: Dict[str, Any]) -> VultrInstance:
        """Create a new Vultr instance"""
            "region": config.get("region", "ewr"),  # New Jersey
            "plan": config.get("plan", "vc2-1c-1gb"),  # 1 vCPU, 1GB RAM
            "os_id": config.get("os_id", 387),  # Ubuntu 20.04
            "label": config.get("label", f"cherry_ai-{datetime.now().timestamp()}"),
            "enable_ipv6": True,
            "backups": "enabled",
            "user_data": self._generate_user_data(config)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/instances",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 202:
                    data = await response.json()
                    instance_data = data["instance"]
                    
                    return VultrInstance(
                        instance_id=instance_data["id"],
                        label=instance_data["label"],
                        ip_address=instance_data["main_ip"],
                        status=instance_data["status"],
                        created_at=datetime.now(),
                        instance_type=instance_data["plan"],
                        region=instance_data["region"]
                    )
                else:
                    error = await response.text()
                    raise Exception(f"Failed to create instance: {error}")
    
    async def delete_instance(self, instance_id: str):
        """Delete a Vultr instance"""
                f"{self.base_url}/instances/{instance_id}",
                headers=self.headers
            ) as response:
                if response.status != 204:
                    error = await response.text()
                    raise Exception(f"Failed to delete instance: {error}")
    
    async def list_instances(self, label_prefix: str = "cherry_ai") -> List[VultrInstance]:
        """List Vultr instances with specific label prefix"""
                f"{self.base_url}/instances",
                headers=self.headers
            ) as response:
                data = await response.json()
                instances = []
                
                for inst in data.get("instances", []):
                    if inst["label"].startswith(label_prefix):
                        instances.append(VultrInstance(
                            instance_id=inst["id"],
                            label=inst["label"],
                            ip_address=inst["main_ip"],
                            status=inst["status"],
                            created_at=datetime.fromisoformat(inst["date_created"]),
                            instance_type=inst["plan"],
                            region=inst["region"]
                        ))
                
                return instances
    
    async def get_instance_metrics(self, instance_id: str) -> Dict[str, float]:
        """Get instance metrics for scaling decisions"""
            "cpu_usage": 0.75,  # 75%
            "memory_usage": 0.60,  # 60%
            "network_in": 1024 * 1024 * 10,  # 10 MB/s
            "network_out": 1024 * 1024 * 5   # 5 MB/s
        }
    
    def _generate_user_data(self, config: Dict[str, Any]) -> str:
        """Generate cloud-init user data for instance initialization"""
        user_data = f"""
"""
    """Handles automatic scaling of Vultr instances"""
        """Evaluate scaling policies and return scaling decisions"""
                if instance.status == "active":
                    metrics = await self.vultr_client.get_instance_metrics(
                        instance.instance_id
                    )
                    
                    if policy.metric == ScalingMetric.CPU_USAGE:
                        total_metric_value += metrics["cpu_usage"]
                    elif policy.metric == ScalingMetric.MEMORY_USAGE:
                        total_metric_value += metrics["memory_usage"]
            
            # Calculate average metric
            avg_metric = total_metric_value / max(instance_count, 1)
            
            # Make scaling decision
            if avg_metric > policy.scale_up_threshold and instance_count < policy.max_instances:
                decisions.append({
                    "action": "scale_up",
                    "policy": policy.name,
                    "current_instances": instance_count,
                    "target_instances": min(instance_count + 1, policy.max_instances),
                    "metric_value": avg_metric,
                    "reason": f"{policy.metric.value} exceeded {policy.scale_up_threshold}"
                })
            elif avg_metric < policy.scale_down_threshold and instance_count > policy.min_instances:
                decisions.append({
                    "action": "scale_down",
                    "policy": policy.name,
                    "current_instances": instance_count,
                    "target_instances": max(instance_count - 1, policy.min_instances),
                    "metric_value": avg_metric,
                    "reason": f"{policy.metric.value} below {policy.scale_down_threshold}"
                })
        
        return decisions
    
    async def execute_scaling(self, decision: Dict[str, Any]):
        """Execute a scaling decision"""
        action = decision["action"]
        policy_name = decision["policy"]
        
        try:

        
            pass
            if action == "scale_up":
                # Create new instance
                config = {
                    "label": f"cherry_ai-worker-{datetime.now().timestamp()}",
                    "role": "worker",
                    "region": "ewr",
                    "plan": "vc2-1c-2gb"  # 1 vCPU, 2GB RAM
                }
                
                instance = await self.vultr_client.create_instance(config)
                logger.info(f"Created instance: {instance.instance_id}")
                
            elif action == "scale_down":
                # Remove oldest instance
                instances = await self.vultr_client.list_instances()
                if instances:
                    # Sort by creation date and remove oldest
                    instances.sort(key=lambda x: x.created_at)
                    to_remove = instances[0]
                    
                    await self.vultr_client.delete_instance(to_remove.instance_id)
                    logger.info(f"Removed instance: {to_remove.instance_id}")
            
            # Update last scaling action
            self.last_scaling_action[policy_name] = datetime.now()
            
        except Exception:

            
            pass
            logger.error(f"Scaling execution failed: {e}")
            raise

class LoadBalancer:
    """Manages load balancing across Vultr instances"""
        """Update load balancer backend pool with active instances"""
            if instance.status == "active":
                # Check instance health
                is_healthy = await self._check_instance_health(instance)
                
                if is_healthy:
                    active_backends.append({
                        "ip": instance.ip_address,
                        "port": 8080,
                        "weight": 1
                    })
                
                self.health_checks[instance.instance_id] = {
                    "healthy": is_healthy,
                    "last_check": datetime.now()
                }
        
        # Update load balancer configuration
        await self._update_nginx_config(active_backends)
        
        return active_backends
    
    async def _check_instance_health(self, instance: VultrInstance) -> bool:
        """Check if instance is healthy"""
                    f"http://{instance.ip_address}:8080/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:

            pass
            return False
    
    async def _update_nginx_config(self, backends: List[Dict]):
        """Update NGINX configuration with active backends"""
        config = """
"""
            config += f"    server {backend['ip']}:{backend['port']} weight={backend['weight']};\n"
        
        config += """
"""
        with open("/etc/nginx/sites-available/cherry_ai", "w") as f:
            f.write(config)
        
        # Reload NGINX
        # subprocess.run is safer than os.system
subprocess.run(["nginx -s reload")

class Vultrconductor:
    """Main conductor for Vultr infrastructure"""
        self.vultr_client = VultrAPIClient(os.getenv("VULTR_API_KEY"))
        self.policies = self._initialize_policies()
        self.autoscaler = AutoScaler(self.vultr_client, self.policies)
        self.load_balancer = LoadBalancer(self.vultr_client)
        self.monitoring_interval = 60  # seconds
        
    def _initialize_policies(self) -> List[ScalingPolicy]:
        """Initialize scaling policies"""
                name="cpu_scaling",
                metric=ScalingMetric.CPU_USAGE,
                scale_up_threshold=0.80,  # 80%
                scale_down_threshold=0.20,  # 20%
                cooldown_seconds=300,
                min_instances=2,
                max_instances=10
            ),
            ScalingPolicy(
                name="memory_scaling",
                metric=ScalingMetric.MEMORY_USAGE,
                scale_up_threshold=0.85,  # 85%
                scale_down_threshold=0.30,  # 30%
                cooldown_seconds=300,
                min_instances=2,
                max_instances=10
            )
        ]
    
    async def start(self):
        """Start the Vultr conductor"""
        logger.info("Starting Vultr conductor")
        
        # Ensure minimum instances
        await self._ensure_minimum_instances()
        
        # Start monitoring loop
        while True:
            try:

                pass
                # Evaluate scaling
                decisions = await self.autoscaler.evaluate_scaling()
                
                # Execute scaling decisions
                for decision in decisions:
                    logger.info(f"Scaling decision: {decision}")
                    await self.autoscaler.execute_scaling(decision)
                
                # Update load balancer
                backends = await self.load_balancer.update_backend_pool()
                logger.info(f"Active backends: {len(backends)}")
                
                # Wait for next iteration
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception:

                
                pass
                logger.error(f"conductor error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _ensure_minimum_instances(self):
        """Ensure minimum number of instances are running"""
            logger.info(f"Creating {min_required - current_count} instances")
            
            for i in range(min_required - current_count):
                config = {
                    "label": f"cherry_ai-worker-{i}",
                    "role": "worker",
                    "region": "ewr",
                    "plan": "vc2-1c-2gb"
                }
                
                await self.vultr_client.create_instance(config)
                await asyncio.sleep(5)  # Avoid rate limiting