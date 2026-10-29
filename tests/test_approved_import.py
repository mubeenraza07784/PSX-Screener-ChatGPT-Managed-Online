import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from cloud.import_approved import REQUIRED_TECH, validate


class ImportValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.day = dt.date(2026, 10, 29)
        self.known = {f"A{i:03d}" for i in range(420)}
        self.headers = ['sym'] + sorted(REQUIRED_TECH - {'sym'})
        self.tech = self.root / 'tech_new.txt'
        self.manifest = self.root / 'source.json'
        self.manifest.write_text(json.dumps({'provider':'Example authorized vendor',
            'permission_basis':'licensed export', 'permission_confirmed': True,
            'as_of': self.day.isoformat()}))
        self.write_rows(self.day)

    def write_rows(self, day, count=420, price='100.5'):
        rows = ['|'.join(self.headers)]
        for sym in sorted(self.known)[:count]:
            rec = dict.fromkeys(self.headers, '')
            rec.update(sym=sym, P=price, lastDate=day.isoformat(), rsi='49', s20='98')
            rows.append('|'.join(rec[f] for f in self.headers))
        self.tech.write_text('\n'.join(rows)+'\n')

    def test_accepts_complete_authorized_snapshot(self):
        self.assertEqual(validate(self.tech, self.manifest, self.known, self.day), (420, '2026-10-29'))

    def test_rejects_stale_data(self):
        self.write_rows(self.day-dt.timedelta(days=1))
        with self.assertRaisesRegex(ValueError, 'row date'):
            validate(self.tech, self.manifest, self.known, self.day)

    def test_rejects_partial_data(self):
        self.write_rows(self.day, count=300)
        with self.assertRaisesRegex(ValueError, 'at least 400'):
            validate(self.tech, self.manifest, self.known, self.day)

    def test_rejects_invalid_price(self):
        self.write_rows(self.day, price='not-a-price')
        with self.assertRaisesRegex(ValueError, 'nonnumeric close'):
            validate(self.tech, self.manifest, self.known, self.day)

    def test_requires_permission_confirmation(self):
        item=json.loads(self.manifest.read_text())
        item['permission_confirmed']=False
        self.manifest.write_text(json.dumps(item))
        with self.assertRaisesRegex(ValueError, 'permission basis'):
            validate(self.tech, self.manifest, self.known, self.day)


if __name__ == '__main__':
    unittest.main()
