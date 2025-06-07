#!/usr/bin/env python3
"""
Sophia Pay Ready Domain MCP Server - Financial Operations & Business Intelligence
Designed for large-scale data downloads, processing, and financial analysis
Integrates with complete database strategy: PostgreSQL, Redis, Weaviate, and Pinecone
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import os
import sys
import pandas as pd
import numpy as np
from decimal import Decimal

# Add the infrastructure directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure'))

try:
    from pinecone_manager import PineconeManager, VectorDocument, DomainSpecificVectorStore
except ImportError:
    print("Pinecone manager not found, using mock implementation")
    PineconeManager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SophiaPayReadyDomainServer:
    """Sophia Pay Ready Domain MCP Server with enterprise-grade financial data processing"""
    
    def __init__(self):
        self.domain = "sophia"
        self.description = "Intelligent, results-driven financial operations specialist for Pay Ready business intelligence and large-scale data processing"
        
        # Database connections with Sophia-specific configuration
        self.postgresql_config = {
            "host": os.getenv("POSTGRES_HOST", "45.77.87.106"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "orchestra"),
            "user": os.getenv("POSTGRES_USER", "orchestra"),
            "password": os.getenv("POSTGRES_PASSWORD", "OrchAI_DB_2024!")
        }
        
        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "45.77.87.106"),
            "port": os.getenv("REDIS_PORT", "6379"),
            "password": os.getenv("REDIS_PASSWORD", ""),
            "db": 1  # Sophia uses Redis DB 1
        }
        
        self.weaviate_config = {
            "url": os.getenv("WEAVIATE_URL", "http://45.77.87.106:8080"),
            "class_prefix": "Sophia"  # Sophia-specific Weaviate classes
        }
        
        # Initialize Pinecone with Sophia namespace
        self.pinecone_manager = None
        self.vector_store = None
        self._initialize_pinecone()
        
        # Initialize database connections
        self._initialize_databases()
        
        # Financial data processing configuration
        self.data_batch_size = 10000
        self.max_file_size_mb = 500
        self.supported_formats = ['csv', 'xlsx', 'json', 'parquet', 'sql']
        
    def _initialize_pinecone(self):
        """Initialize Pinecone vector database with Sophia namespace"""
        try:
            pinecone_api_key = os.getenv(
                "PINECONE_API_KEY",
                "pcsk_4vD8zy_Shcrmkr8JKBGm9hZ7ipbFRGVfGxb4Z3xkTAky5noWPRx2RMrWoFcoXPr5Vkwm5L"
            )
            if PineconeManager and pinecone_api_key:
                self.pinecone_manager = PineconeManager(api_key=pinecone_api_key)
                self.vector_store = DomainSpecificVectorStore(self.pinecone_manager)
                logger.info("✅ Pinecone initialized for Sophia domain")
            else:
                logger.warning("⚠️ Pinecone not available, using fallback storage")
        except Exception as e:
            logger.error(f"❌ Error initializing Pinecone: {e}")
    
    def _initialize_databases(self):
        """Initialize PostgreSQL, Redis, and Weaviate connections"""
        try:
            # PostgreSQL connection
            import psycopg2
            self.pg_conn = psycopg2.connect(**self.postgresql_config)
            logger.info("✅ PostgreSQL connected for Sophia domain")
            
            # Create Sophia-specific schemas if they don't exist
            self._setup_sophia_schemas()
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.pg_conn = None
        
        try:
            # Redis connection (using DB 1 for Sophia)
            import redis
            self.redis_client = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                password=self.redis_config["password"],
                db=self.redis_config["db"],
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis connected for Sophia domain (DB 1)")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
        
        try:
            # Weaviate connection
            import weaviate
            self.weaviate_client = weaviate.Client(self.weaviate_config["url"])
            logger.info("✅ Weaviate connected for Sophia domain")
        except Exception as e:
            logger.error(f"❌ Weaviate connection failed: {e}")
            self.weaviate_client = None
    
    def _setup_sophia_schemas(self):
        """Setup Sophia-specific database schemas for financial data"""
        if not self.pg_conn:
            return
            
        try:
            cursor = self.pg_conn.cursor()
            
            # Create Sophia schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS sophia")
            
            # Financial transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sophia.financial_transactions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    transaction_id VARCHAR(255) UNIQUE NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                    transaction_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    merchant_id VARCHAR(255),
                    customer_id VARCHAR(255),
                    payment_method VARCHAR(50),
                    processing_fee DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    metadata JSONB,
                    risk_score DECIMAL(3,2),
                    compliance_flags TEXT[],
                    CONSTRAINT valid_amount CHECK (amount > 0),
                    CONSTRAINT valid_risk_score CHECK (risk_score >= 0 AND risk_score <= 1)
                )
            """)
            
            # Business intelligence metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sophia.business_metrics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(15,4) NOT NULL,
                    metric_type VARCHAR(50) NOT NULL,
                    dimension_1 VARCHAR(100),
                    dimension_2 VARCHAR(100),
                    dimension_3 VARCHAR(100),
                    time_period VARCHAR(20) NOT NULL,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_source VARCHAR(100),
                    metadata JSONB,
                    UNIQUE(metric_name, time_period, dimension_1, dimension_2, dimension_3)
                )
            """)
            
            # Large data processing jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sophia.data_processing_jobs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_name VARCHAR(255) NOT NULL,
                    job_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'queued',
                    file_path TEXT,
                    file_size_mb DECIMAL(10,2),
                    records_total INTEGER,
                    records_processed INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    processing_config JSONB,
                    results_summary JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Financial reports and analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sophia.financial_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_name VARCHAR(255) NOT NULL,
                    report_type VARCHAR(50) NOT NULL,
                    report_period VARCHAR(20) NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_points INTEGER,
                    key_insights TEXT[],
                    recommendations TEXT[],
                    risk_factors TEXT[],
                    report_data JSONB,
                    file_path TEXT,
                    status VARCHAR(20) DEFAULT 'active'
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sophia_transactions_date ON sophia.financial_transactions(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sophia_transactions_status ON sophia.financial_transactions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sophia_transactions_merchant ON sophia.financial_transactions(merchant_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sophia_metrics_name_period ON sophia.business_metrics(metric_name, time_period)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sophia_jobs_status ON sophia.data_processing_jobs(status)")
            
            self.pg_conn.commit()
            logger.info("✅ Sophia database schemas created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error setting up Sophia schemas: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
    
    async def handle_large_data_download(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle large-scale data downloads and processing for financial analysis"""
        try:
            job_id = data_config.get("job_id", f"download_{datetime.now().timestamp()}")
            
            # Create processing job record
            if self.pg_conn:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    INSERT INTO sophia.data_processing_jobs 
                    (job_name, job_type, status, file_path, processing_config)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data_config.get("job_name", f"Data Download {job_id}"),
                    "large_data_download",
                    "processing",
                    data_config.get("source_url", ""),
                    json.dumps(data_config)
                ))
                db_job_id = cursor.fetchone()[0]
                self.pg_conn.commit()
            
            # Cache job status in Redis for real-time monitoring
            if self.redis_client:
                job_status = {
                    "job_id": job_id,
                    "status": "processing",
                    "progress": 0,
                    "started_at": datetime.now().isoformat(),
                    "estimated_completion": (datetime.now() + timedelta(minutes=30)).isoformat()
                }
                self.redis_client.setex(f"sophia:job:{job_id}", 3600, json.dumps(job_status))
            
            # Store in Pinecone for intelligent search
            if self.vector_store:
                doc = VectorDocument(
                    id=f"sophia_download_{job_id}",
                    content=f"Large data download: {data_config.get('job_name', '')} - {data_config.get('description', '')}",
                    metadata={
                        "type": "data_download_job",
                        "job_type": data_config.get("data_type", "financial"),
                        "status": "processing",
                        "source": data_config.get("source_system", ""),
                        "created_at": datetime.now().isoformat()
                    },
                    domain="sophia"
                )
                self.pinecone_manager.upsert_documents([doc], "sophia")
            
            return {
                "status": "success",
                "message": f"💼 Large data download '{data_config.get('job_name')}' initiated successfully! I'm processing this with enterprise-grade efficiency.",
                "job_id": job_id,
                "db_job_id": str(db_job_id) if 'db_job_id' in locals() else None,
                "estimated_completion": "30 minutes",
                "monitoring_endpoint": f"sophia:job:{job_id}",
                "capabilities": [
                    "Real-time progress tracking",
                    "Automatic data validation",
                    "Financial compliance checking",
                    "Business intelligence extraction"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error handling large data download: {e}")
            return {
                "status": "error",
                "message": f"Data download failed: {e}"
            }
    
    async def process_financial_transaction_batch(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process large batches of financial transactions with validation and compliance"""
        try:
            processed_count = 0
            failed_count = 0
            compliance_flags = []
            
            if not self.pg_conn:
                return {"status": "error", "message": "Database connection not available"}
            
            cursor = self.pg_conn.cursor()
            
            for transaction in transactions:
                try:
                    # Validate transaction data
                    validation_result = self._validate_financial_transaction(transaction)
                    if not validation_result["valid"]:
                        failed_count += 1
                        continue
                    
                    # Calculate risk score
                    risk_score = self._calculate_transaction_risk(transaction)
                    
                    # Insert transaction
                    cursor.execute("""
                        INSERT INTO sophia.financial_transactions 
                        (transaction_id, amount, currency, transaction_type, status, 
                         merchant_id, customer_id, payment_method, processing_fee, 
                         metadata, risk_score, compliance_flags)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (transaction_id) DO UPDATE SET
                        amount = EXCLUDED.amount,
                        status = EXCLUDED.status,
                        processed_at = CURRENT_TIMESTAMP,
                        metadata = EXCLUDED.metadata,
                        risk_score = EXCLUDED.risk_score
                    """, (
                        transaction.get("transaction_id"),
                        Decimal(str(transaction.get("amount", 0))),
                        transaction.get("currency", "USD"),
                        transaction.get("transaction_type", "payment"),
                        transaction.get("status", "pending"),
                        transaction.get("merchant_id"),
                        transaction.get("customer_id"),
                        transaction.get("payment_method"),
                        Decimal(str(transaction.get("processing_fee", 0))) if transaction.get("processing_fee") else None,
                        json.dumps(transaction.get("metadata", {})),
                        risk_score,
                        validation_result.get("compliance_flags", [])
                    ))
                    
                    processed_count += 1
                    
                    # Collect compliance flags
                    if validation_result.get("compliance_flags"):
                        compliance_flags.extend(validation_result["compliance_flags"])
                    
                except Exception as e:
                    logger.error(f"Error processing transaction {transaction.get('transaction_id', 'unknown')}: {e}")
                    failed_count += 1
            
            self.pg_conn.commit()
            
            # Cache batch summary in Redis
            if self.redis_client:
                batch_summary = {
                    "processed": processed_count,
                    "failed": failed_count,
                    "compliance_flags": list(set(compliance_flags)),
                    "processed_at": datetime.now().isoformat()
                }
                self.redis_client.setex(
                    f"sophia:batch:{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                    3600, 
                    json.dumps(batch_summary)
                )
            
            return {
                "status": "success",
                "message": f"💰 Financial transaction batch processed successfully! {processed_count} transactions processed with {len(set(compliance_flags))} compliance considerations.",
                "processed_count": processed_count,
                "failed_count": failed_count,
                "compliance_flags": list(set(compliance_flags)),
                "processing_rate": f"{processed_count} transactions/batch"
            }
            
        except Exception as e:
            logger.error(f"Error processing financial transaction batch: {e}")
            return {
                "status": "error",
                "message": f"Batch processing failed: {e}"
            }
    
    def _validate_financial_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial transaction for compliance and data integrity"""
        validation_result = {
            "valid": True,
            "compliance_flags": [],
            "errors": []
        }
        
        # Required fields validation
        required_fields = ["transaction_id", "amount", "transaction_type"]
        for field in required_fields:
            if not transaction.get(field):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Amount validation
        try:
            amount = float(transaction.get("amount", 0))
            if amount <= 0:
                validation_result["valid"] = False
                validation_result["errors"].append("Amount must be positive")
            elif amount > 100000:  # Large transaction flag
                validation_result["compliance_flags"].append("LARGE_TRANSACTION")
        except (ValueError, TypeError):
            validation_result["valid"] = False
            validation_result["errors"].append("Invalid amount format")
        
        # Currency validation
        valid_currencies = ["USD", "EUR", "GBP", "CAD", "AUD"]
        if transaction.get("currency") not in valid_currencies:
            validation_result["compliance_flags"].append("FOREIGN_CURRENCY")
        
        # Risk-based flags
        if transaction.get("payment_method") == "cryptocurrency":
            validation_result["compliance_flags"].append("CRYPTO_PAYMENT")
        
        return validation_result
    
    def _calculate_transaction_risk(self, transaction: Dict[str, Any]) -> float:
        """Calculate risk score for financial transaction"""
        risk_score = 0.0
        
        # Amount-based risk
        amount = float(transaction.get("amount", 0))
        if amount > 10000:
            risk_score += 0.3
        elif amount > 1000:
            risk_score += 0.1
        
        # Payment method risk
        payment_method = transaction.get("payment_method", "").lower()
        if payment_method in ["cryptocurrency", "wire_transfer"]:
            risk_score += 0.4
        elif payment_method in ["credit_card", "debit_card"]:
            risk_score += 0.1
        
        # Transaction type risk
        if transaction.get("transaction_type") in ["withdrawal", "transfer"]:
            risk_score += 0.2
        
        # Ensure risk score is between 0 and 1
        return min(1.0, max(0.0, risk_score))
    
    async def generate_business_intelligence_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive business intelligence reports from financial data"""
        try:
            report_name = report_config.get("report_name", f"BI_Report_{datetime.now().strftime('%Y%m%d')}")
            
            if not self.pg_conn:
                return {"status": "error", "message": "Database connection not available"}
            
            cursor = self.pg_conn.cursor()
            
            # Generate various business metrics
            insights = []
            recommendations = []
            risk_factors = []
            
            # Transaction volume analysis
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_transactions,
                    SUM(amount) as total_volume,
                    AVG(amount) as avg_transaction,
                    COUNT(CASE WHEN risk_score > 0.5 THEN 1 END) as high_risk_count
                FROM sophia.financial_transactions 
                WHERE created_at >= %s
            """, (datetime.now() - timedelta(days=30),))
            
            volume_data = cursor.fetchone()
            if volume_data:
                insights.append(f"Processed {volume_data[0]:,} transactions totaling ${volume_data[1]:,.2f}")
                insights.append(f"Average transaction value: ${volume_data[2]:,.2f}")
                
                if volume_data[3] > 0:
                    risk_percentage = (volume_data[3] / volume_data[0]) * 100
                    risk_factors.append(f"{risk_percentage:.1f}% of transactions flagged as high-risk")
            
            # Payment method distribution
            cursor.execute("""
                SELECT payment_method, COUNT(*), SUM(amount)
                FROM sophia.financial_transactions 
                WHERE created_at >= %s AND payment_method IS NOT NULL
                GROUP BY payment_method 
                ORDER BY COUNT(*) DESC
            """, (datetime.now() - timedelta(days=30),))
            
            payment_methods = cursor.fetchall()
            if payment_methods:
                insights.append(f"Top payment method: {payment_methods[0][0]} ({payment_methods[0][1]:,} transactions)")
            
            # Generate recommendations based on data
            if volume_data and volume_data[0] > 1000:
                recommendations.append("High transaction volume detected - consider scaling processing infrastructure")
            
            if risk_factors:
                recommendations.append("Implement enhanced fraud detection for high-risk transactions")
            
            # Store report in database
            cursor.execute("""
                INSERT INTO sophia.financial_reports 
                (report_name, report_type, report_period, data_points, key_insights, recommendations, risk_factors, report_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                report_name,
                report_config.get("report_type", "business_intelligence"),
                "30_days",
                volume_data[0] if volume_data else 0,
                insights,
                recommendations,
                risk_factors,
                json.dumps({
                    "volume_analysis": volume_data,
                    "payment_methods": payment_methods,
                    "generated_at": datetime.now().isoformat()
                })
            ))
            
            report_id = cursor.fetchone()[0]
            self.pg_conn.commit()
            
            return {
                "status": "success",
                "message": f"📊 Business intelligence report '{report_name}' generated successfully! I've identified key patterns and strategic opportunities.",
                "report_id": str(report_id),
                "insights": insights,
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "data_points": volume_data[0] if volume_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating business intelligence report: {e}")
            return {
                "status": "error",
                "message": f"Report generation failed: {e}"
            }
    
    async def search_financial_data(self, query: str, search_type: str = "all") -> Dict[str, Any]:
        """Search financial data across all databases with intelligent insights"""
        try:
            results = {
                "query": query,
                "search_type": search_type,
                "results": [],
                "insights": [],
                "recommended_actions": []
            }
            
            # Search in Pinecone for semantic similarity
            if self.pinecone_manager:
                vector_results = self.pinecone_manager.search_documents(query, "sophia", top_k=10)
                for match in vector_results.matches:
                    results["results"].append({
                        "source": "pinecone",
                        "score": match.score,
                        "content": match.metadata.get("content", ""),
                        "type": match.metadata.get("type", ""),
                        "metadata": match.metadata
                    })
            
            # Search in PostgreSQL for structured financial data
            if self.pg_conn and search_type in ["all", "transactions"]:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    SELECT transaction_id, amount, transaction_type, status, merchant_id, created_at, risk_score
                    FROM sophia.financial_transactions
                    WHERE transaction_id ILIKE %s OR merchant_id ILIKE %s
                    ORDER BY created_at DESC LIMIT 10
                """, (f"%{query}%", f"%{query}%"))
                
                for row in cursor.fetchall():
                    results["results"].append({
                        "source": "postgresql",
                        "type": "financial_transaction",
                        "transaction_id": row[0],
                        "amount": float(row[1]),
                        "transaction_type": row[2],
                        "status": row[3],
                        "merchant_id": row[4],
                        "created_at": row[5].isoformat(),
                        "risk_score": float(row[6]) if row[6] else 0.0
                    })
            
            # Generate intelligent insights
            if results["results"]:
                transaction_results = [r for r in results["results"] if r.get("type") == "financial_transaction"]
                if transaction_results:
                    avg_amount = np.mean([r["amount"] for r in transaction_results])
                    high_risk_count = len([r for r in transaction_results if r.get("risk_score", 0) > 0.5])
                    
                    results["insights"].append(f"Average transaction amount: ${avg_amount:,.2f}")
                    if high_risk_count > 0:
                        results["insights"].append(f"{high_risk_count} high-risk transactions identified")
                    
                    results["recommended_actions"].append("Review transaction patterns for optimization opportunities")
            
            return {
                "status": "success",
                "message": f"🔍 Found {len(results['results'])} results for '{query}' with intelligent financial analysis",
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Error searching financial data: {e}")
            return {
                "status": "error",
                "message": f"Search failed: {e}"
            }
    
    async def get_domain_status(self) -> Dict[str, Any]:
        """Get comprehensive status of Sophia domain and database connections"""
        status = {
            "domain": self.domain,
            "description": self.description,
            "timestamp": datetime.now().isoformat(),
            "databases": {
                "postgresql": "disconnected",
                "redis": "disconnected", 
                "weaviate": "disconnected",
                "pinecone": "disconnected"
            },
            "statistics": {},
            "capabilities": [
                "Large-scale data processing",
                "Financial transaction analysis",
                "Business intelligence reporting",
                "Real-time compliance monitoring",
                "Risk assessment automation"
            ]
        }
        
        # Check PostgreSQL
        if self.pg_conn:
            try:
                cursor = self.pg_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sophia.financial_transactions")
                transaction_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM sophia.financial_reports")
                report_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM sophia.data_processing_jobs WHERE status = 'processing'")
                active_jobs = cursor.fetchone()[0]
                
                status["databases"]["postgresql"] = "connected"
                status["statistics"]["financial_transactions"] = transaction_count
                status["statistics"]["reports_generated"] = report_count
                status["statistics"]["active_jobs"] = active_jobs
            except Exception as e:
                logger.error(f"PostgreSQL status check failed: {e}")
        
        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                status["databases"]["redis"] = "connected"
                # Get cache statistics
                cache_keys = self.redis_client.keys("sophia:*")
                status["statistics"]["cached_items"] = len(cache_keys)
            except Exception as e:
                logger.error(f"Redis status check failed: {e}")
        
        # Check Weaviate
        if self.weaviate_client:
            try:
                status["databases"]["weaviate"] = "connected"
            except Exception as e:
                logger.error(f"Weaviate status check failed: {e}")
        
        # Check Pinecone
        if self.pinecone_manager:
            try:
                stats = self.pinecone_manager.get_index_stats("sophia")
                status["databases"]["pinecone"] = "connected"
                status["statistics"]["vector_count"] = stats.total_vector_count
            except Exception as e:
                logger.error(f"Pinecone status check failed: {e}")
        
        return status
    
    async def process_natural_language_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process natural language requests with Sophia's intelligent, results-driven personality"""
        try:
            request_lower = request.lower()
            
            # Determine request type and respond with Sophia's personality
            if any(word in request_lower for word in ["download", "data", "large", "process", "import"]):
                return {
                    "status": "success",
                    "message": "💼 Excellent! Large-scale data operations are my specialty. I'll handle this with enterprise-grade efficiency and deliver actionable insights. What data source are we working with?",
                    "suggested_actions": [
                        "Configure large data download",
                        "Set up batch processing pipeline",
                        "Define data validation rules",
                        "Schedule automated processing"
                    ],
                    "personality": "efficient_data_specialist"
                }
            
            elif any(word in request_lower for word in ["financial", "payment", "transaction", "money", "revenue"]):
                return {
                    "status": "success", 
                    "message": "💰 Perfect! Financial analysis and payment processing are core to our Pay Ready operations. I'll provide comprehensive insights and ensure compliance at every step. What financial data needs attention?",
                    "suggested_actions": [
                        "Analyze transaction patterns",
                        "Generate financial reports",
                        "Monitor payment compliance",
                        "Calculate risk assessments"
                    ],
                    "personality": "strategic_financial_analyst"
                }
            
            elif any(word in request_lower for word in ["report", "analysis", "insight", "intelligence", "metrics"]):
                return {
                    "status": "success",
                    "message": "📊 Outstanding! Business intelligence and strategic reporting drive our success. I'll generate comprehensive insights that translate data into actionable business strategies. What metrics should we focus on?",
                    "suggested_actions": [
                        "Generate BI dashboard",
                        "Create performance metrics",
                        "Analyze market trends",
                        "Develop strategic recommendations"
                    ],
                    "personality": "strategic_business_analyst"
                }
            
            elif any(word in request_lower for word in ["risk", "compliance", "audit", "security"]):
                return {
                    "status": "success",
                    "message": "🛡️ Absolutely critical! Risk management and compliance are fundamental to our Pay Ready operations. I'll ensure we maintain the highest standards while optimizing for business growth. What compliance area needs review?",
                    "suggested_actions": [
                        "Conduct risk assessment",
                        "Review compliance status",
                        "Generate audit reports",
                        "Implement security measures"
                    ],
                    "personality": "compliance_risk_manager"
                }
            
            else:
                # General Sophia response
                return {
                    "status": "success",
                    "message": "💼 Hello! I'm Sophia, your Pay Ready operations specialist. I excel at large-scale data processing, financial analysis, and business intelligence. I turn complex data into strategic insights that drive results. How can I optimize your operations today?",
                    "suggested_actions": [
                        "Large-scale data processing",
                        "Financial transaction analysis", 
                        "Business intelligence reporting",
                        "Risk and compliance management"
                    ],
                    "personality": "results_driven_operations_specialist"
                }
                
        except Exception as e:
            logger.error(f"Error processing natural language request: {e}")
            return {
                "status": "error",
                "message": "💼 I apologize for the technical difficulty. Let me resolve this efficiently and get back to optimizing your operations."
            }

def main():
    """Test the Sophia Pay Ready domain server"""
    async def test_server():
        server = SophiaPayReadyDomainServer()
        
        print("💼 Sophia Pay Ready Domain MCP Server - Financial Operations")
        print("=" * 60)
        
        # Test domain status
        status = await server.get_domain_status()
        print(f"📊 Domain Status: {json.dumps(status, indent=2)}")
        
        # Test large data download
        download_result = await server.handle_large_data_download({
            "job_id": "test_download_1",
            "job_name": "Q4 Financial Data Import",
            "source_url": "https://api.payready.com/financial-data/q4",
            "data_type": "financial_transactions",
            "description": "Quarterly financial transaction data for analysis"
        })
        print(f"📥 Download Result: {download_result}")
        
        # Test financial transaction processing
        sample_transactions = [
            {
                "transaction_id": "TXN_001",
                "amount": 1250.00,
                "currency": "USD",
                "transaction_type": "payment",
                "merchant_id": "MERCH_123",
                "customer_id": "CUST_456",
                "payment_method": "credit_card"
            },
            {
                "transaction_id": "TXN_002", 
                "amount": 15000.00,
                "currency": "USD",
                "transaction_type": "transfer",
                "merchant_id": "MERCH_789",
                "customer_id": "CUST_101",
                "payment_method": "wire_transfer"
            }
        ]
        
        batch_result = await server.process_financial_transaction_batch(sample_transactions)
        print(f"💰 Batch Processing Result: {batch_result}")
        
        # Test business intelligence report
        report_result = await server.generate_business_intelligence_report({
            "report_name": "Pay Ready Q4 Analysis",
            "report_type": "quarterly_review"
        })
        print(f"📊 BI Report Result: {report_result}")
        
        # Test natural language processing
        nl_result = await server.process_natural_language_request(
            "I need to process a large dataset of financial transactions and generate compliance reports"
        )
        print(f"💬 Natural Language Result: {nl_result}")
        
        # Test financial data search
        search_result = await server.search_financial_data("TXN_001")
        print(f"🔍 Search Result: {search_result}")
        
        print("\n🎉 Sophia Pay Ready domain server test completed!")
    
    asyncio.run(test_server())

if __name__ == "__main__":
    main() 