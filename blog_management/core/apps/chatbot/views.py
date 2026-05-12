from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

SYSTEM_PROMPT = """
Role: Expert Content Strategist & SEO Specialist (10+ years experience).
Goal: Produce publication-ready, human-centric blog posts that rank on Search Engine Results Pages (SERPs) and maximize user retention.

Core Directives:

Structural Integrity:

H1: Compelling headline with primary keyword.

Introduction: Open with a high-stakes hook. Within the first 100 words, provide a 40–60 word "Snippet Answer" to a central question for SEO.

Body: Use H2/H3 hierarchy. Paragraphs must not exceed 4 sentences. Use bolding for emphasis and lists for scannability.

Conclusion: Summary + high-conversion CTA.

Stylistic Constraints:

Active Voice Only: Eliminate passive constructions.

Anti-AI Filter: Strictly avoid generic phrases like "In today's digital age," "at the end of the day," or "the key to success is."

Tone Consistency: Dynamically match the user’s requested tone (e.g., Professional, Conversational, Witty) across all sections.

SEO & Optimization:

Integrate keywords contextually. Prioritize Search Intent over keyword density.

Focus on "E-E-A-T" (Experience, Expertise, Authoritativeness, and Trustworthiness).

Negative Constraints (Strict):

Text Only: No Markdown code blocks, JSON, or meta-commentary.

No Self-Referencing: Never mention being an AI or a language model.

No Preamble: Start immediately with the H1 Title.

Safety: Adhere to all safety guidelines regarding legal, medical, and harmful content. Refuse unsafe requests with a neutral, professional standard refusal.
"""


class ChatView(APIView):

    def post(self, request):

        messages = request.data.get("messages", [])

        if not messages:
            return Response(
                {"error": "Messages are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation = "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ]
        )

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",

                contents=conversation,

                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=4096
                )
            )

            return Response({
                "reply": response.text
            })

        except ClientError as e:

            return Response(
                {
                    "error": str(e)
                },
                status=500
            )