import os
import logging
from typing import Dict, Any, List
import json

import google.generativeai as genai
from google.generativeai import types
from config import Config

logger = logging.getLogger(__name__)

class AIPersonalizer:
    """Service for AI-powered personalization using Gemini"""
    
    def __init__(self):
        self.config = Config()
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found, AI personalization will be disabled")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
    
    def generate_cold_email(self, lead_data: Dict[str, Any], client_data: Dict[str, Any]) -> str:
        """Generate personalized cold email using Gemini AI"""
        if not self.client:
            return self._fallback_cold_email(lead_data)
        
        try:
            prompt = f"""Generate a personalized cold email for a lead generation service.

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
5. Focus on solving their hiring challenges
6. Don't be overly sales-y

Email should start with "Hi {lead_data['first_name']}," and end with "Best,\\nAILeadGen"
"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini, using fallback")
                return self._fallback_cold_email(lead_data)
                
        except Exception as e:
            logger.error(f"Error generating cold email with AI: {e}")
            return self._fallback_cold_email(lead_data)
    
    def generate_icebreaker(self, lead_data: Dict[str, Any], client_data: Dict[str, Any]) -> str:
        """Generate personalized icebreaker using Gemini AI"""
        if not self.client:
            return self._fallback_icebreaker(lead_data)
        
        try:
            prompt = f"""Generate a personalized LinkedIn icebreaker message for a lead generation service.

Lead Information:
- Name: {lead_data['first_name']} {lead_data['last_name']}
- Title: {lead_data['title']}
- Company: {lead_data['company']}

Instructions:
1. Keep it under 50 words
2. Make it conversational and friendly
3. Reference their company or role specifically
4. Sound like a genuine connection request
5. Avoid being sales-y
6. Make it feel personal, not templated

Generate only the icebreaker message, no additional text.
"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini, using fallback")
                return self._fallback_icebreaker(lead_data)
                
        except Exception as e:
            logger.error(f"Error generating icebreaker with AI: {e}")
            return self._fallback_icebreaker(lead_data)
    
    def generate_follow_up_sequence(self, lead_data: Dict[str, Any], previous_messages: List[str]) -> List[str]:
        """Generate a sequence of follow-up messages"""
        if not self.client:
            return self._fallback_follow_up_sequence(lead_data)
        
        try:
            prompt = f"""Generate a sequence of 3 follow-up emails for a lead generation service.

Lead Information:
- Name: {lead_data['first_name']} {lead_data['last_name']}
- Title: {lead_data['title']}
- Company: {lead_data['company']}

Previous messages sent:
{chr(10).join(previous_messages)}

Instructions:
1. Create 3 different follow-up emails
2. Each should be under 80 words
3. Space them for: 3 days later, 1 week later, 2 weeks later
4. Gradually increase value proposition
5. Use different angles/approaches
6. Maintain professional but friendly tone
7. Include clear call-to-actions

Format as JSON array with fields: "timing", "subject", "body"
"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                follow_ups = json.loads(response.text)
                return [f_up['body'] for f_up in follow_ups]
            else:
                logger.warning("Empty response from Gemini, using fallback")
                return self._fallback_follow_up_sequence(lead_data)
                
        except Exception as e:
            logger.error(f"Error generating follow-up sequence with AI: {e}")
            return self._fallback_follow_up_sequence(lead_data)
    
    def _fallback_cold_email(self, lead_data: Dict[str, Any]) -> str:
        """Fallback cold email template when AI is unavailable"""
        return f"""Hi {lead_data['first_name']},

I noticed you're the {lead_data['title']} at {lead_data['company']}. We help teams like yours get access to top-tier candidates fast using AI-sourced leads.

Our clients typically see 3x faster hiring times and higher quality candidates. Would you be interested in a quick demo or a free sample list to start?

Best,
AILeadGen"""
    
    def _fallback_icebreaker(self, lead_data: Dict[str, Any]) -> str:
        """Fallback icebreaker template when AI is unavailable"""
        return f"Saw you're doing great work at {lead_data['company']} — especially in hiring tech talent. Thought I'd reach out!"
    
    def _fallback_follow_up_sequence(self, lead_data: Dict[str, Any]) -> List[str]:
        """Fallback follow-up sequence when AI is unavailable"""
        return [
            f"Hi {lead_data['first_name']}, following up on my previous message about AI-sourced leads. Many {lead_data['title']}s find our service helps them fill positions 3x faster. Worth a quick chat?",
            f"Hi {lead_data['first_name']}, hope you're well! Still interested in learning how we can help {lead_data['company']} access better candidates? Happy to share some success stories from similar companies.",
            f"Hi {lead_data['first_name']}, last follow-up from me! If hiring top talent is still a priority for {lead_data['company']}, I'd love to send over a free sample of our AI-sourced leads. No strings attached."
        ]
