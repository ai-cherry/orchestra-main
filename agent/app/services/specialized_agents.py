"""
"""
    """Types of specialized agents"""
    PERSONAL = "personal"
    PAY_READY = "pay_ready"
    PARAGON_MEDICAL = "paragon_medical"

@dataclass
class UserPreference:
    """User preference data structure"""
    """Apartment listing data structure"""
    """Clinical trial data structure"""
    """Base class for specialized agents"""
        self.status = "idle"
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.tasks_completed = 0
        self.llm_router = get_intelligent_llm_router()
        
        # Redis for caching and state management
        self.redis_client = None
        self._init_redis()
        
        # Weaviate for vector search
        self.weaviate_client = None
        self._init_weaviate()
        
    def _init_redis(self):
        """Initialize Redis connection"""
            logger.error(f"Failed to initialize Redis: {e}")
    
    def _init_weaviate(self):
        """Initialize Weaviate connection"""
                url="http://localhost:8080",
                timeout_config=(5, 15)
            )
        except Exception:

            pass
            logger.error(f"Failed to initialize Weaviate: {e}")
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task - to be implemented by subclasses"""
        """Get agent status"""
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "tasks_completed": self.tasks_completed
        }

class PersonalAgent(BaseSpecializedAgent):
    """
    """
            agent_id="personal-001",
            name="Personal Assistant",
            agent_type=AgentType.PERSONAL
        )
        self.user_preferences: Dict[str, Dict[str, UserPreference]] = defaultdict(dict)
        self.search_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.feedback_loops: Dict[str, List[float]] = defaultdict(list)
        
    async def learn_preference(
        self,
        user_id: str,
        category: str,
        signal_type: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Learn from user interaction"""
        if signal_type == "positive":
            pref.positive_signals += 1
            pref.weight = min(2.0, pref.weight * 1.1)  # Increase weight up to 2x
        elif signal_type == "negative":
            pref.negative_signals += 1
            pref.weight = max(0.1, pref.weight * 0.9)  # Decrease weight down to 0.1x
        
        pref.last_updated = datetime.utcnow()
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.hset(
                f"user_preferences:{user_id}",
                category,
                json.dumps({
                    "weight": pref.weight,
                    "positive": pref.positive_signals,
                    "negative": pref.negative_signals,
                    "updated": pref.last_updated.isoformat()
                })
            )
    
    async def adaptive_search(
        self,
        user_id: str,
        query: str,
        search_type: str = "general"
    ) -> Dict[str, Any]:
        """Perform adaptive search based on user preferences"""
                "user_id": user_id,
                "search_type": search_type,
                "preferences": {k: v.weight for k, v in preferences.items()}
            }
        )
        
        # Extract and rank results
        results = await self._extract_and_rank_results(response, preferences)
        
        # Store in search history
        search_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "enhanced_query": enhanced_query,
            "results_count": len(results),
            "top_result": results[0] if results else None
        }
        self.search_history[user_id].append(search_entry)
        
        # Update vector store for semantic search
        if self.weaviate_client and results:
            await self._update_vector_store(user_id, query, results)
        
        return {
            "query": query,
            "results": results,
            "preferences_applied": list(preferences.keys()),
            "search_id": search_entry["timestamp"]
        }
    
    async def _enhance_query_with_preferences(
        self,
        query: str,
        preferences: Dict[str, UserPreference]
    ) -> str:
        """Enhance query based on user preferences"""
            pref_context = ", ".join([
                f"{cat} (importance: {pref.weight:.1f})"
                for cat, pref in sorted_prefs[:3]
            ])
            enhanced = f"{query}\n\nUser preferences: {pref_context}"
        else:
            enhanced = query
        
        return enhanced
    
    async def _extract_and_rank_results(
        self,
        response: Dict[str, Any],
        preferences: Dict[str, UserPreference]
    ) -> List[Dict[str, Any]]:
        """Extract and rank results based on preferences"""
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse results (simplified - in production would use structured output)
        results = []
        for i, line in enumerate(content.split("\n")):
            if line.strip():
                results.append({
                    "id": f"result_{i}",
                    "content": line.strip(),
                    "relevance_score": 1.0 - (i * 0.1)  # Simple decay
                })
        
        # Apply preference weighting
        for result in results:
            score_boost = 0.0
            for cat, pref in preferences.items():
                if cat.lower() in result["content"].lower():
                    score_boost += pref.weight * 0.2
            result["final_score"] = result["relevance_score"] + score_boost
        
        # Sort by final score
        results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return results[:10]  # Top 10 results
    
    async def _update_vector_store(
        self,
        user_id: str,
        query: str,
        results: List[Dict[str, Any]]
    ):
        """Update vector store with search results"""
                "user_id": user_id,
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "top_results": json.dumps(results[:3])
            }
            
            self.weaviate_client.data_object.create(
                data_object=data_object,
                class_name="UserSearchHistory"
            )
        except Exception:

            pass
            logger.error(f"Failed to update vector store: {e}")
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a personal agent task"""
        self.status = "active"
        self.last_activity = datetime.utcnow()
        
        try:

        
            pass
            task_type = task.get("type", "search")
            
            if task_type == "search":
                result = await self.adaptive_search(
                    user_id=task["user_id"],
                    query=task["query"],
                    search_type=task.get("search_type", "general")
                )
            elif task_type == "learn_preference":
                await self.learn_preference(
                    user_id=task["user_id"],
                    category=task["category"],
                    signal_type=task["signal_type"],
                    context=task.get("context")
                )
                result = {"status": "preference_updated"}
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            self.tasks_completed += 1
            return result
            
        finally:
            self.status = "idle"

class PayReadyAgent(BaseSpecializedAgent):
    """
    """
            agent_id="payready-001",
            name="Pay Ready Rental Assistant",
            agent_type=AgentType.PAY_READY
        )
        self.market_data_cache: Dict[str, Any] = {}
        self.neighborhood_scores: Dict[str, float] = {}
        self.tech_amenity_weights = {
            "fiber_internet": 2.0,
            "smart_locks": 1.5,
            "smart_thermostat": 1.3,
            "usb_outlets": 1.2,
            "ev_charging": 1.8,
            "package_lockers": 1.4,
            "app_payments": 1.3,
            "virtual_tours": 1.1
        }
    
    async def analyze_listing(
        self,
        listing_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ApartmentListing:
        """Analyze an apartment listing"""
            id=listing_data["id"],
            address=listing_data["address"],
            price=listing_data["price"],
            sqft=listing_data["sqft"],
            amenities=listing_data.get("amenities", []),
            smart_home_features=listing_data.get("smart_home_features", []),
            neighborhood_score=0.0,
            tech_score=0.0
        )
        
        # Calculate neighborhood score
        listing.neighborhood_score = await self._calculate_neighborhood_score(
            listing.address,
            user_preferences
        )
        
        # Calculate tech score
        listing.tech_score = self._calculate_tech_score(
            listing.amenities + listing.smart_home_features
        )
        
        # Calculate overall score
        listing.overall_score = await self._calculate_overall_score(
            listing,
            user_preferences
        )
        
        return listing
    
    async def _calculate_neighborhood_score(
        self,
        address: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate neighborhood score based on demographics and amenities"""
        cache_key = f"neighborhood:{address}"
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return float(cached)
        
        # Analyze neighborhood using LLM
        prompt = f"""
        """
            context={"query_type": QueryType.ANALYTICAL.value}
        )
        
        # Extract score (simplified - would use structured output)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:

            pass
            score = float(content.split("Score:")[-1].split()[0])
            score = max(0, min(100, score))  # Clamp to 0-100
        except Exception:

            pass
            score = 50.0  # Default
        
        # Cache result
        if self.redis_client:
            await self.redis_client.setex(cache_key, 86400, str(score))  # 24h cache
        
        return score
    
    def _calculate_tech_score(self, features: List[str]) -> float:
        """Calculate technology amenity score"""
        """Calculate overall listing score"""
            "price": 0.3,
            "location": 0.25,
            "tech": 0.2,
            "size": 0.15,
            "amenities": 0.1
        }
        
        # Override with user preferences
        if preferences and "weights" in preferences:
            weights.update(preferences["weights"])
        
        # Price score (inverse - lower is better)
        price_score = max(0, 100 - (listing.price / 50))  # $50/point
        
        # Size score
        size_score = min(100, listing.sqft / 10)  # 10 sqft/point
        
        # Amenity score
        amenity_score = min(100, len(listing.amenities) * 10)  # 10 points per amenity
        
        # Calculate weighted score
        overall = (
            weights["price"] * price_score +
            weights["location"] * listing.neighborhood_score +
            weights["tech"] * listing.tech_score +
            weights["size"] * size_score +
            weights["amenities"] * amenity_score
        )
        
        return overall
    
    async def market_analysis(
        self,
        location: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive market analysis"""
        prompt = f"""
        """
            context={"query_type": QueryType.DEEP_SEARCH.value}
        )
        
        # Parse response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {
            "location": location,
            "analysis": content,
            "timestamp": datetime.utcnow().isoformat(),
            "criteria": criteria
        }
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Pay Ready agent task"""
        self.status = "active"
        self.last_activity = datetime.utcnow()
        
        try:

        
            pass
            task_type = task.get("type", "analyze_listing")
            
            if task_type == "analyze_listing":
                listing = await self.analyze_listing(
                    task["listing_data"],
                    task.get("user_preferences")
                )
                result = {
                    "listing": listing.__dict__,
                    "recommendation": "recommended" if listing.overall_score > 70 else "not_recommended"
                }
            elif task_type == "market_analysis":
                result = await self.market_analysis(
                    task["location"],
                    task["criteria"]
                )
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            self.tasks_completed += 1
            return result
            
        finally:
            self.status = "idle"

class ParagonMedicalResearchAgent(BaseSpecializedAgent):
    """
    """
            agent_id="paragon-001",
            name="Paragon Medical Research Assistant",
            agent_type=AgentType.PARAGON_MEDICAL
        )
        self.trial_cache: Dict[str, ClinicalTrial] = {}
        self.pubmed_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.alert_subscriptions: Dict[str, Dict[str, Any]] = {}
        
    async def search_clinical_trials(
        self,
        conditions: List[str],
        phases: List[str] = ["Phase 3", "Phase 4"],
        location: Optional[Dict[str, float]] = None,
        max_distance_miles: float = 50
    ) -> List[ClinicalTrial]:
        """Search for clinical trials matching criteria"""
        query_parts.extend([f"condition:{cond}" for cond in conditions])
        query_parts.extend([f"phase:{phase}" for phase in phases])
        
        # Use LLM to search and parse trials
        prompt = f"""
        """
            context={"query_type": QueryType.DEEP_SEARCH.value}
        )
        
        # Parse trials from response
        trials = await self._parse_clinical_trials(response)
        
        # Filter by location if provided
        if location:
            trials = await self._filter_by_distance(trials, location, max_distance_miles)
        
        # Calculate relevance scores
        for trial in trials:
            trial.relevance_score = await self._calculate_relevance_score(
                trial,
                conditions,
                phases
            )
        
        # Sort by relevance
        trials.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return trials
    
    async def _parse_clinical_trials(self, response: Dict[str, Any]) -> List[ClinicalTrial]:
        """Parse clinical trials from LLM response"""
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Simple parsing - in production would use structured output
        current_trial = None
        for line in content.split("\n"):
            if "NCT" in line:
                if current_trial:
                    trials.append(current_trial)
                
                # Extract NCT ID
                nct_id = line.split("NCT")[1].split()[0]
                current_trial = ClinicalTrial(
                    nct_id=f"NCT{nct_id}",
                    title="",
                    phase="",
                    conditions=[],
                    interventions=[],
                    eligibility_criteria={},
                    locations=[]
                )
            elif current_trial:
                # Parse other fields (simplified)
                if "Title:" in line:
                    current_trial.title = line.split("Title:")[1].strip()
                elif "Phase:" in line:
                    current_trial.phase = line.split("Phase:")[1].strip()
                # ... parse other fields
        
        if current_trial:
            trials.append(current_trial)
        
        return trials
    
    async def _filter_by_distance(
        self,
        trials: List[ClinicalTrial],
        user_location: Dict[str, float],
        max_distance: float
    ) -> List[ClinicalTrial]:
        """Filter trials by distance from user"""
                lat_diff = location.get("lat", 0) - user_location["lat"]
                lon_diff = location.get("lon", 0) - user_location["lon"]
                distance = (lat_diff**2 + lon_diff**2)**0.5 * 69  # Rough miles conversion
                min_distance = min(min_distance, distance)
            
            if min_distance <= max_distance:
                trial.distance_miles = min_distance
                filtered.append(trial)
        
        return filtered
    
    async def _calculate_relevance_score(
        self,
        trial: ClinicalTrial,
        target_conditions: List[str],
        target_phases: List[str]
    ) -> float:
        """Calculate trial relevance score"""
        im_keywords = ["internal medicine", "pain management", "chronic pain", "medical device"]
        if any(keyword in trial.title.lower() for keyword in im_keywords):
            score += 25
        
        # Distance factor (if available)
        if trial.distance_miles is not None:
            distance_score = max(0, 25 - (trial.distance_miles / 2))  # Lose 1 point per 2 miles
            score += distance_score
        
        return min(100, score)
    
    async def search_pubmed(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search PubMed for relevant literature"""
        cache_key = f"pubmed:{query}:{json.dumps(filters or {})}"
        if cache_key in self.pubmed_cache:
            return self.pubmed_cache[cache_key]
        
        # Use LLM to search PubMed
        prompt = f"""
        """
            context={"query_type": QueryType.DEEP_SEARCH.value}
        )
        
        # Parse results
        results = []  # Would implement parsing logic
        
        # Cache results
        self.pubmed_cache[cache_key] = results
        
        return results
    
    async def setup_trial_alert(
        self,
        user_id: str,
        criteria: Dict[str, Any],
        notification_method: str = "email"
    ) -> Dict[str, Any]:
        """Set up automated alerts for new matching trials"""
        alert_id = f"alert_{user_id}_{datetime.utcnow().timestamp()}"
        
        self.alert_subscriptions[alert_id] = {
            "user_id": user_id,
            "criteria": criteria,
            "notification_method": notification_method,
            "created_at": datetime.utcnow().isoformat(),
            "last_checked": datetime.utcnow().isoformat(),
            "matches_found": 0
        }
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.hset(
                f"trial_alerts:{user_id}",
                alert_id,
                json.dumps(self.alert_subscriptions[alert_id])
            )
        
        return {
            "alert_id": alert_id,
            "status": "active",
            "criteria": criteria
        }
    
    async def check_trial_alerts(self):
        """Check all active alerts for new matches"""
                    conditions=alert_data["criteria"].get("conditions", []),
                    phases=alert_data["criteria"].get("phases", ["Phase 3", "Phase 4"])
                )
                
                # Check for new matches since last check
                last_checked = datetime.fromisoformat(alert_data["last_checked"])
                new_trials = [
                    trial for trial in trials
                    if trial.relevance_score > 70  # High relevance only
                ]
                
                if new_trials:
                    # Send notification (simplified)
                    logger.info(f"Found {len(new_trials)} new trials for alert {alert_id}")
                    alert_data["matches_found"] += len(new_trials)
                
                alert_data["last_checked"] = datetime.utcnow().isoformat()
                
            except Exception:

                
                pass
                logger.error(f"Error checking alert {alert_id}: {e}")
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a medical research agent task"""
        self.status = "active"
        self.last_activity = datetime.utcnow()
        
        try:

        
            pass
            task_type = task.get("type", "search_trials")
            
            if task_type == "search_trials":
                trials = await self.search_clinical_trials(
                    conditions=task["conditions"],
                    phases=task.get("phases", ["Phase 3", "Phase 4"]),
                    location=task.get("location"),
                    max_distance_miles=task.get("max_distance", 50)
                )
                result = {
                    "trials": [trial.__dict__ for trial in trials[:10]],  # Top 10
                    "total_found": len(trials)
                }
            elif task_type == "search_literature":
                results = await self.search_pubmed(
                    task["query"],
                    task.get("filters")
                )
                result = {"articles": results}
            elif task_type == "setup_alert":
                result = await self.setup_trial_alert(
                    task["user_id"],
                    task["criteria"],
                    task.get("notification_method", "email")
                )
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            self.tasks_completed += 1
            return result
            
        finally:
            self.status = "idle"

# Agent Registry
SPECIALIZED_AGENTS = {
    AgentType.PERSONAL.value: PersonalAgent(),
    AgentType.PAY_READY.value: PayReadyAgent(),
    AgentType.PARAGON_MEDICAL.value: ParagonMedicalResearchAgent()
}

async def get_specialized_agent(agent_type: str) -> BaseSpecializedAgent:
    """Get a specialized agent by type"""
        raise ValueError(f"Unknown agent type: {agent_type}")
    return agent

async def process_agent_task(
    agent_type: str,
    task: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a task with the appropriate specialized agent"""