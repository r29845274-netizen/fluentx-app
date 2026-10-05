#!/usr/bin/env python3
import argparse, concurrent.futures, json, time, urllib.request

def one(url, timeout):
    started=time.perf_counter()
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'FluentX-LoadTest/1.0'})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            r.read()
            ok=200 <= r.status < 300
            code=r.status
    except Exception:
        ok=False; code=0
    return ok,code,(time.perf_counter()-started)*1000

def pct(values,p):
    values=sorted(values)
    i=min(len(values)-1,max(0,round((len(values)-1)*p)))
    return round(values[i],2)

ap=argparse.ArgumentParser()
ap.add_argument('--url',required=True)
ap.add_argument('--requests',type=int,default=500)
ap.add_argument('--concurrency',type=int,default=25)
ap.add_argument('--timeout',type=float,default=10)
ap.add_argument('--max-error-rate',type=float,default=.01)
ap.add_argument('--max-p95-ms',type=float,default=1500)
a=ap.parse_args()
start=time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=a.concurrency) as ex:
    rows=list(ex.map(lambda _:one(a.url,a.timeout),range(a.requests)))
elapsed=time.perf_counter()-start
lat=[x[2] for x in rows]
ok=sum(1 for x in rows if x[0])
error_rate=1-ok/len(rows)
report={'url':a.url,'requests':len(rows),'concurrency':a.concurrency,'success':ok,
'error_rate':round(error_rate,4),'elapsed_seconds':round(elapsed,2),
'requests_per_second':round(len(rows)/elapsed,2),'p50_ms':pct(lat,.5),
'p95_ms':pct(lat,.95),'p99_ms':pct(lat,.99),'max_ms':round(max(lat),2)}
print(json.dumps(report,indent=2))
if error_rate>a.max_error_rate or report['p95_ms']>a.max_p95_ms: raise SystemExit(1)
