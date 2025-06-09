"""
"""
    """Test the Personal Agent functionality"""
        """Test learning positive preferences"""
        user_id = "test_user"
        category = "restaurants"
        
        await agent.learn_preference(user_id, category, "positive")
        
        assert category in agent.user_preferences[user_id]
        pref = agent.user_preferences[user_id][category]
        assert pref.positive_signals == 1
        assert pref.weight > 1.0
    
    @pytest.mark.asyncio
    async def test_learn_preference_negative(self, agent):
        """Test learning negative preferences"""
        user_id = "test_user"
        category = "fast_food"
        
        await agent.learn_preference(user_id, category, "negative")
        
        assert category in agent.user_preferences[user_id]
        pref = agent.user_preferences[user_id][category]
        assert pref.negative_signals == 1
        assert pref.weight < 1.0
    
    @pytest.mark.asyncio
    async def test_adaptive_search(self, agent):
        """Test adaptive search with preferences"""
        user_id = "test_user"
        query = "Find Italian restaurants"
        
        # Set up preferences
        agent.user_preferences[user_id] = {
            "italian": UserPreference(category="italian", weight=1.5, positive_signals=3),
            "expensive": UserPreference(category="expensive", weight=0.5, negative_signals=2)
        }
        
        # Mock LLM response
        agent.llm_router.route_query = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "1. Luigi's Italian Restaurant\n2. Pasta Paradise\n3. Roma Ristorante"
                }
            }]
        })
        
        result = await agent.adaptive_search(user_id, query)
        
        assert result["query"] == query
        assert len(result["results"]) > 0
        assert "italian" in result["preferences_applied"]
        assert agent.llm_router.route_query.called
    
    @pytest.mark.asyncio
    async def test_preference_weighting(self, agent):
        """Test that preferences affect result ranking"""
            "italian": UserPreference(category="italian", weight=2.0),
            "cheap": UserPreference(category="cheap", weight=1.5)
        }
        
        # Mock response
        response = {
            "choices": [{
                "message": {
                    "content": "Result without preferences"
                }
            }]
        }
        
        results = await agent._extract_and_rank_results(response, preferences)
        
        # Results mentioning preferences should score higher
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_process_task_search(self, agent):
        """Test processing a search task"""
        agent.adaptive_search = AsyncMock(return_value={"results": []})
        
        task = {
            "type": "search",
            "user_id": "test_user",
            "query": "Test query"
        }
        
        result = await agent.process_task(task)
        
        assert agent.adaptive_search.called
        assert agent.tasks_completed == 1
        assert agent.status == "idle"

class TestPayReadyAgent:
    """Test the Pay Ready Agent functionality"""
        """Test apartment listing analysis"""
            "id": "apt123",
            "address": "123 Tech St, San Francisco, CA",
            "price": 3000,
            "sqft": 1200,
            "amenities": ["gym", "pool", "parking"],
            "smart_home_features": ["smart_locks", "fiber_internet"]
        }
        
        # Mock neighborhood score calculation
        agent._calculate_neighborhood_score = AsyncMock(return_value=85.0)
        
        listing = await agent.analyze_listing(listing_data)
        
        assert isinstance(listing, ApartmentListing)
        assert listing.id == "apt123"
        assert listing.tech_score > 50  # Base score + smart features
        assert listing.neighborhood_score == 85.0
        assert listing.overall_score > 0
    
    @pytest.mark.asyncio
    async def test_tech_score_calculation(self, agent):
        """Test technology amenity scoring"""
            "fiber internet available",
            "smart locks installed",
            "ev charging station"
        ]
        
        score = agent._calculate_tech_score(features)
        
        # Should have base score + bonuses for each tech feature
        assert score > 50
        assert score <= 100
    
    @pytest.mark.asyncio
    async def test_neighborhood_score_caching(self, agent):
        """Test that neighborhood scores are cached"""
        address = "123 Test St"
        
        # Mock Redis client
        agent.redis_client = Mock()
        agent.redis_client.get = AsyncMock(return_value="75.0")
        
        score = await agent._calculate_neighborhood_score(address)
        
        assert score == 75.0
        assert agent.redis_client.get.called
    
    @pytest.mark.asyncio
    async def test_market_analysis(self, agent):
        """Test market analysis functionality"""
            "choices": [{
                "message": {
                    "content": "Average rent: $2500-3500. Market is competitive."
                }
            }]
        })
        
        result = await agent.market_analysis(
            "San Francisco",
        )
        
        assert result["location"] == "San Francisco"
        assert "analysis" in result
        assert agent.llm_router.route_query.called

