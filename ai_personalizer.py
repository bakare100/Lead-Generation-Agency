import os
import logging
from typing import Dict, Any, List
import json

import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)

class AIPersonalizer:
    """Service for AI-powered personalization using Gemini"""

    def __init__(self):
        self.config = Config()
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            logger.warning("GEMINI_API_KEY not found, AI personalization disabled")
            self.model_flash = None
            self.model_pro = None
            return

        # NEW API — correct configuration
        genai.configure(api_key=api_key)

        # Initialize models
        self.model_flash = genai.GenerativeModel("gemini-1.5-flash")
        self.model_pro = genai.GenerativeModel("gemini-1.5-pro")

    # ---------------------------------------------------------
    # COLD EMAIL
    # ---------------------------------------------------------
    def generate_cold_email(self, lead_data: Dict[str, Any], client_data: Dict[str, Any]) -> str:
        if not self.model_flash:
            return self._fallback_cold_email(lead_data)

        try:
            prompt = f"""
Generate a personalized cold email for a lead generation service.

Lead Information:
- Name: {lead_data['first_name']} {lead_data['last_name']}
- Title: {lead_data['title']}
- Company: {lead_data['company']}

Client Information:
- Service: AI-powered lead generation
- Target: Hiring managers and HR professionals
- Value Proposition: Fast access to top-tier candidates using AI-sourced leads

Instructions:
1. Keep it under 100 words
2. Make it personal and relevant to their role
3. Include a clear call-to-action
4. Sound professional but friendly
5. Not sales-y
Start with: Hi {lead_data['first_name']},
End with: Best,\nAILeadGen
"""

            response = self.model_flash.generate_content(prompt)

            if hasattr(response, "text") and response.text:
                return response.text.strip()

            return self._fallback_cold_email(lead_data)

        except Exception as e:
            logger.error(f"Cold email generation error: {e}")
            return self._fallback_cold_email(lead_data)

    # ---------------------------------------------------------
    # ICEBREAKER
    # ---------------------------------------------------------
    def generate_icebreaker(self, lead_data: Dict[str, Any], client_data: Dict[str, Any]) -> str:
        if not self.model_flash:
            return self._fallback_icebreaker(lead_data)

        try:
            prompt = f"""
Generate a personalized LinkedIn icebreaker.

Lead Information:
- Name: {lead_data['first_name']} {lead_data['last_name']}
- Title: {lead_data['title']}
- Company: {lead_data['company']}

Instructions:
- Under 50 words
- Conversational & friendly
- Reference their company or role
- No sales
- Output ONLY the message
"""

            response = self.model_flash.generate_content(prompt)

            if hasattr(response, "text") and response.text:
                return response.text.strip()

            return self._fallback_icebreaker(lead_data)

        except Exception as e:
            logger.error(f"Icebreaker generation error: {e}")
            return self._fallback_icebreaker(lead_data)

    # ---------------------------------------------------------
    # FOLLOW UP SEQUENCE
    # ---------------------------------------------------------
    def generate_follow_up_sequence(self, lead_data: Dict[str, Any], previous_messages: List[str]) -> List[str]:
        if not self.model_pro:
            return self._fallback_follow_up_sequence(lead_data)

        try:
            prompt = f"""
Generate a SEQUENCE of 3 follow-up emails for a lead generation service.

Lead:
- {lead_data['first_name']} {lead_data['last_name']}
- {lead_data['title']} at {lead_data['company']}

Previous messages:
{chr(10).join(previous_messages)}

Instructions:
- 3 emails
- Each under 80 words
- Timings: 3 days, 1 week, 2 weeks
- Increasing value
- JSON array with fields: "timing", "subject", "body"
"""

            response = self.model_pro.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            if hasattr(response, "text") and response.text:
                parsed = json.loads(response.text)
                return [msg["body"] for msg in parsed]

            return self._fallback_follow_up_sequence(lead_data)

        except Exception as e:
            logger.error(f"Follow-up sequence error: {e}")
            return self._fallback_follow_up_sequence(lead_data)

    # ---------------------------------------------------------
    # FALLBACKS
    # ---------------------------------------------------------
    def _fallback_cold_email(self, lead_data: Dict[str, Any]) -> str:
        return f"""Hi {lead_data['first_name']},

I noticed you're the {lead_data['title']} at {lead_data['company']}. We help teams like yours get access to top-tier candidates using AI-sourced leads.

Would you be open to a quick chat or a free sample?

Best,
AILeadGen"""

    def _fallback_icebreaker(self, lead_data: Dict[str, Any]) -> str:
        return (
            f"Saw you're doing great work at {lead_data['company']} — "
            "thought I'd reach out!"
        )

    def _fallback_follow_up_sequence(self, lead_data: Dict[str, Any]) -> List[str]:
        return [
            f"Hi {lead_data['first_name']}, following up on my previous message about AI-sourced leads.",
            f"Hi {lead_data['first_name']}_]()_
