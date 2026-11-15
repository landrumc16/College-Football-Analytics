"""Provision the reviewed dashboard after account access exists. No frontend secrets.

Default prints a plan; --apply needs an owner-run private environment or use the
PostHog connection instead. Never pass a key in argv or commit it to the repo.
"""
import argparse,json,os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,build_opener,HTTPRedirectHandler

SPEC=Path(__file__).resolve().parents[1]/'ops/posthog/dashboard.json'
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def provision(api,project,spec):
    root=f'/api/projects/{project}/'
    tag=spec['tag']
    def listing(path):
        items=[]
        while path:
            result=api('GET',path);items.extend(result['results']);path=result.get('next')
        return items
    dashboards=[d for d in listing(root+'dashboards/?limit=100') if tag in d.get('tags',[]) and not d.get('deleted')]
    if len(dashboards)>1:raise ValueError('Duplicate managed dashboards; review in PostHog before continuing')
    dashboard=dashboards[0] if dashboards else api('POST',root+'dashboards/',{k:spec[k] for k in ('name','description')}|{'tags':[tag]})
    dashboard=api('GET',root+f"dashboards/{dashboard['id']}/")
    if dashboard.get('is_shared') is not False:raise ValueError('Public sharing is enabled or unverified; disable it in PostHog before continuing')
    existing=[i for i in listing(root+'insights/?limit=100') if tag in i.get('tags',[]) and not i.get('deleted')]
    for index,item in enumerate(spec['insights']):
        matches=[i for i in existing if i.get('name')==item['name']]
        if len(matches)>1:raise ValueError('Duplicate managed insight; review in PostHog')
        payload=item|{'dashboards':[dashboard['id']],'tags':[tag],'order':index}
        if matches:api('PATCH',root+f"insights/{matches[0]['id']}/",payload)
        else:api('POST',root+'insights/',payload)
    return dashboard['id']

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    spec=json.loads(SPEC.read_text())
    if not args.apply:
        print(json.dumps({'mode':'plan-only; no requests or credentials required','dashboard':spec},indent=2));return
    host=os.environ.get('POSTHOG_APP_HOST','');project=os.environ.get('POSTHOG_PROJECT_ID','');token=os.environ.get('POSTHOG_PERSONAL_API_KEY','')
    if host not in ('https://us.posthog.com','https://eu.posthog.com') or not project.isdigit() or not token:raise SystemExit('Set private POSTHOG_APP_HOST, POSTHOG_PROJECT_ID and POSTHOG_PERSONAL_API_KEY. Never use VITE_ for a private key.')
    opener=build_opener(NoRedirect)
    def api(method,path,payload=None):
        target=path if path.startswith('https://') else host+path
        if urlparse(target).netloc!=urlparse(host).netloc or not urlparse(target).path.startswith(f'/api/projects/{project}/'):raise ValueError('Refusing to send credentials outside this PostHog project')
        data=json.dumps(payload).encode() if payload is not None else None
        request=Request(target,data=data,method=method,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with opener.open(request,timeout=30) as response:return json.loads(response.read())
    try:dashboard=provision(api,project,spec)
    except Exception as error:raise SystemExit(f'PostHog setup did not complete ({type(error).__name__}). Review project access/settings; no key or server response is printed.') from None
    print(f'Provisioned dashboard: {host}/project/{project}/dashboard/{dashboard}. Verify membership, IP settings and controlled ingestion before declaring live readiness.')
if __name__=='__main__':main()
