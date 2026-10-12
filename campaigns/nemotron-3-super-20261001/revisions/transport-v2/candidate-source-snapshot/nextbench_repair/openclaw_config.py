"""Explicit provider timeout, bounded by the unchanged whole-attempt limit."""
from nextbench.openclaw_config import configuration as original_configuration


def configuration(token,profile,limits):
    result=original_configuration(token,profile,limits)
    # OpenClaw 2026.9.7 supports this field and caps its stream/first-event
    # watchdog by the finite CLI/agent deadline. Leave enough time for the
    # relay's 180-second transport deadline to settle and report an error.
    result['models']['providers']['ihb']['timeoutSeconds']=min(210,limits['attempt_timeout_sec'])
    return result
