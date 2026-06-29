import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import gemini_service

def test_resume_parser():
    print("Testing Resume Parser...")
    resume_text = "Experienced Developer with skills in React and Python."
    parsed = gemini_service.parse_resume(resume_text)
    assert "skills" in parsed, "Skills missing in resume parse result"
    print("Resume Parser OK")

def test_jd_parser():
    print("Testing Job Description Parser...")
    jd_text = "Looking for a Senior Developer who knows React, Python, and Kafka."
    parsed = gemini_service.parse_jd(jd_text)
    assert "required_skills" in parsed, "Required skills missing in JD parse result"
    print("JD Parser OK")

def test_match_agent():
    print("Testing Match Agent...")
    res_parsed = gemini_service.get_mock_resume_parsed()
    jd_parsed = gemini_service.get_mock_jd_parsed()
    match = gemini_service.match_resume_and_jd(res_parsed, jd_parsed)
    assert "matchScore" in match, "Match score missing in comparison"
    assert match["matchScore"] > 0, "Invalid match score calculated"
    print("Match Agent OK")

def test_question_generator():
    print("Testing Adaptive Question Generator...")
    q = gemini_service.generate_question({}, {}, [], "Technical", "Medium")
    assert len(q) > 10, "Question generated is too short"
    print("Question Generator OK")

def test_judge_agent():
    print("Testing Judge Agent...")
    eval_res = gemini_service.judge_answer(
        question="How do you handle migrations?",
        answer="I run migrations in standard CI/CD with transaction wrappers.",
        signals={"responseTime": 30, "latencySeconds": 2.0, "wordCount": 10, "wordsPerMinute": 20, "fillerCount": 0}
    )
    assert "accuracy" in eval_res, "Evaluation result missing accuracy score"
    print("Judge Agent OK")

def test_career_roadmap_agent():
    print("Testing Career Intelligence Roadmap Agent...")
    res = gemini_service.generate_career_roadmap(
        resume={"candidate_name": "Test Candidate", "skills": ["React"]},
        target_role="DevOps Engineer",
        target_company="Google"
    )
    assert "current_readiness" in res, "Readiness missing in roadmap result"
    assert "weekly_milestones" in res, "Weekly plan missing in roadmap result"
    assert "resume_checkpoint_upgrades" in res, "Checkpoints missing in roadmap result"
    print("Career Intelligence Agent OK")

if __name__ == "__main__":
    print("--- Running AI Agent Verification Suite ---")
    try:
        test_resume_parser()
        test_jd_parser()
        test_match_agent()
        test_question_generator()
        test_judge_agent()
        test_career_roadmap_agent()
        print("--- All tests completed successfully! ---")
    except AssertionError as e:
        print(f"Test assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error running tests: {e}")
        sys.exit(1)
