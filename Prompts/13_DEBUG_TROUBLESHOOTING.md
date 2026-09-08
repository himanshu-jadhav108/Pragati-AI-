# PROMPT 13 — DEBUGGING / REPAIR

The PRAGATI AI MVP currently has a failure. Do not rewrite the whole project.

First:
1. inspect the repo
2. reproduce the failure
3. identify root cause
4. apply the smallest robust fix
5. add/adjust a regression test
6. rerun affected tests
7. report exact files changed

Rules:
- preserve working behavior
- do not replace real APIs with fake UI data merely to hide an error
- do not disable validation
- do not silently swallow exceptions
- do not remove audit/governance logic
- do not hardcode the expected answer unless the test fixture is explicitly labeled as a fixture
- if an external provider is unavailable, activate the documented fallback rather than breaking the application

At the end provide:
ROOT CAUSE
FIX
TESTS RUN
RESULT
ANY REMAINING LIMITATION
