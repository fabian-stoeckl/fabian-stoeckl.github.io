import importlib.util
from pathlib import Path
import unittest
import json
import tempfile
import io
from contextlib import redirect_stdout
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
    x=u.refresh_item({'ticker':'TEST'},old,'2026-10-07')
    self.assertEqual(x['series'],old['series']);self.assertEqual(x['status'],'ok');self.assertTrue(x['stale']);self.assertIn('update_error',x)
 def test_new_data_with_delay_is_marked_stale(self):
  with patch.object(u,'fetch',return_value={'2026':[{'date':'2026-10-02'}]}):
   x=u.refresh_item({'ticker':'TEST'},None,'2026-10-05')
   self.assertFalse(x['stale']);self.assertEqual(x['lag_sessions'],1);self.assertEqual(x['last_price_date'],'2026-10-02')
 def test_empty_data_and_first_failure(self):
  for kwargs in [dict(return_value={'2026':[]}),dict(side_effect=RuntimeError('unavailable'))]:
   with patch.object(u,'fetch',**kwargs):
    x=u.refresh_item({'ticker':'TEST'},None,'2026-10-05')
    self.assertEqual(x['status'],'error');self.assertTrue(x['stale']);self.assertEqual(x['last_price_date'],'');self.assertIn('update_error',x)
 def test_success_clears_prior_failure(self):
  old={'series':{'2026':[{'date':'2026-10-02','price':100}]},'update_error':'old error','stale':True}
  with patch.object(u,'fetch',return_value={'2026':[{'date':'2026-10-05','price':101}]}):
   x=u.refresh_item({'ticker':'TEST'},old,'2026-10-05')
   self.assertEqual(x['status'],'ok');self.assertFalse(x['stale']);self.assertNotIn('update_error',x)
 def test_good_friday_easter_and_dst(self):
  for now,expected in [('2026-04-03T21:00Z','2026-04-02'),('2026-04-06T21:00Z','2026-04-02'),('2026-10-06T09:00Z','2026-10-05'),('2026-10-26T15:00Z','2026-10-23'),('2026-10-26T18:00Z','2026-10-26')]:
   self.assertEqual(u.expected_etf_date(pd.Timestamp(now)),expected)
 def test_two_session_buffer_and_third_session_warning(self):
  for expected,lag,stale in [('2026-10-02',0,False),('2026-10-05',1,False),('2026-10-06',2,False),('2026-10-07',3,True)]:
   with patch.object(u,'fetch',return_value={'2026':[{'date':'2026-10-02','price':100}]}):
    x=u.refresh_item({'ticker':'TEST'},None,expected)
    self.assertEqual(x['lag_sessions'],lag);self.assertEqual(x['stale'],stale)
  self.assertEqual(u.lag_sessions('2026-04-02','2026-04-07'),1)
 def test_recent_failure_is_preserved_without_stale_warning(self):
  old={'series':{'2026':[{'date':'2026-10-02','price':100}]}}
  with patch.object(u,'fetch',side_effect=RuntimeError('unavailable')):
   x=u.refresh_item({'ticker':'TEST'},old,'2026-10-06')
   self.assertEqual(x['series'],old['series']);self.assertFalse(x['stale']);self.assertIn('update_error',x)
 def test_workflow_tolerance_preserves_data_and_success_timestamp(self):
  # Exercise main's exit status and saved payload, not just per-item staleness.
  for mode in ['older_response', 'fetch_failure']:
   for expected,code in [('2026-10-02',0),('2026-10-05',0),('2026-10-06',0),('2026-10-07',1)]:
    with self.subTest(mode=mode,expected=expected), tempfile.TemporaryDirectory() as tmp:
     config=Path(tmp)/'etfs.json';out=Path(tmp)/'data.json'
     series={'2026':[{'date':'2026-10-02','price':100,'performance':0}]}
     config.write_text(json.dumps([{'ticker':'TEST'}]))
     out.write_text(json.dumps({'last_successful_update_at':'previous-success','etfs':[{'ticker':'TEST','series':series}]}))
     fetch_args=dict(return_value={'2026':[{'date':'2026-10-01','price':90}]}) if mode=='older_response' else dict(side_effect=RuntimeError('unavailable'))
     log=io.StringIO()
     with patch.object(u,'CONFIG',config),patch.object(u,'OUT',out),patch.object(u,'FX_PAIRS',[]),patch.object(u,'expected_etf_date',return_value=expected),patch.object(u,'xetra_session_closes',return_value=[]),patch.object(u,'fetch',**fetch_args),redirect_stdout(log):
      self.assertEqual(u.main(),code)
     saved=json.loads(out.read_text())
     self.assertEqual(saved['etfs'][0]['series'],series)
     self.assertIn('update_error',saved['etfs'][0])
     self.assertEqual(saved['last_successful_update_at'],'previous-success')
     self.assertEqual(saved['update_status'],'warning' if code else 'ok')
     self.assertIn('::warning::' if code else '::notice::',log.getvalue())
if __name__=='__main__':unittest.main()
