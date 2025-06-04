# TODO: Consider adding connection pooling configuration
"""
"""
    """
    COMPANY_SUFFIXES = {"inc", "incorporated", "corp", "corporation", "llc", "ltd", "limited", "co", "company", "gmbh", "ag", "sa", "srl", "bv", "nv", "plc", "lp", "llp"}
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
            score_val = result[1] # Original score 0-100
            normalized_score = score_val / 100.0
            unified_id, existing_confidence = candidate_map[matched_name]

            # Adjust confidence based on context match (example)
            if context and context.get("company"):
                company_match = await self._check_person_company_match(unified_id, context["company"])
                if company_match:
                    normalized_score = min(normalized_score * 1.2, 1.0) # Boost confidence

            logger.debug(f"Fuzzy match for person '{name}': Found candidate '{matched_name}' with score {score_val:.2f} (normalized {normalized_score:.2f}). Unified ID: {unified_id}")
            return (unified_id, normalized_score)
        else:
            top_candidate_name = result[0] if result else "N/A"
            top_candidate_score = result[1] if result else "N/A"
            logger.debug(f"Fuzzy match for person '{name}': No candidate met threshold (name_threshold: {self.name_threshold}). Top candidate: {top_candidate_name} with score {top_candidate_score}")
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
            score_val = result[1] # Original score 0-100
            normalized_score = score_val / 100.0
            unified_id, existing_confidence = candidate_map[matched_name]
            logger.debug(f"Fuzzy match for company '{name}' (normalized to '{normalized_name}'): Found candidate '{matched_name}' with score {score_val:.2f}. Unified ID: {unified_id}")
            return (unified_id, normalized_score)
        else:
            top_candidate_name = result[0] if result else "N/A"
            top_candidate_score = result[1] if result else "N/A"
            logger.debug(f"Fuzzy match for company '{name}' (normalized to '{normalized_name}'): No candidate met threshold (company_threshold: {self.company_threshold}). Top candidate: {top_candidate_name} with score {top_candidate_score}")
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
        logger.info(f"Creating new person entity. Name: '{name}', Email: '{email}', Source: {source_system}:{source_id}, Context: {context}")
        unified_id = str(uuid.uuid4())
        metadata = {
            "name": name,
            "email": self._normalize_email(email) if email else None,
            "created_at": datetime.utcnow().isoformat(),
            "source_systems": [source_system] if source_system else [],
            # Store original context if provided
            "initial_context": context if context else {}
        }

        # Merging additional_context into metadata directly if it was passed as 'context'
        if context: # This 'context' is the 'additional_context' from resolve_person
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
        logger.info(f"Creating new company entity. Name: '{name}', Domain: '{domain}', Source: {source_system}:{source_id}, Context: {context}")
        unified_id = str(uuid.uuid4())
        metadata = {
            "name": name,
            "normalized_name": self._normalize_company_name(name) if name else None,
            "domain": domain.lower().strip() if domain else None,
            "created_at": datetime.utcnow().isoformat(),
            "source_systems": [source_system] if source_system else [],
            "initial_context": context if context else {}
        }

        if context: # This 'context' is the 'additional_context' from resolve_company
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
        logger.info(f"Adding new source mapping for {entity_type} UID {unified_id}: {source_system}:{source_id} with confidence {confidence_score:.2f}")
        cache_key = f"{source_system}:{source_id}"

        table_name = "pay_ready_person_mappings" if entity_type == "person" else "pay_ready_company_mappings"
        cache_dict = self.cache["persons"] if entity_type == "person" else self.cache["companies"]

        if cache_key in cache_dict and cache_dict[cache_key] == unified_id:
            logger.debug(f"Source mapping {cache_key} to UID {unified_id} already in cache and DB (assumed). Skipping redundant add.")
            return

        # Fetch current main entity metadata to update its source_systems list
        main_entity_data = await self.postgres.fetchrow(
            f"SELECT metadata FROM {table_name} WHERE unified_id = $1", unified_id
        )

        if main_entity_data:
            current_metadata = main_entity_data.get("metadata", {})
            if isinstance(current_metadata, str):
                try:
                    current_metadata = json.loads(current_metadata)
                except json.JSONDecodeError:
                    logger.error(f"Could not parse existing metadata for {entity_type} UID {unified_id}. Initializing new metadata.")
                    current_metadata = {}

            source_systems_list = current_metadata.get("source_systems", [])
            if source_system not in source_systems_list: # Avoid duplicate entries
                source_systems_list.append(source_system)
                current_metadata["source_systems"] = source_systems_list

                # TODO: Consider if new source_id's metadata (name, email, domain) should enrich the main entity's metadata.
                # This would require fetching the new source's data, comparing, and merging.
                # For now, just updating the source_systems list.
                # Example: current_metadata["name"] = new_name if new_name is richer and confidence is high.

                await self.postgres.execute_raw(
                    f"UPDATE {table_name} SET metadata = $1, updated_at = NOW() WHERE unified_id = $2",
                    json.dumps(current_metadata),
                    unified_id,
                )
                logger.debug(f"Updated source_systems list in main entity {entity_type} UID {unified_id}.")

        # Add the specific source_id to unified_id mapping
        # This table (`pay_ready_person_source_mappings` or `pay_ready_company_source_mappings`)
        # should exist and track each source_id to its unified_id.
        # The prompt implies this table is `pay_ready_person_mappings` itself if it can have multiple rows per unified_id (one per source_id).
        # Assuming `pay_ready_person_mappings` and `pay_ready_company_mappings` store one row per source_system:source_id combination.
        # If so, an INSERT or UPDATE ON CONFLICT is needed here.
        # The current logic seems to update the main unified entity's metadata's source_systems list.
        # And the cache update below handles the direct source_system:source_id -> unified_id link.
        # The crucial part is ensuring the DB also has this specific mapping if it's not the main entity row.
        # For now, the code structure suggests the main table itself might be what's queried by source_system+source_id.
        # This part of the logic might need further clarification based on exact DB schema for source mappings vs unified entities.
        # The current code for _add_source_mapping primarily updates the list of source systems in the *main* entity's metadata.
        # It does not seem to insert a new row into `pay_ready_person_mappings` for the new source_id if it's different from the one that created the entity.
        # This seems to be the intention of the original code.

        # Update cache
        cache_dict[cache_key] = unified_id
        logger.info(f"Cached new source mapping: {cache_key} -> {unified_id}")

        # If the mapping was for an email or domain, update those specific caches too
        # This part is implicitly handled by resolve_person/resolve_company if they call _add_source_mapping
        # after finding a match via email/domain and then wanting to link a new source_id to that same unified_id.
        # No, this needs to be explicit if _add_source_mapping is called with a new source_id for an existing entity.
        # The metadata for the new source_id (which might contain email/domain) should be used.
        # This requires fetching the metadata for the newly added source_id.
        # This is getting complex; the primary goal of _add_source_mapping is to link the source_system:source_id to the unified_id.
        # The original code for `_add_source_mapping` does not update email/domain caches.
        # Let's stick to the original scope first and enhance if needed.
        # The crucial DB operation for source mapping is:
        # INSERT INTO pay_ready_person_source_mappings (unified_id, source_system, source_id, metadata, confidence_score, created_at, updated_at)
        # VALUES ($1, $2, $3, $4, $5, NOW(), NOW()) ON CONFLICT (source_system, source_id) DO UPDATE SET ...
        # (This assumes a separate source_mappings table. If not, the logic in resolve_person/company for new entities is what creates these mappings).
        # The current code seems to assume that pay_ready_person_mappings IS the source mapping table.

    async def _check_person_company_match(self, unified_person_id: str, company_name: str) -> bool:
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
        normalized = name.lower().strip()

        # Remove punctuation
        # A more robust way is to use regex for punctuation removal: re.sub(r'[^\w\s]', '', normalized)
        for char in ".,;:!?()[]{}'\"`~@#$%^&*-_+=<>|\\/": # Expanded punctuation list
            normalized = normalized.replace(char, "")

        # Normalize whitespace (multiple spaces to one, strip leading/trailing)
        normalized = " ".join(normalized.split())


        # Remove common suffixes using the class attribute
        if normalized: # Ensure there's something to split
            words = normalized.split()
            # Filter out suffixes and reconstruct. Handles cases where all words might be suffixes.
            filtered_words = [w for w in words if w not in self.COMPANY_SUFFIXES]
            normalized = " ".join(filtered_words).strip()

        return normalized

    async def run_resolution_batch(self):
        """
        Periodically re-evaluates existing entity mappings to consolidate entities,
        apply updated normalization/matching logic, or incorporate new information.
        This assumes `pay_ready_person_mappings` and `pay_ready_company_mappings` store
        one row PER SOURCE MAPPING (source_system, source_id) to a unified_id, and
        contain `metadata` with the original data used for resolution.
        """
        logger.info("Starting entity re-resolution batch run...")
        processed_persons = 0
        person_changes_detected = 0
        processed_companies = 0
        company_changes_detected = 0

        # Re-resolve Persons
        # Fetch distinct source mappings. If a unified_id has multiple sources, this will process each.
        # The order by created_at DESC might help prioritize newer data if resolver logic uses it,
        # but resolve_person should be idempotent or handle context updates carefully.
        person_mappings_to_check = await self.postgres.fetch_raw(
            """
            SELECT source_system, source_id, unified_id, metadata
            FROM pay_ready_person_mappings
            WHERE unified_id IS NOT NULL ORDER BY created_at DESC;
            """
            # Consider adding LIMIT/OFFSET for very large datasets to process in smaller batches.
        )
        logger.info(f"Found {len(person_mappings_to_check)} person source mappings to re-evaluate.")

        for record in person_mappings_to_check:
            processed_persons += 1
            metadata = record.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse metadata for person source {record['source_system']}:{record['source_id']}. Skipping.")
                    continue

            name = metadata.get("name") # Original name from this source
            email = metadata.get("email") # Original email from this source
            current_unified_id = str(record.get("unified_id"))
            additional_context = metadata.get("initial_context") # Or any other relevant context stored

            try:
                # Re-resolve without the current source_system:source_id link to see if it merges elsewhere
                # This is complex. A simpler approach is to just call resolve_person again.
                # If resolve_person is truly idempotent or can improve matches, this is fine.
                # For a true re-resolution where an entity might merge, the resolver needs to be
                # able to ignore its own current mapping temporarily.
                # For now, assume resolve_person can be called again.
                new_unified_id = await self.resolve_person(
                    name=name,
                    email=email,
                    source_system=record["source_system"], # Pass current source for context
                    source_id=record["source_id"],         # Pass current source_id
                    additional_context=additional_context
                )

                if new_unified_id and new_unified_id != current_unified_id:
                    person_changes_detected += 1
                    logger.info(
                        f"Entity Batch Re-resolution for PERSON: "
                        f"Source {record['source_system']}:{record['source_id']}. "
                        f"Original UID: {current_unified_id}, Newly Resolved UID: {new_unified_id}. Potential merge/update needed."
                    )
                    # TODO: Implement actual merge logic here if IDs change.
                    # This might involve updating all records pointing to current_unified_id to new_unified_id,
                    # and then potentially deleting/archiving the old current_unified_id entity.
                    # This is a complex operation and needs careful handling (e.g., in a separate merge task).
            except Exception as e:
                logger.error(f"Error re-resolving person {record['source_system']}:{record['source_id']}: {e}", exc_info=True)


        # Re-resolve Companies
        company_mappings_to_check = await self.postgres.fetch_raw(
            """
            SELECT source_system, source_id, unified_id, metadata
            FROM pay_ready_company_mappings
            WHERE unified_id IS NOT NULL ORDER BY created_at DESC;
            """
        )
        logger.info(f"Found {len(company_mappings_to_check)} company source mappings to re-evaluate.")

        for record in company_mappings_to_check:
            processed_companies += 1
            metadata = record.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse metadata for company source {record['source_system']}:{record['source_id']}. Skipping.")
                    continue

            name = metadata.get("name")
            domain = metadata.get("domain")
            current_unified_id = str(record.get("unified_id"))
            additional_context = metadata.get("initial_context")

            try:
                new_unified_id = await self.resolve_company(
                    name=name,
                    domain=domain,
                    source_system=record["source_system"],
                    source_id=record["source_id"],
                    additional_context=additional_context
                )

                if new_unified_id and new_unified_id != current_unified_id:
                    company_changes_detected += 1
                    logger.info(
                        f"Entity Batch Re-resolution for COMPANY: "
                        f"Source {record['source_system']}:{record['source_id']}. "
                        f"Original UID: {current_unified_id}, Newly Resolved UID: {new_unified_id}. Potential merge/update needed."
                    )
                    # TODO: Implement actual merge logic here.
            except Exception as e:
                logger.error(f"Error re-resolving company {record['source_system']}:{record['source_id']}: {e}", exc_info=True)

        logger.info(
            f"Entity re-resolution batch run completed. "
            f"Persons processed: {processed_persons}, potential changes: {person_changes_detected}. "
            f"Companies processed: {processed_companies}, potential changes: {company_changes_detected}."
        )

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
