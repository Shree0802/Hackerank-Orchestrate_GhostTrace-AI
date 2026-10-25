import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import re

df_req = pd.read_csv('dataset/deletion_requests.csv')

# Let's inspect texts that do NOT contain standard deletion verbs
# In English, French, Spanish, German, Portuguese, Italian, Dutch, Korean, Japanese, Chinese, etc.
del_verbs = [
    'delet', 'eras', 'close', 'remov', 'supprim', 'eliminar', 'lösch', 'borr', 
    'cancela', 'chiud', 'verwijder', 'destroy', 'purge', 'effac', 'terminat',
    'exclus', 'excluir', 'supprimer', 'eliminare', 'löschen', 'entfern',
    '삭제', '탈퇴', '해지', # Korean
    '削除', '退会', '解約', # Japanese
    '删除', '注销', # Chinese
    'usunięc', 'usun', # Polish
    'sterg', 'șterg', # Romanian
]

non_del_cases = []
for idx, r in df_req.iterrows():
    text = r['request_text'].lower()
    has_del = any(v in text for v in del_verbs)
    if not has_del:
        non_del_cases.append((r['case_id'], r['reported_status'], r['request_text']))

print(f"Cases without standard deletion verbs: {len(non_del_cases)}")
for cid, rep, txt in non_del_cases:
    print(f"{cid} ({rep}): {txt}")

print("\nExplicit non-deletion requests:")
for idx, r in df_req.iterrows():
    text = r['request_text'].lower()
    if any(k in text for k in ['keep', 'export', 'download', 'access', 'rectif', 'correct', 'opt-out', 'opt out', 'newsletter', 'marketing']):
        # check if it is asking NOT to delete, or only to export/access/opt-out
        if 'keep the account' in text or 'do not delete' in text or 'don\'t delete' in text or 'without deleting' in text or 'instead of deleting' in text:
            print(f"KEEP/DO NOT DELETE: {r['case_id']}: {r['request_text']}")
        elif ('download' in text or 'export' in text or 'access' in text) and not any(v in text for v in del_verbs):
            print(f"ACCESS/EXPORT ONLY: {r['case_id']}: {r['request_text']}")
