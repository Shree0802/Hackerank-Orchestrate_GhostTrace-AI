import pandas as pd
import json

df_out = pd.read_csv('dataset/sample_output.csv')

PHASE_ORDER = {'FINDING': 1, 'REMEDIATION': 2, 'VERIFICATION': 3}
OP_ORDER = {
    'REPORT_REMAINING_RECORD': 1,
    'REPORT_EXPOSED_PII': 2,
    'REPORT_ACTIVE_DATA_FLOW': 3,
    'REPORT_RESTORE_RISK': 4,
    'DISABLE_DATA_FLOW': 1,
    'BLOCK_RESTORE': 2,
    'DELETE_RECORD': 3,
    'REDACT_RECORD': 4,
    'ANONYMIZE_RECORD': 5,
    'VERIFY_RECORD_ABSENT': 1,
    'VERIFY_RECORD_PRESENT': 2,
    'VERIFY_RECORD_REDACTED': 3,
    'VERIFY_RECORD_ANONYMIZED': 4,
    'VERIFY_DATA_FLOW_DISABLED': 5,
    'VERIFY_RESTORE_BLOCKED': 6,
}

def step_sort_key(step):
    p = PHASE_ORDER.get(step['phase'], 99)
    op = OP_ORDER.get(step['operation'], 99)
    sys = step['system_id']
    res = step['resource_id']
    return (p, op, sys, res)

all_matched = True
for _, r in df_out.iterrows():
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    sorted_steps = sorted(steps, key=step_sort_key)
    
    # check order
    orig_keys = [(s['phase'], s['operation'], s['system_id'], s['resource_id']) for s in steps]
    sorted_keys = [(s['phase'], s['operation'], s['system_id'], s['resource_id']) for s in sorted_steps]
    if orig_keys != sorted_keys:
        print(f"Mismatch in {cid}:")
        print("  Original:", orig_keys)
        print("  Sorted:  ", sorted_keys)
        all_matched = False

if all_matched:
    print("SUCCESS: 100% of sample cases strictly match the sorting key (phase, op_order, system_id, resource_id)!")
