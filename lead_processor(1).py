import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

from ai_personalizer import AIPersonalizer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LeadProcessor:
    def __init__(self, api_key: str):
        self.personalizer = AIPersonalizer(api_key)

    async def process_lead(
        self,
        lead: Dict[str, Any],
        company_info: Dict[str, Any],
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Processes a single lead by combining lead data, company info,
        and optional context, then generating personalized outreach.
        """

        try:
            prompt_data = {
                "lead": lead,
                "company_info": company_info,
                "additional_context": additional_context or {},
            }

            logger.info(f"Processing lead: {lead}")

            personalization_result = await self.personalizer.generate_outreach(prompt_data)

            return {
                "lead": lead,
                "company": company_info,
                "personalized_outreach": personalization_result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing lead: {e}")
            return {
                "lead": lead,
                "company": company_info,
                "personalized_outreach": None,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def process_leads_batch(
        self,
        leads: List[Dict[str, Any]],
        company_info: Dict[str, Any],
        additional_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Handles multiple leads at once.
        Each lead is processed asynchronously.
        """

        processed = []
        for lead in leads:
            result = await self.process_lead(
                lead,
                company_info,
                additional_context,
            )
            processed.append(result)

        return processed
