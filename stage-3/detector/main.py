from monitor import tail_log

for entry in tail_log("/var/log/nginx/hng-access.log"):
    print(entry)
    print(entry['source_ip'], entry['status'])