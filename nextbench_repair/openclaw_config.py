"""Explicit provider timeout, bounded by the unchanged whole-attempt limit."""
from nextbench.openclaw_config import configuration as original_configuration


def configuration(token,profile,limits):
    result=original_configuration(token,profile,limits)
    # OpenClaw 2026.9.7 supports this field and caps its stream/first-event
    # watchdog by the finite CLI/agent deadline. Use that unchanged deadline
    # so upstream streaming plus durable settlement cannot hit a shorter SDK
    # timeout. The relay still has its separate 180-second first/idle timeout.
    result['models']['providers']['ihb']['timeoutSeconds']=limits['attempt_timeout_sec']
    return result
