#!/usr/bin/env python3
"""
"""
    """
    """
        """
        """
        self.project_name = "cherry-ai-infrastructure"
        
    def check_prerequisites(self) -> bool:
        """
        """
        print("🔍 Checking prerequisites...")
        
        # Check Pulumi CLI
        try:

            pass
            result = subprocess.run(
                ["pulumi", "version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print("❌ Pulumi CLI not found. Please install Pulumi.")
                return False
            print(f"✅ Pulumi version: {result.stdout.strip()}")
        except Exception:

            pass
            print("❌ Pulumi CLI not found. Please install Pulumi.")
            return False
        
        # Check Python
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
        print(f"✅ Python version: {sys.version}")
        
        # Check virtual environment
        if not os.path.exists("venv"):
            print("📦 Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", "venv"])
            
        # Install dependencies
        print("📦 Installing dependencies...")
        pip_cmd = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"])
        
        return True
    
    def select_stack(self) -> bool:
        """
        """
        print(f"\n🎯 Selecting stack: {self.stack}")
        
        # Check if stack exists
        result = subprocess.run(
            ["pulumi", "stack", "ls", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            stacks = json.loads(result.stdout)
            stack_names = [s["name"].split("/")[-1] for s in stacks]
            
            if self.stack not in stack_names:
                print(f"📝 Creating new stack: {self.stack}")
                subprocess.run(["pulumi", "stack", "init", self.stack])
            else:
                subprocess.run(["pulumi", "stack", "select", self.stack])
        else:
            print(f"📝 Creating new stack: {self.stack}")
            subprocess.run(["pulumi", "stack", "init", self.stack])
        
        return True
    
    def preview_changes(self) -> bool:
        """
        """
        print("\n🔍 Previewing infrastructure changes...")
        
        result = subprocess.run(
            ["pulumi", "preview", "--diff"],
            env={**os.environ, "PULUMI_SKIP_UPDATE_CHECK": "true"}
        )
        
        return result.returncode == 0
    
    def deploy(self, auto_approve: bool = False) -> bool:
        """
        """
        print(f"\n🚀 Deploying to {self.stack} environment...")
        
        # Create deployment record
        deployment_id = f"{self.stack}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"📋 Deployment ID: {deployment_id}")
        
        # Run deployment
        cmd = ["pulumi", "up", "--yes"] if auto_approve else ["pulumi", "up"]
        
        result = subprocess.run(
            cmd,
            env={
                **os.environ,
                "PULUMI_SKIP_UPDATE_CHECK": "true",
                "DEPLOYMENT_ID": deployment_id
            }
        )
        
        if result.returncode == 0:
            print(f"\n✅ Deployment successful!")
            self.save_deployment_record(deployment_id, "success")
            self.export_outputs()
            return True
        else:
            print(f"\n❌ Deployment failed!")
            self.save_deployment_record(deployment_id, "failed")
            return False
    
    def destroy(self, auto_approve: bool = False) -> bool:
        """
        """
        print(f"\n🗑️  Destroying {self.stack} environment...")
        
        if not auto_approve:
            confirm = input("⚠️  Are you sure? Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("❌ Destruction cancelled")
                return False
        
        cmd = ["pulumi", "destroy", "--yes"]
        result = subprocess.run(cmd)
        
        return result.returncode == 0
    
    def export_outputs(self):
        """
        """
        print("\n📤 Exporting stack outputs...")
        
        result = subprocess.run(
            ["pulumi", "stack", "output", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            outputs = json.loads(result.stdout)
            
            # Save outputs to file
            output_file = f"outputs-{self.stack}.json"
            with open(output_file, "w") as f:
                json.dump(outputs, f, indent=2)
            
            print(f"✅ Outputs saved to {output_file}")
            
            # Print important outputs
            if "load_balancer_ip" in outputs:
                print(f"\n🌐 Load Balancer IP: {outputs['load_balancer_ip']}")
            if "monitoring_ip" in outputs:
                print(f"📊 Monitoring URL: http://{outputs['monitoring_ip']}:3000")
            
            # Save kubeconfig if available
            if "kubeconfig" in outputs:
                kubeconfig_file = f"kubeconfig-{self.stack}.yaml"
                with open(kubeconfig_file, "w") as f:
                    f.write(outputs["kubeconfig"])
                print(f"☸️  Kubeconfig saved to {kubeconfig_file}")
    
    def save_deployment_record(self, deployment_id: str, status: str):
        """
        """
            "deployment_id": deployment_id,
            "stack": self.stack,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "user": os.environ.get("USER", "unknown")
        }
        
        # Append to deployment log
        log_file = "deployments.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    
    def rollback(self):
        """
        """
        print("\n⏪ Rolling back to previous deployment...")
        
        result = subprocess.run(["pulumi", "stack", "history", "--json"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            history = json.loads(result.stdout)
            if len(history) > 1:
                # Find last successful deployment
                for i, entry in enumerate(history[1:], 1):
                    if entry.get("result") == "succeeded":
                        print(f"🔄 Rolling back to version {entry['version']}")
                        subprocess.run(["pulumi", "stack", "export", "--version", 
                                      str(entry["version"]), "|", "pulumi", 
                                      "stack", "import", "--force"])
                        return self.deploy(auto_approve=True)
        
        print("❌ No previous successful deployment found")
        return False

def main():
    """
    """
        description="Deploy Cherry AI infrastructure"
    )
    parser.add_argument(
        "action",
        choices=["deploy", "preview", "destroy", "rollback", "export"],
        help="Action to perform"
    )
    parser.add_argument(
        "--stack",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Target stack (default: dev)"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    # Initialize deployer
    deployer = InfrastructureDeployer(args.stack)
    
    # Check prerequisites
    if not deployer.check_prerequisites():
        sys.exit(1)
    
    # Select stack
    if not deployer.select_stack():
        sys.exit(1)
    
    # Execute action
    if args.action == "preview":
        success = deployer.preview_changes()
    elif args.action == "deploy":
        success = deployer.deploy(args.auto_approve)
    elif args.action == "destroy":
        success = deployer.destroy(args.auto_approve)
    elif args.action == "rollback":
        success = deployer.rollback()
    elif args.action == "export":
        deployer.export_outputs()
        success = True
    else:
        print(f"❌ Unknown action: {args.action}")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()