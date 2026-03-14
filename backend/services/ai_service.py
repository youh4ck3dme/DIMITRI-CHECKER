import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Load environment variables from .env file
load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if OpenAI and self.api_key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    def generate_risk_narrative(self, company_data: Dict, risk_score: float) -> str:
        """
        Generuje ľudsky čitateľný komentár k riziku firmy.
        """
        if not self.client:
            return "AI Auditor je momentálne nedostupný (chýba API kľúč)."

        try:
            prompt = f"""
            Si expert na corporate intelligence v regióne V4. 
            Analyzuj nasledujúce dáta o firme a navrhni zhrnutie rizika pre investora v slovenčine.
            Firma: {company_data.get('name', 'Neznáma')}
            Krajina: {company_data.get('country', 'N/A')}
            Risk Score: {risk_score}/10
            Detaily: {company_data.get('details', '')}
            
            Zameraj sa na to, či skóre zodpovedá štruktúre a či existujú varovné signály.
            Zhrnutie musí byť stručné, korporátne a profesionálne.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Chyba AI analýzy: {str(e)}"

    def assistant_chat(self, user_query: str, context_data: Optional[Dict] = None) -> str:
        """
        Korporátny asistent pre navigáciu v dátach.
        """
        if not self.client:
            return "Asistent je v režime offline."
            
        # Implementácia asistenta...
        return "Pripravený analyzovať vašu požiadavku."

# Singleton instance
ai_service = AIService()
