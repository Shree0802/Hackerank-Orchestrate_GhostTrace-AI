with open('dataset/evidence/logs/resource_lookup_trace_20260926_103856.log', 'r') as f:
    for line in f:
        if 'mori.ren' in line or 'user_50' in line:
            print(line.strip())
