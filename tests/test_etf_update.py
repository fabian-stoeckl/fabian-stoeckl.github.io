import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import pandas as pd
spec=importlib.util.spec_from_file_location('update',Path(__file__).resolve().parents[1]/'scripts/update_etf_data.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
class UpdateTests(unittest.TestCase):
 def test_completed_sessions(self):
  for now,expected in [('2026-10-05T06:00Z','2026-10-02'),('2026-10-05T21:00Z','2026-10-05'),('2026-10-04T12:00Z','2026-10-02'),('2026-12-25T21:00Z','2026-12-23')]:
   self.assertEqual(u.expected_etf_date(pd.Timestamp(now)),expected)
 def test_preserves_data_on_failure_or_regression(self):
  old={'series':{'2026':[{'date':'2026-10-02','price':100,'performance':0}]}}
  for args in [dict(side_effect=RuntimeError('unavailable')),dict(return_value={'2026':[{'date':'2026-10-01'}]})]:
   with patch.object(u,'fetch',**args):
    x=u.refresh_item({'ticker':'TEST'},old,'2026-10-05')
    self.assertEqual(x['series'],old['series']);self.assertEqual(x['status'],'ok');self.assertTrue(x['stale']);self.assertIn('update_error',x)
 def test_new_data_with_delay_is_marked_stale(self):
  with patch.object(u,'fetch',return_value={'2026':[{'date':'2026-10-02'}]}):
   x=u.refresh_item({'ticker':'TEST'},None,'2026-10-05')
   self.assertTrue(x['stale']);self.assertEqual(x['last_price_date'],'2026-10-02')
if __name__=='__main__':unittest.main()
