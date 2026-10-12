import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from bench.security import SecurityError, safe_export, validated_archive, validate_container, restricted_args, resource_name

def archive(name, kind=tarfile.REGTYPE):
    b=io.BytesIO()
    with tarfile.open(fileobj=b, mode='w') as t:
        m=tarfile.TarInfo(name); m.type=kind
        if kind==tarfile.REGTYPE: m.size=2; t.addfile(m, io.BytesIO(b'ok'))
        else: m.linkname='/etc/passwd'; t.addfile(m)
    return b.getvalue()

class ExportTests(unittest.TestCase):
    def test_bad_paths(self):
        for name in ('../oops', '/etc/passwd', 'C:/oops', 'out\\..\\oops', 'out/CON.txt', 'out/file:secret', 'out/trailing.'):
            with self.subTest(name=name), self.assertRaises(SecurityError): validated_archive(archive(name))
    def test_links_devices_and_pipes(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE):
            with self.subTest(kind=kind), self.assertRaises(SecurityError): validated_archive(archive('out/result',kind))
    def test_regular_export(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'fresh'; safe_export(archive('out/answer.txt'),dest)
            self.assertEqual((dest/'out/answer.txt').read_bytes(),b'ok')
            with self.assertRaises(SecurityError): safe_export(archive('out/answer.txt'),dest)
    def test_no_writes_on_rejected_archive(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'fresh'
            with self.assertRaises(SecurityError): safe_export(archive('../oops'),dest)
            self.assertFalse(dest.exists())
    def test_names_and_flags(self):
        for s in ('ordinary-container', 'ihb-; rm', 'ihb-../x'):
            with self.assertRaises(SecurityError): resource_name(s)
        args=restricted_args('ihb-test')
        self.assertIn('--read-only',args); self.assertNotIn('--privileged',args)

if __name__=='__main__': unittest.main()
