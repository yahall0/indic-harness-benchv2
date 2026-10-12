"""Kernel-managed exclusive controller lock, released automatically after a crash."""
import os
from pathlib import Path

class ControllerLease:
    def __init__(self,path): self.path=Path(path); self.file=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.path.open('a+b')
        if not self.path.stat().st_size: self.file.write(b'0'); self.file.flush()
        self.file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.file.close(); self.file=None
            raise RuntimeError('Another benchmark controller is active; refusing duplicate spending')
        return self
    def __exit__(self,*args):
        if self.file:
            self.file.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_UN)
            self.file.close(); self.file=None
