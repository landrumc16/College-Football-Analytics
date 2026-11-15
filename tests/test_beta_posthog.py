"""Dashboard contract/provisioning tests. No requests to PostHog or invented account access."""
import json
from copy import deepcopy
from scripts.configure_beta_posthog import SPEC,provision

def test_dashboard_covers_beta_and_excludes_test_traffic():
    spec=json.loads(SPEC.read_text())
    assert len(spec['insights'])==12
    for insight in spec['insights'][:-1]:
        assert "properties.traffic_type = 'beta'" in insight['query']['source']['query']
    assert "properties.traffic_type = 'test'" in spec['insights'][-1]['query']['source']['query']
    assert 'person' not in spec['insights'][0]['query']['source']['query']

def test_dashboard_setup_is_idempotent_and_not_public():
    spec=json.loads(SPEC.read_text());dashboards=[];insights=[]
    def api(method,path,body=None):
        if method=='GET' and '/dashboards/?' in path:return {'results':deepcopy(dashboards),'next':None}
        if method=='GET' and '/insights/?' in path:return {'results':deepcopy(insights),'next':None}
        if method=='POST' and path.endswith('/dashboards/'):
            dashboards.append(body|{'id':1,'is_shared':False});return dashboards[-1]
        if method=='GET' and path.endswith('/dashboards/1/'):return deepcopy(dashboards[0])
        if method=='POST' and path.endswith('/insights/'):
            insights.append(body|{'id':len(insights)+1});return insights[-1]
        if method=='PATCH' and '/insights/' in path:
            target=int(path.rstrip('/').split('/')[-1])-1;insights[target].update(body);return insights[target]
        raise AssertionError((method,path))
    assert provision(api,'42',spec)==1
    assert provision(api,'42',spec)==1
    assert len(dashboards)==1 and len(insights)==12
    assert all(i['dashboards']==[1] for i in insights)
    dashboards[0]['is_shared']=True
    import pytest
    with pytest.raises(ValueError,match='Public sharing'):provision(api,'42',spec)
