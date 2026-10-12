"""Reuse hardened, frozen Docker operations with explicit campaign image pins."""
from bench.containers import Containers


class CampaignContainers(Containers):
    def __init__(self, journal, run_id, images):
        if set(images) != {'agent', 'relay', 'helper', 'grader'}:
            raise ValueError('Four explicit image pins are required')
        self.images = images
        self.resources = []
        self.journal, self.run_id = journal, run_id
        self.identities = {}
