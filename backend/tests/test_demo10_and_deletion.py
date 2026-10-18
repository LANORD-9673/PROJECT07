from collections import Counter
from pathlib import Path
import pytest
from services.importer import parse_table
from services.rule_engine.engine import evaluate, BaselineApproval

DEMO=Path(__file__).resolve().parents[2]/'demo'

@pytest.mark.parametrize('extension',['.csv','.xlsx'])
def test_ten_customer_scenarios(extension):
    loans,issues=parse_table((DEMO/('loans_10'+extension)).read_bytes(),'loans',extension)
    auth,auth_issues=parse_table((DEMO/('authorities_10'+extension)).read_bytes(),'authority',extension)
    assert len(loans)==10 and len({x['payload']['customer_id'] for x in loans})==10
    assert not issues and not auth_issues
    actual=evaluate(loans,auth,BaselineApproval('test-hash','TEST-FIXTURE-ONLY'))
    # Expectations specified by the scenario author, not generated from runtime.
    expected={('R006','T01'):'EXCEPTION',('R007','T02'):'EXCEPTION',('R008','T03'):'EXCEPTION',('R009','T03'):'NOT_APPLICABLE',('R010','T02'):'INSUFFICIENT_INFORMATION',('R010','T03'):'INSUFFICIENT_INFORMATION'}
    for row in actual: assert row['test_result']==expected.get((row['row_id'],row['test_id']),'PASS')
    assert Counter(x['test_result'] for x in actual)=={'PASS':24,'EXCEPTION':3,'NOT_APPLICABLE':1,'INSUFFICIENT_INFORMATION':2}


def import_sources(client):
    ids={}
    for kind,name,fields,key in [
        ('policies','POL-LOAN-01_compact.txt',{'policy_id':'POL-LOAN-01','policy_set_id':'BASELINE','effective_from':'2026-10-08T00:00:00+07:00'},'policy_snapshot_id'),
        ('loans','loans_10.csv',{'dataset_id':'TEST-10'},'dataset_snapshot_id'),
        ('authorities','authorities_10.csv',{'authority_id':'TEST-AUTH'},'authority_snapshot_id')]:
        res=client.post('/api/import/'+kind,files={'file':(name,(DEMO/name).read_bytes())},data=fields)
        assert res.status_code==201,res.text
        ids[key]=res.json()['data']['snapshot_id']
    return ids


def test_delete_unused_sources_and_reimport_versions(client):
    from models.db import connect
    ids=import_sources(client)
    for sid in ids.values():
        res=client.delete('/api/snapshots/'+sid)
        assert res.status_code==200 and res.json()['data']['deleted']
        assert client.get('/api/snapshots/'+sid).status_code==404
        with connect() as db:
            for table in ['snapshots','policy_texts','loan_rows','authority_rows','import_issues']:
                assert db.execute(f'SELECT COUNT(*) FROM {table} WHERE snapshot_id=?',(sid,)).fetchone()[0]==0
    assert client.delete('/api/snapshots/'+ids['dataset_snapshot_id']).status_code==404
    new=import_sources(client)
    assert all(client.get('/api/snapshots/'+sid).json()['data']['version']==2 for sid in new.values())


def test_used_snapshots_are_protected(client):
    ids=import_sources(client)
    run=client.post('/api/audit-runs',json={'audit_name':'Evidence retention',**ids})
    assert run.status_code==201,run.text
    listed=client.get('/api/snapshots').json()['data']
    assert all(x['used_by_runs']==1 for x in listed)
    for sid in ids.values():
        assert client.delete('/api/snapshots/'+sid).status_code==409
        assert client.get('/api/snapshots/'+sid).status_code==200
