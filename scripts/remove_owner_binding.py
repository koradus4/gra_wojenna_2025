import json
import subprocess
import sys
p = sys.argv[1]
member = sys.argv[2]
policy = json.loads(subprocess.check_output(['gcloud','projects','get-iam-policy',p,'--format=json']))
modified = False
for b in policy.get('bindings',[]):
    if b.get('role')=='roles/owner' and member in b.get('members',[]):
        b['members'].remove(member)
        modified = True
# remove empty bindings
policy['bindings'] = [b for b in policy.get('bindings',[]) if b.get('members')]
open('policy_tmp.json','w').write(json.dumps(policy))
if modified:
    subprocess.check_call(['gcloud','projects','set-iam-policy',p,'policy_tmp.json'])
    print('Removed',member,'from',p)
else:
    print('No change for',p)
