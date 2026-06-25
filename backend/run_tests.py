import sys
import os
import io

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

stdout_buf = io.StringIO()
sys.stdout = stdout_buf
sys.stderr = stdout_buf

try:
    from tests import test_agents
    print("--- Running AI Agent Verification Suite ---")
    test_agents.test_resume_parser()
    test_agents.test_jd_parser()
    test_agents.test_match_agent()
    test_agents.test_question_generator()
    test_agents.test_judge_agent()
    print("--- All tests completed successfully! ---")
except Exception as e:
    print(f"Exception during test execution: {e}")

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

with open("test_run_python.log", "w") as f:
    f.write(stdout_buf.getvalue())

print("Test wrapper completed. Written results to test_run_python.log")
