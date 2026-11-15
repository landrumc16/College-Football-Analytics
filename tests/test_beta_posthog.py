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


def test_public_token_wiring_uses_masked_repository_secret_and_us_region():
    from pathlib import Path
    workflow=Path('.github/workflows/dashboard.yml').read_text()
    assert 'VITE_POSTHOG_PUBLIC_KEY: ${{ secrets.POSTHOG_PUBLIC_KEY }}' in workflow
    assert "secrets.POSTHOG_PUBLIC_KEY != '' && 'https://us.i.posthog.com' || ''" in workflow
    assert 'vars.POSTHOG_PUBLIC_KEY' not in workflow
    assert 'POSTHOG_PERSONAL_API_KEY' not in workflow


def test_live_verification_uses_deployment_secret_without_admin_keys():
    from pathlib import Path
    workflow=Path('.github/workflows/beta-analytics.yml').read_text()
    live=workflow.split('  deployment-secret-and-live-capture:')[1]
    assert "if: github.event_name == 'push'" in live
    assert 'VITE_POSTHOG_PUBLIC_KEY: ${{ secrets.POSTHOG_PUBLIC_KEY }}' in live
    assert "secrets.POSTHOG_PUBLIC_KEY != '' && 'https://us.i.posthog.com' || ''" in live
    assert 'VITE_POSTHOG_TRAFFIC: test' in live
    assert 'POSTHOG_PERSONAL_API_KEY' not in live
    assert 'path: web/posthog-live-evidence/' in live and 'path: web/dist' not in live


def test_direct_setup_reuses_every_existing_dashboard_query():
    from pathlib import Path
    guide=Path('docs/POSTHOG-DIRECT-SETUP.md').read_text()
    spec=json.loads(SPEC.read_text())
    for insight in spec['insights']:
        assert insight['name'] in guide
        assert insight['query']['source']['query'] in guide
    assert '737110' in guide and 'public sharing **off**' in guide
