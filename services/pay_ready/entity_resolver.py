# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
            "persons": {},  # source_system:source_id -> unified_id
            "companies": {},  # source_system:source_id -> unified_id
            "emails": {},  # email -> unified_id
            "domains": {},  # domain -> company_unified_id
        }
        self.name_threshold = 85  # Minimum fuzzy match score
        self.company_threshold = 80
        self._cache_loaded = False

    async def initialize(self):
        """Load existing mappings into cache"""
        logger.info("Loading entity mappings into cache")

        # Load person mappings
        persons = await self.postgres.fetch_raw(
            """
        """
            cache_key = f"{person['source_system']}:{person['source_id']}"
            self.cache["persons"][cache_key] = str(person["unified_id"])

            # Cache email mapping if available
            metadata = person.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            email = metadata.get("email")
            if email:
                self.cache["emails"][email.lower()] = str(person["unified_id"])

        # Load company mappings
        companies = await self.postgres.fetch_raw(
            """
        """
            cache_key = f"{company['source_system']}:{company['source_id']}"
            self.cache["companies"][cache_key] = str(company["unified_id"])

            # Cache domain mapping if available
            metadata = company.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            domain = metadata.get("domain")
            if domain:
                self.cache["domains"][domain.lower()] = str(company["unified_id"])

        self._cache_loaded = True
        logger.info(
            f"Loaded {len(self.cache['persons'])} person mappings and "
            f"{len(self.cache['companies'])} company mappings"
        )

    async def resolve_person(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        source_system: Optional[str] = None,
        source_id: Optional[str] = None,
        additional_context: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        """
            cache_key = f"{source_system}:{source_id}"
            if cache_key in self.cache["persons"]:
                return self.cache["persons"][cache_key]

        # Try email exact match
        if email:
            normalized_email = self._normalize_email(email)
            if normalized_email:
                # Check cache
                if normalized_email in self.cache["emails"]:
                    unified_id = self.cache["emails"][normalized_email]
                    # Update source mapping if we have it
                    if source_system and source_id:
                        await self._add_source_mapping("person", unified_id, source_system, source_id)
                    return unified_id

                # Check database
                result = await self.postgres.fetchrow(
                    """
                """
                    unified_id = str(result["unified_id"])
                    self.cache["emails"][normalized_email] = unified_id
                    if source_system and source_id:
                        await self._add_source_mapping("person", unified_id, source_system, source_id)
                    return unified_id

        # Try fuzzy name matching
        if name:
            match_result = await self._fuzzy_match_person(name, additional_context)
            if match_result:
                unified_id, confidence = match_result
                if source_system and source_id:
                    await self._add_source_mapping(
                        "person", unified_id, source_system, source_id, confidence_score=confidence
                    )
                return unified_id

        # No match found - create new unified ID
        return await self._create_new_person(name, email, source_system, source_id, additional_context)

    async def resolve_company(
        self,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        source_system: Optional[str] = None,
        source_id: Optional[str] = None,
        additional_context: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        """
            cache_key = f"{source_system}:{source_id}"
            if cache_key in self.cache["companies"]:
                return self.cache["companies"][cache_key]

        # Try domain exact match
        if domain:
            normalized_domain = domain.lower().strip()
            if normalized_domain in self.cache["domains"]:
                unified_id = self.cache["domains"][normalized_domain]
                if source_system and source_id:
                    await self._add_source_mapping("company", unified_id, source_system, source_id)
                return unified_id

            # Check database
            result = await self.postgres.fetchrow(
                """
            """
                unified_id = str(result["unified_id"])
                self.cache["domains"][normalized_domain] = unified_id
                if source_system and source_id:
                    await self._add_source_mapping("company", unified_id, source_system, source_id)
                return unified_id

        # Try fuzzy name matching
        if name:
            match_result = await self._fuzzy_match_company(name, additional_context)
            if match_result:
                unified_id, confidence = match_result
                if source_system and source_id:
                    await self._add_source_mapping(
                        "company", unified_id, source_system, source_id, confidence_score=confidence
                    )
                return unified_id

        # No match found - create new unified ID
        return await self._create_new_company(name, domain, source_system, source_id, additional_context)

    async def _fuzzy_match_person(self, name: str, context: Optional[Dict] = None) -> Optional[Tuple[str, float]]:
        """
        """
            """
        """
            cand_name = candidate["name"]
            if cand_name:
                # If we have company context, prefer matches from same company
                if context and context.get("company") and candidate.get("company"):
                    if context["company"].lower() == candidate["company"].lower():
                        # Boost score for same company
                        candidate_names.append(cand_name)
                        candidate_map[cand_name] = (
                            str(candidate["unified_id"]),
                            candidate.get("confidence_score", 1.0),
                        )
                else:
                    candidate_names.append(cand_name)
                    candidate_map[cand_name] = (str(candidate["unified_id"]), candidate.get("confidence_score", 1.0))

        # Perform fuzzy matching
        result = process.extractOne(name, candidate_names, scorer=fuzz.token_sort_ratio)

        if result and result[1] >= self.name_threshold:
            matched_name = result[0]
            score = result[1] / 100.0  # Normalize to 0-1
            unified_id, existing_confidence = candidate_map[matched_name]

            # Adjust confidence based on context match
            if context and context.get("company"):
                # Check if the matched person is from the same company
                company_match = await self._check_person_company_match(unified_id, context["company"])
                if company_match:
                    score = min(score * 1.2, 1.0)  # Boost confidence

            return (unified_id, score)

        return None

    async def _fuzzy_match_company(self, name: str, context: Optional[Dict] = None) -> Optional[Tuple[str, float]]:
        """
        """
            """
        """
            cand_name = candidate.get("normalized_name") or candidate.get("name")
            if cand_name:
                candidate_names.append(cand_name)
                candidate_map[cand_name] = (str(candidate["unified_id"]), candidate.get("confidence_score", 1.0))

        # Perform fuzzy matching
        result = process.extractOne(normalized_name, candidate_names, scorer=fuzz.token_sort_ratio)

        if result and result[1] >= self.company_threshold:
            matched_name = result[0]
            score = result[1] / 100.0  # Normalize to 0-1
            unified_id, existing_confidence = candidate_map[matched_name]
            return (unified_id, score)

        return None

    async def _create_new_person(
        self,
        name: Optional[str],
        email: Optional[str],
        source_system: Optional[str],
        source_id: Optional[str],
        context: Optional[Dict],
    ) -> str:
        """Create a new unified person ID"""
            "name": name,
            "email": self._normalize_email(email) if email else None,
            "created_at": datetime.utcnow().isoformat(),
            "source_systems": [source_system] if source_system else [],
        }

        if context:
            metadata.update(context)

        # Insert into database
        await self.postgres.execute_raw(
            """
        """
            cache_key = f"{source_system}:{source_id}"
            self.cache["persons"][cache_key] = unified_id

        if email:
            normalized_email = self._normalize_email(email)
            if normalized_email:
                self.cache["emails"][normalized_email] = unified_id

        logger.info(f"Created new person with unified ID: {unified_id}")
        return unified_id

    async def _create_new_company(
        self,
        name: Optional[str],
        domain: Optional[str],
        source_system: Optional[str],
        source_id: Optional[str],
        context: Optional[Dict],
    ) -> str:
        """Create a new unified company ID"""
            "name": name,
            "normalized_name": self._normalize_company_name(name) if name else None,
            "domain": domain.lower().strip() if domain else None,
            "created_at": datetime.utcnow().isoformat(),
            "source_systems": [source_system] if source_system else [],
        }

        if context:
            metadata.update(context)

        # Insert into database
        await self.postgres.execute_raw(
            """
        """
            cache_key = f"{source_system}:{source_id}"
            self.cache["companies"][cache_key] = unified_id

        if domain:
            normalized_domain = domain.lower().strip()
            self.cache["domains"][normalized_domain] = unified_id

        logger.info(f"Created new company with unified ID: {unified_id}")
        return unified_id

    async def _add_source_mapping(
        self, entity_type: str, unified_id: str, source_system: str, source_id: str, confidence_score: float = 1.0
    ):
        """Add a new source system mapping for an existing entity"""
        cache_key = f"{source_system}:{source_id}"
        cache_dict = self.cache["persons"] if entity_type == "person" else self.cache["companies"]

        if cache_key in cache_dict:
            return

        # Get existing metadata
        result = await self.postgres.fetchrow(
            """
        """
            metadata = result["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Add source system to list
            source_systems = metadata.get("source_systems", [])
            if source_system not in source_systems:
                source_systems.append(source_system)
                metadata["source_systems"] = source_systems

            # Insert new mapping
            await self.postgres.execute_raw(
                """
            """
        """Check if a person is associated with a company"""
            """
        """
            f"%{company_name}%",
        )

        return result is not None

    def _normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize and validate email address"""
            logger.warning(f"Invalid email address: {email}")
            return None

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching"""
            return ""

        # Remove common suffixes
        suffixes = [
            "inc",
            "incorporated",
            "corp",
            "corporation",
            "llc",
            "ltd",
            "limited",
            "co",
            "company",
            "gmbh",
            "ag",
            "sa",
            "srl",
            "bv",
            "nv",
        ]

        normalized = name.lower().strip()

        # Remove punctuation
        for char in ".,;:!?()[]{}":
            normalized = normalized.replace(char, "")

        # Remove common suffixes
        words = normalized.split()
        filtered_words = []

        # TODO: Consider using list comprehension for better performance


        for word in words:
            if word not in suffixes:
                filtered_words.append(word)

        return " ".join(filtered_words).strip()

    async def run_resolution_batch(self):
        """Run batch entity resolution for unresolved entities"""
        logger.info("Running batch entity resolution")

        # Find unresolved persons (those without unified_id in metadata)
        unresolved_persons = await self.postgres.fetch_raw(
            """
        """
            metadata = person.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            unified_id = await self.resolve_person(
                name=metadata.get("user_name"),
                email=metadata.get("user_email"),
                source_system=person["source_system"],
                source_id=person["source_id"],
            )

            if unified_id:
                # Update interactions with resolved ID
                await self.postgres.execute_raw(
                    """
                """
                    person["source_system"],
                    person["source_id"],
                )

                resolved_count += 1

        logger.info(f"Resolved {resolved_count} persons in batch")

    async def get_entity_details(self, unified_id: str, entity_type: str = "person") -> Optional[Dict]:
        """Get detailed information about an entity"""
            """
        """
            metadata = mapping.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Merge metadata, preferring higher confidence sources
            for key, value in metadata.items():
                if key not in merged_metadata and value:
                    merged_metadata[key] = value

            source_systems.append(
                {
                    "system": mapping["source_system"],
                    "id": mapping["source_id"],
                    "confidence": mapping["confidence_score"],
                }
            )

        return {
            "unified_id": unified_id,
            "entity_type": entity_type,
            "metadata": merged_metadata,
            "source_systems": source_systems,
            "created_at": mappings[0]["created_at"].isoformat() if mappings else None,
        }
