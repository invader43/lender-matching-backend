"""Gemini AI service for PDF processing and rule extraction."""

import os
from typing import List, Dict, Any
from google import genai
from google.genai import types


class GeminiService:
    """Service for interacting with Gemini API using async client."""
    
    def __init__(self):
        """Initialize Gemini client."""
        print("Initializing GeminiService...")
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set"
            )
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"  # Using latest model
        print(f"GeminiService initialized with model: {self.model_id}")
    
    async def extract_rules_from_pdf(
        self,
        pdf_path: str,
        current_parameters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract underwriting rules from a PDF using Gemini.
        
        Args:
            pdf_path: Path to the PDF file
            current_parameters: List of existing parameter definitions
            
        Returns:
            Dictionary containing:
                - rules: List of extracted rules
                - new_parameters: List of new parameter definitions needed
        """
        print(f"Starting rule extraction from PDF: {pdf_path}")
        
        # Build the prompt with current schema context
        current_schema_list = [
            f"{p['key_name']} ({p['data_type']}): {p['display_label']}"
            for p in current_parameters
        ]
        
        print(f"Building system prompt with {len(current_schema_list)} existing parameters...")
        prompt = self._build_system_prompt(current_schema_list)
        
        # Read the PDF file as bytes
        print(f"Reading PDF file: {pdf_path}")
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Generate content with inline PDF bytes using ASYNC client
        print("Sending request to Gemini API...")
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf',
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent extraction
                response_mime_type="application/json"
            )
        )
        print("Received response from Gemini API.")
        
        # Parse the JSON response
        print("Parsing Gemini response...")
        result = self._parse_gemini_response(response.text)
        
        print(f"Extraction complete. Found {len(result['rules'])} rules and {len(result['new_parameters'])} new parameters.")
        return result
    
    def _build_system_prompt(self, current_schema_list: List[str]) -> str:
        """Build the system prompt for rule extraction."""
        schema_str = "\n".join(current_schema_list) if current_schema_list else "No parameters defined yet"
        
        return f"""You are a credit underwriter assistant specialized in extracting lending criteria from policy documents.

**Current Parameter Schema:**
{schema_str}

**Your Task:**
1. Identify every eligibility rule and scoring criterion in the document
2. For each rule:
   - If it maps to an existing parameter in the Current Schema, use that parameter's key_name
   - If it requires a NEW parameter not in the Current Schema, define it with:
     * key_name (snake_case, e.g., "truck_age_years" )
     * display_label (human-readable, e.g., "Age of Truck")
     * data_type (one of: string, number, boolean, select, currency)
     * options (only for select type, e.g., {{"values": ["Option1", "Option2"]}})
3. Determine the operator (gt, lt, eq, neq, gte, lte, in, contains)
4. Extract the threshold value
5. Classify as "eligibility" (must pass) or "scoring" (adds points)
6. Write a clear failure_reason message

**Output Format (JSON):**
{{
  "rules": [
    {{
      "parameter": "fico_score",
      "operator": "gte",
      "value": 650,
      "type": "eligibility",
      "weight": 0,
      "reason": "FICO score must be at least 650"
    }},
    {{
      "parameter": "truck_age_years",
      "new_parameter_def": {{
        "key_name": "truck_age_years",
        "display_label": "Age of Truck (Years)",
        "data_type": "number",
        "description": "Age of the equipment in years"
      }},
      "operator": "lte",
      "value": 10,
      "type": "eligibility",
      "weight": 0,
      "reason": "Equipment cannot be older than 10 years"
    }}
  ]
}}

**Important:**
- Only include "new_parameter_def" if the parameter doesn't exist in Current Schema
- Be precise with operators (use gte/lte for "at least"/"at most")
- Extract ALL rules, even minor ones
- For scoring rules, assign appropriate weight (1-10 scale)
- Keep all names lesser than 50 characters
"""
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's JSON response.
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Parsed dictionary with rules and new_parameters
        """
        import json
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            print("Direct JSON parsing failed, attempting to extract from markdown blocks...")
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                print(f"Failed to parse response text: {response_text[:200]}...")
                raise ValueError("Failed to parse Gemini response as JSON")
        
        # Separate rules and new parameters
        rules = []
        new_parameters = []
        
        for rule in data.get("rules", []):
            if "new_parameter_def" in rule:
                new_param = rule.pop("new_parameter_def")
                new_parameters.append(new_param)
            rules.append(rule)
        
        return {
            "rules": rules,
            "new_parameters": new_parameters
        }


# Singleton instance
_gemini_service = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        print("Creating new GeminiService singleton instance...")
        _gemini_service = GeminiService()
    return _gemini_service