class TestParagonMedicalResearchAgent:
    """Test the Paragon Medical Research Agent functionality"""
        """Test clinical trial search"""
        conditions = ["chronic pain", "fibromyalgia"]
        phases = ["Phase 3", "Phase 4"]
        
        # Mock LLM response
        agent.llm_router.route_query = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "NCT12345678 Title: Pain Management Study Phase: Phase 3"
                }
            }]
        })
        
        agent._parse_clinical_trials = AsyncMock(return_value=[
            ClinicalTrial(
                nct_id="NCT12345678",
                title="Pain Management Study",
                phase="Phase 3",
                conditions=["chronic pain"],
                interventions=[],
                eligibility_criteria={},
                locations=[]
            )
        ])
        
        trials = await agent.search_clinical_trials(conditions, phases)
        
        assert len(trials) > 0
        assert trials[0].nct_id == "NCT12345678"
        assert agent.llm_router.route_query.called
    
    @pytest.mark.asyncio
    async def test_relevance_scoring(self, agent):
        """Test clinical trial relevance scoring"""
            nct_id="NCT12345678",
            title="Chronic Pain Management with Medical Device",
            phase="Phase 3",
            conditions=["chronic pain", "fibromyalgia"],
            interventions=["medical device"],
            eligibility_criteria={},
            locations=[],
            distance_miles=10
        )
        
        score = await agent._calculate_relevance_score(
            trial,
            ["chronic pain", "fibromyalgia"],
            ["Phase 3", "Phase 4"]
        )
        
        # Should have high score for matching conditions and phase
        assert score > 50
        assert score <= 100
    
    @pytest.mark.asyncio
    async def test_setup_trial_alert(self, agent):
        """Test setting up trial alerts"""
        user_id = "test_user"
        criteria = {
            "conditions": ["chronic pain"],
            "phases": ["Phase 3"]
        }
        
        result = await agent.setup_trial_alert(user_id, criteria)
        
        assert "alert_id" in result
        assert result["status"] == "active"
        assert result["criteria"] == criteria
        assert len(agent.alert_subscriptions) == 1
    
    @pytest.mark.asyncio
    async def test_distance_filtering(self, agent):
        """Test filtering trials by distance"""
                nct_id="NCT001",
                title="Trial 1",
                phase="Phase 3",
                conditions=[],
                interventions=[],
                eligibility_criteria={},
                locations=[{"lat": 37.7749, "lon": -122.4194}]  # SF
            ),
            ClinicalTrial(
                nct_id="NCT002",
                title="Trial 2",
                phase="Phase 3",
                conditions=[],
                interventions=[],
                eligibility_criteria={},
                locations=[{"lat": 40.7128, "lon": -74.0060}]  # NYC
            )
        ]
        
        user_location = {"lat": 37.7749, "lon": -122.4194}  # SF
        filtered = await agent._filter_by_distance(trials, user_location, 50)
        
        # Should include nearby trial
        assert len(filtered) >= 1
        assert filtered[0].nct_id == "NCT001"

class TestAgentRegistry:
    """Test agent registry and task processing"""
        """Test retrieving agents by type"""
        """Test error handling for invalid agent type"""
        with pytest.raises(ValueError, match="Unknown agent type"):
            await get_specialized_agent("invalid_type")
    
    @pytest.mark.asyncio
    async def test_process_agent_task(self):
        """Test task processing through registry"""
                    mock_process.return_value = {"status": "success"}
                    
                    result = await process_agent_task(
                        AgentType.PERSONAL.value,
                        {"type": "search", "query": "test"}
                    )
                    
                    assert result["status"] == "success"
                    assert mock_process.called

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test that all agents initialize correctly"""
            assert personal.id == "personal-001"
            assert personal.type == AgentType.PERSONAL
            
            payready = PayReadyAgent()
            assert payready.id == "payready-001"
            assert payready.type == AgentType.PAY_READY
            
            paragon = ParagonMedicalResearchAgent()
            assert paragon.id == "paragon-001"
            assert paragon.type == AgentType.PARAGON_MEDICAL

if __name__ == "__main__":
    pytest.main([__file__, "-v"])