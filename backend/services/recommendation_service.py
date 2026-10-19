import logging
from typing import Dict, Union, Any
from backend.ai.vector_store_manager import get_shared_vector_store
from backend.ai.rag import run_rag_pipeline
logger = logging.getLogger(__name__)

# Analyzes the candidate's profile to suggest skills,
# certifications, projects, and career moves.
class RecommendationService:
    def __init__(self):
        logger.info("Initializing the Recommendation Service..")
        self.vector_store = get_shared_vector_store()

    # Generates Strategic Career Recommendations..
    def get_recommendation(self, target_role: str = "") -> Union[str, Dict[str, Any]]:
        logger.info("Generating career recommendations...")
        target_role = target_role.strip()
        if target_role:
            query = (
                f"The candidate wants to transition into or advance "
                f"as a '{target_role}'.\n\n"

                "Analyze the candidate's resume and provide a SHORT, "
                "practical career recommendation for this target role.\n\n"

                "Use exactly this structure:\n\n"

                "Skills to Upgrade\n"
                "1. <Skill name>\n"
                "   Learn: <specific topics or technologies to learn>\n\n"
                "2. <Skill name>\n"
                "   Learn: <specific topics or technologies to learn>\n\n"
                "3. <Skill name>\n"
                "   Learn: <specific topics or technologies to learn>\n\n"

                "Recommended Certification\n"
                "<One relevant certification>\n"
                "Why: <one short reason>\n\n"

                "Recommended Project\n"
                "<One practical portfolio project>\n"
                "Technologies: <relevant technologies>\n\n"

                "Next Step\n"
                "<One short actionable next step>\n\n"

                "IMPORTANT RULES:\n"
                "- Keep the response concise.\n"
                "- Recommend exactly 3 skills to upgrade.\n"
                "- Recommend exactly 1 certification.\n"
                "- Recommend exactly 1 portfolio project.\n"
                "- Use the resume only to understand the candidate's existing "
                "skills and background.\n"
                "- You may use general industry knowledge to recommend skills, "
                "certifications, and projects.\n"
                "- Do not claim the candidate already has a skill unless the "
                "resume supports it.\n"
                "- Do not invent experience, education, certifications, projects, "
                "or achievements.\n"
                "- DO NOT discuss career gaps, employment gaps, unemployment "
                "periods, resume gaps, or missing employment history.\n"
                "- This recommendation must focus on skills, certification, "
                "projects, and career development.\n"
                "- Do not add any additional sections.\n"
            )
        else:
            query = (
                "Based on the candidate's current resume context "
                "and career trajectory:\n"
                "1. Recommend 3 specific technical skills "
                "the candidate should learn next.\n"
                "2. Recommend 1 high-impact portfolio project.\n"
                "3. Recommend general career-development advice.\n\n"

                "Keep the recommendations practical and relevant "
                "to the candidate's existing profile.\n"
                "Do not invent candidate experience, skills, "
                "education, certifications, or achievements."
            )
        try:
            response = run_rag_pipeline(
                user_query=query,
                vector_store=self.vector_store,
                service_type="recommendation",
                expected_format="text",
                top_k=4
            )
            logger.info("Successfully Generated the Recommendations..")
            return response
        except Exception as e:
            logger.exception("Failed to Generate the Recommendations..")
            return {
                "error": "Failed to Generate the Recommendations"
            }