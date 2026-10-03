import os,re,shutil
ROOT=os.path.dirname(os.path.abspath(__file__)); W=ROOT+"/www"
shutil.rmtree(W,ignore_errors=True); os.makedirs(W+"/fonts",exist_ok=True)
links=[]
for pkg,css in [("pt-sans",["400.css","700.css"]),("pt-sans-narrow",["400.css","700.css"]),("pt-serif",["400.css","700.css","400-italic.css"])]:
    src=f"{ROOT}/node_modules/@fontsource/{pkg}"; dst=f"{W}/fonts/{pkg}"
    os.makedirs(dst+"/files",exist_ok=True)
    for c in css:
        t=open(f"{src}/{c}").read()
        # keep only cyrillic + latin subsets, woff2 only
        blocks=re.findall(r'/\*[^*]*\*/\s*@font-face\s*{[^}]*}',t)
        keep=[b for b in blocks if re.search(r'/\*\s*[\w-]*-(cyrillic|latin)-\d',b)]
        out=[]
        for b in keep:
            b=re.sub(r",\s*url\([^)]*\.woff\)\s*format\('woff'\)","",b)
            for f in re.findall(r"url\(\./files/([^)]+\.woff2)\)",b): shutil.copy(f"{src}/files/{f}",f"{dst}/files/{f}")
            out.append(b)
        open(f"{dst}/{c}","w").write("\n".join(out))
        links.append(f'<link rel="stylesheet" href="fonts/{pkg}/{c}">')
h=open(ROOT+"/src/app.html").read()
d=open(ROOT+"/src/data.json").read().replace('</','<\\/')
h=h.replace("__DATA__",d)
h=re.sub(r'<link rel="preconnect"[^>]*>\s*','',h)
h=re.sub(r'<link href="https://fonts.googleapis.com[^>]*>',"\n".join(links),h)
open(W+"/index.html","w").write(h)
print("www size:",sum(os.path.getsize(os.path.join(dp,f)) for dp,dn,fn in os.walk(W) for f in fn))
print(links)
