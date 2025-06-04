#!/usr/bin/env python3
"""
"""
    """Configuration for data source connections."""
    """Base class for all data source integrations."""
        """Get or create HTTP session."""
            headers = {"User-Agent": "cherry_ai-AI/1.0"}
            if self.config.additional_headers:
                headers.update(self.config.additional_headers)

            self._session = aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        """Close the session."""
        """Sync data from source. To be implemented by subclasses."""
    """Integration for Gong.io call intelligence platform."""
        """Sync calls, meetings, and insights from Gong."""
        """Sync call recordings and transcripts."""
        url = f"{self.config.base_url}/v2/calls"

        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.config.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json",
        }

        params = {"fromDateTime": since.isoformat(), "limit": 100}

        count = 0
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

                for call in data.get("calls", []):
                    # Process call transcript
                    if call.get("transcript"):
                        transcript_content = " ".join(
                            [
                                f"{speaker['speakerId']}: {sentence['text']}"
                                for speaker in call.get("speakers", [])
                                for sentence in speaker.get("sentences", [])
                            ]
                        )

                        await self.memory_system.add_memory(
                            user_id=self.user_id,
                            content=transcript_content,
                            source="gong",
                            source_metadata={
                                "type": "call_transcript",
                                "call_id": call.get("id"),
                                "title": call.get("title"),
                                "duration": call.get("duration"),
                                "participants": [p.get("emailAddress") for p in call.get("participants", [])],
                                "date": call.get("actualStart"),
                                "deal_id": call.get("dealId"),
                            },
                            context_tags=["sales_call", "gong", "transcript"],
                        )
                        count += 1

                    # Process call insights
                    if call.get("insights"):
                        insights_content = json.dumps(call["insights"], indent=2)

                        await self.memory_system.add_memory(
                            user_id=self.user_id,
                            content=f"Call Insights: {insights_content}",
                            source="gong",
                            source_metadata={
                                "type": "call_insights",
                                "call_id": call.get("id"),
                                "insights": call["insights"],
                            },
                            context_tags=["sales_insights", "gong", "analytics"],
                        )
                        count += 1

        return count

    async def _sync_insights(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync meeting insights and analytics."""
        """Sync deal intelligence."""
    """Integration for Salesforce CRM."""
        """Authenticate with Salesforce using OAuth."""
        auth_url = f"{self.config.base_url}/services/oauth2/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.api_key,
            "client_secret": self.config.additional_headers.get("client_secret"),
        }

        async with session.post(auth_url, data=data) as response:
            if response.status == 200:
                auth_data = await response.json()
                self._access_token = auth_data["access_token"]
                self._instance_url = auth_data["instance_url"]

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync accounts, contacts, opportunities, and activities from Salesforce."""
            logger.error("Failed to authenticate with Salesforce")
            return 0

        session = await self._get_session()
        synced_count = 0

        if not since:
            since = datetime.utcnow() - timedelta(days=30)

        # Sync different Salesforce objects
        synced_count += await self._sync_accounts(session, since)
        synced_count += await self._sync_opportunities(session, since)
        synced_count += await self._sync_contacts(session, since)
        synced_count += await self._sync_activities(session, since)

        return synced_count

    async def _sync_accounts(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce accounts."""
        soql = f"""
        """
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self._instance_url}/services/data/v57.0/query"

        count = 0
        async with session.get(url, headers=headers, params={"q": soql}) as response:
            if response.status == 200:
                data = await response.json()

                for record in data.get("records", []):
                    content = f"""
                    """
                        source="salesforce",
                        source_metadata={
                            "type": "account",
                            "account_id": record.get("Id"),
                            "industry": record.get("Industry"),
                            "account_type": record.get("Type"),
                            "last_modified": record.get("LastModifiedDate"),
                        },
                        context_tags=["crm", "salesforce", "account"],
                    )
                    count += 1

        return count

    async def _sync_opportunities(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce opportunities."""
        soql = f"""
        """
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self._instance_url}/services/data/v57.0/query"

        count = 0
        async with session.get(url, headers=headers, params={"q": soql}) as response:
            if response.status == 200:
                data = await response.json()

                for record in data.get("records", []):
                    content = f"""
                    """
                        source="salesforce",
                        source_metadata={
                            "type": "opportunity",
                            "opportunity_id": record.get("Id"),
                            "stage": record.get("StageName"),
                            "amount": record.get("Amount"),
                            "close_date": record.get("CloseDate"),
                            "probability": record.get("Probability"),
                        },
                        context_tags=["crm", "salesforce", "opportunity", "pipeline"],
                    )
                    count += 1

        return count

    async def _sync_contacts(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce contacts."""
        """Sync Salesforce activities (tasks, events)."""
    """Integration for HubSpot CRM and marketing platform."""
        """Sync contacts, companies, deals, and activities from HubSpot."""
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        # Sync different HubSpot objects
        synced_count += await self._sync_contacts(session, headers, since)
        synced_count += await self._sync_companies(session, headers, since)
        synced_count += await self._sync_deals(session, headers, since)

        return synced_count

    async def _sync_contacts(self, session: aiohttp.ClientSession, headers: Dict[str, str], since: datetime) -> int:
        """Sync HubSpot contacts."""
        url = f"{self.config.base_url}/crm/v3/objects/contacts"

        params = {
            "properties": "firstname,lastname,email,company,jobtitle,phone,notes",
            "limit": 100,
        }

        count = 0
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

                for contact in data.get("results", []):
                    props = contact.get("properties", {})
                    content = f"""
                    """
                        source="hubspot",
                        source_metadata={
                            "type": "contact",
                            "contact_id": contact.get("id"),
                            "email": props.get("email"),
                            "company": props.get("company"),
                            "created_at": contact.get("createdAt"),
                            "updated_at": contact.get("updatedAt"),
                        },
                        context_tags=["crm", "hubspot", "contact"],
                    )
                    count += 1

        return count

    async def _sync_companies(self, session: aiohttp.ClientSession, headers: Dict[str, str], since: datetime) -> int:
        """Sync HubSpot companies."""
        """Sync HubSpot deals."""
    """Integration for Slack workspace communications."""
        """Sync messages, channels, and user data from Slack."""
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        # Sync channels and their messages
        channels = await self._get_channels(session, headers)

        for channel in channels:
            synced_count += await self._sync_channel_messages(session, headers, channel, since)

        return synced_count

    async def _get_channels(self, session: aiohttp.ClientSession, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get list of Slack channels."""
        url = f"{self.config.base_url}/conversations.list"

        params = {"types": "public_channel,private_channel", "limit": 200}

        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("channels", [])

        return []

    async def _sync_channel_messages(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        channel: Dict[str, Any],
        since: datetime,
    ) -> int:
        """Sync messages from a specific channel."""
        url = f"{self.config.base_url}/conversations.history"

        # Convert to Slack timestamp
        oldest = str(int(since.timestamp()))

        params = {"channel": channel["id"], "oldest": oldest, "limit": 200}

        count = 0
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

                for message in data.get("messages", []):
                    if message.get("text"):
                        content = f"""
                        """
                        if message.get("thread_ts"):
                            replies = await self._get_thread_replies(
                                session, headers, channel["id"], message["thread_ts"]
                            )
                            if replies:
                                content += f"\nThread Replies: {len(replies)} messages"

                        await self.memory_system.add_memory(
                            user_id=self.user_id,
                            content=content.strip(),
                            source="slack",
                            source_metadata={
                                "type": "message",
                                "channel_id": channel["id"],
                                "channel_name": channel.get("name"),
                                "user_id": message.get("user"),
                                "timestamp": message.get("ts"),
                                "thread_ts": message.get("thread_ts"),
                            },
                            context_tags=["communication", "slack", "message"],
                        )
                        count += 1

        return count

    async def _get_thread_replies(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        channel_id: str,
        thread_ts: str,
    ) -> List[Dict[str, Any]]:
        """Get replies to a thread."""
        url = f"{self.config.base_url}/conversations.replies"

        params = {"channel": channel_id, "ts": thread_ts}

        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("messages", [])

        return []

class LookerIntegration(BaseDataSourceIntegration):
    """Integration for Looker business intelligence platform."""
        """Authenticate with Looker API."""
        auth_url = f"{self.config.base_url}/api/4.0/login"

        auth_data = {
            "client_id": self.config.api_key,
            "client_secret": self.config.additional_headers.get("client_secret"),
        }

        async with session.post(auth_url, json=auth_data) as response:
            if response.status == 200:
                auth_response = await response.json()
                self._access_token = auth_response["access_token"]

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync dashboards, looks, and data from Looker."""
            logger.error("Failed to authenticate with Looker")
            return 0

        session = await self._get_session()
        synced_count = 0

        # Sync different Looker objects
        synced_count += await self._sync_dashboards(session)
        synced_count += await self._sync_looks(session)
        synced_count += await self._sync_explores(session)

        return synced_count

    async def _sync_dashboards(self, session: aiohttp.ClientSession) -> int:
        """Sync Looker dashboards."""
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self.config.base_url}/api/4.0/dashboards"

        count = 0
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                dashboards = await response.json()

                for dashboard in dashboards:
                    content = f"""
                    """
                        source="looker",
                        source_metadata={
                            "type": "dashboard",
                            "dashboard_id": dashboard.get("id"),
                            "title": dashboard.get("title"),
                            "folder_id": dashboard.get("folder", {}).get("id"),
                            "created_at": dashboard.get("created_at"),
                            "updated_at": dashboard.get("updated_at"),
                        },
                        context_tags=[
                            "analytics",
                            "looker",
                            "dashboard",
                            "business_intelligence",
                        ],
                    )
                    count += 1

        return count

    async def _sync_looks(self, session: aiohttp.ClientSession) -> int:
        """Sync Looker looks (saved queries)."""
        """Sync Looker explores and data models."""
    """cherry_aites data collection from all sources."""
        """Add a data source integration."""
        """Sync data from all configured sources."""
                logger.info(f"Starting sync for {name}")
                count = await integration.sync_data(since)
                results[name] = count
                logger.info(f"Synced {count} items from {name}")
            except Exception:

                pass
                logger.error(f"Failed to sync {name}: {e}")
                results[name] = -1
            finally:
                await integration.close()

        return results

    async def setup_default_integrations(self, configs: Dict[str, DataSourceConfig]) -> None:
        """Set up all default integrations."""
        if "gong" in configs:
            self.add_integration(
                "gong",
                GongIntegration(configs["gong"], self.memory_system, self.user_id),
            )

        if "salesforce" in configs:
            self.add_integration(
                "salesforce",
                SalesforceIntegration(configs["salesforce"], self.memory_system, self.user_id),
            )

        if "hubspot" in configs:
            self.add_integration(
                "hubspot",
                HubSpotIntegration(configs["hubspot"], self.memory_system, self.user_id),
            )

        if "slack" in configs:
            self.add_integration(
                "slack",
                SlackIntegration(configs["slack"], self.memory_system, self.user_id),
            )

        if "looker" in configs:
            self.add_integration(
                "looker",
                LookerIntegration(configs["looker"], self.memory_system, self.user_id),
            )
