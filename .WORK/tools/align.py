"""Phase 7: align guide English (ref_guide.txt) to JP strings (phase6/jp_master.json).

Per .sp file, local DP alignment against the whole guide line sequence.
A guide line may cover 1..3 consecutive JP strings of the same speaker (its
sentences are split across them). English is only ever taken from the guide.
Output: phase7/alignment.json + alignment.tsv (with confidence for review).
"""
import json, math, re, sys, collections

GUIDE = 'ref_guide.txt'
SPK = {**{b: 'Alice' for b in range(100, 107)}, **{b: 'Mikhail' for b in range(110, 114)},
       **{b: 'Lucille' for b in range(120, 124)}, 1: 'Mikhail', 3: 'Nabokov', 4: 'Wizard',
       5: 'Vampire', 6: 'Fairy', None: None}
NAMES = [('Alice', 'ã‚¢ãƒªã‚¹'), ('Mikhail', 'ãƒŸãƒ’ãƒ£ã‚¨ãƒ«'), ('Nabokov', 'ãƒŠãƒœã‚³ãƒ•'),
         ('Lucille', 'ãƒ«ã‚·ãƒ¼ãƒ«'), ('Father', 'ãŠçˆ¶ã•ã¾'), ('professor', 'åšå£«'),
         ('dress', 'ãƒ‰ãƒ¬ã‚¹'), ('genomeroid', 'ã‚²ãƒŽãƒ ãƒ­ã‚¤ãƒ‰'), ('Vampire', 'ãƒ´ã‚¡ãƒ³ãƒ‘ã‚¤ã‚¢'),
         ('Fairy', 'ãƒ•ã‚§ã‚¢ãƒªãƒ¼'), ('Wizard', 'ã‚¦ã‚£ã‚¶ãƒ¼ãƒ‰')]
MAXK = 4
JUMP = 4.0


def guide_units():
    L = open(GUIDE, encoding='utf-8', errors='replace').read().split('\n')
    units, scene, cur = [], '', None
    for n, l in enumerate(L):
        if n < 340:
            continue
        m = re.match(r'^\[(\d+)\]\.(.*)', l)
        if m:
            scene = m.group(1); cur = None; continue
        m = re.match(r'^([A-Z][A-Za-z\.\' ]{1,12}):\s+(\S.*)$', l)
        if m and not re.match(r'^(January|February|March|April|May|June|July|August|'
                              r'September|October|November|December)', m.group(1)):
            cur = {'line': n + 1, 'scene': scene, 'spk': m.group(1), 'en': m.group(2).strip()}
            units.append(cur); continue
        m = re.match(r'^\s{2,}/(.+)/\s*$', l)
        if m:
            units.append({'line': n + 1, 'scene': scene, 'spk': '/', 'en': m.group(1).strip()})
            cur = None; continue
        if cur and re.match(r'^ {6,}\S', l):
            cur['en'] += ' ' + l.strip(); continue
        if not l.strip() or l.startswith('---') or l.startswith('~~'):
            cur = None
    return units


def sentences(t):
    p = re.findall(r'.+?(?:[\.\?!â€¦~]+["\')]*(?=\s|$)|$)', t)
    return [s.strip() for s in p if s.strip()]


def jp_sent(j):
    return max(1, len(re.findall(r'[ã€‚ï¼ï¼Ÿâ€¦]+(?:ã€)?(?!$)', j.replace('{NL}', ''))) + 1)


def jlen(j):
    return len(re.sub(r'\{[^}]*\}', '', j))


def score(g, js):
    spk = SPK.get(js[0]['speaker'], '?')
    s = 0.0
    if spk is None:
        s += 1.5 if g['spk'] in ('/', 'Voice', 'Report', 'Diary') else -1.0
    elif g['spk'] == spk:
        s += 2.0
    elif g['spk'] == '/':
        s -= 5.0
    elif g['spk'] in ('Voice', '/'):
        s -= 1.0
    else:
        s -= 4.0
    jt = ''.join(x['jp'] for x in js)
    en = g['en']
    for e, j in NAMES:
        a, b = e.lower() in en.lower(), j in jt
        if a and b:
            s += 1.5
        elif b and not a:
            s -= 0.5
    for p in '?!':
        a, b = p in en, ('ï¼Ÿ' if p == '?' else 'ï¼') in jt
        s += 0.5 if a == b else -0.4
    r = (len(en) + 1) / (jlen(jt) + 1)
    s -= 1.0 * abs(math.log(r / 2.6))
    s -= 0.6 * abs(math.log((len(sentences(en)) + 1) / (sum(jp_sent(x['jp']) for x in js) + 1)))
    de, dj = re.fullmatch(r'[\.â€¦\s]+', en), re.fullmatch(r'(\{[^}]*\}|[â€¦ã€‚])+', jt)
    if de or dj:
        s += 1.5 if (de and dj) else -1.5
    return s - 0.5


def align_file(js, G):
    n, m = len(js), len(G)
    NEG = -1e9
    H = [[0.0] * (m + 1) for _ in range(n + 1)]
    B = [[None] * (m + 1) for _ in range(n + 1)]
    best = (0.0, 0, 0)
    for i in range(1, n + 1):
        Hi, Bi = H[i], B[i]
        run, runj = 0.0, 0
        for jj in range(1, m + 1):
            v, b = 0.0, None
            if run - JUMP > v: v, b = run - JUMP, ('jump', runj)
            t = H[i - 1][jj] - 2.0
            if t > v: v, b = t, ('skipjp',)
            t = Hi[jj - 1] - (0.2 if G[jj - 1]['spk'] == '/' else 1.2)
            if t > v: v, b = t, ('skipg',)
            for k in range(1, MAXK + 1):
                if i - k < 0:
                    break
                grp = js[i - k:i]
                if k > 1 and SPK.get(grp[-1]['speaker']) != SPK.get(grp[0]['speaker']):
                    break
                t = H[i - k][jj - 1] + score(G[jj - 1], grp) - 0.7 * (k - 1)
                if t > v: v, b = t, ('m', k)
            Hi[jj], Bi[jj] = v, b
            if v > run: run, runj = v, jj
            if v > run: run, runj = v, jj
            if v > best[0]:
                best = (v, i, jj)
    res, (v, i, jj) = [], best
    while i > 0 and jj > 0 and B[i][jj]:
        b = B[i][jj]
        if b[0] == 'skipjp':
            i -= 1
        elif b[0] == 'skipg':
            jj -= 1
        elif b[0] == 'jump':
            jj = b[1]
        else:
            k = b[1]
            res.append((i - k, k, jj - 1, H[i][jj] - H[i - k][jj - 1]))
            i -= k; jj -= 1
    return best[0], res[::-1]


def split_en(en, js):
    ss = sentences(en)
    k = len(js)
    if k == 1:
        return [en], True
    if len(ss) < k:
        return None, False
    w = [jlen(x['jp']) for x in js]
    tot, out, pos = sum(w), [], 0
    acc = 0
    for q in range(k - 1):
        acc += w[q]
        target = acc / tot * len(en)
        best, bi = None, None
        for e in range(pos + 1, len(ss) - (k - 2 - q)):
            l = len(' '.join(ss[:e]))
            if best is None or abs(l - target) < best:
                best, bi = abs(l - target), e
        out.append(' '.join(ss[pos:bi])); pos = bi
    out.append(' '.join(ss[pos:]))
    return out, True


def main():
    j = json.load(open('phase6/jp_master.json', encoding='utf-8'))
    G = guide_units()
    files = collections.OrderedDict()
    for x in j:
        files.setdefault(x['file'], []).append(x)
    rows = []
    for f, js in files.items():
        js.sort(key=lambda x: x['order'])
        tot, res = align_file(js, G)
        got = {}
        for i0, k, gi, sc in res:
            grp = js[i0:i0 + k]
            parts, ok = split_en(G[gi]['en'], grp)
            for q, x in enumerate(grp):
                got[x['idx']] = {'gline': G[gi]['line'], 'scene': G[gi]['scene'],
                                 'gspk': G[gi]['spk'],
                                 'en': parts[q] if ok else (G[gi]['en'] if q == 0 else ''),
                                 'k': k, 'score': round(sc / k, 2),
                                 'conf': 'high' if sc / k >= 3 and ok else
                                         'med' if sc / k >= 1 and ok else 'low'}
        for x in js:
            r = dict(x); r.update(got.get(x['idx'], {'en': None, 'conf': 'none'}))
            rows.append(r)
        print('%-22s %4d strings  matched %4d  score %7.1f' % (f, len(js), len(got), tot),
              file=sys.stderr)
    json.dump(rows, open('phase7/alignment.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    with open('phase7/alignment.tsv', 'w', encoding='utf-8') as o:
        o.write('file\tidx\torder\tspk\tconf\tscore\tgline\tjp\ten\n')
        for r in rows:
            o.write('\t'.join(str(r.get(c, '')) for c in
                              ('file', 'idx', 'order', 'speaker', 'conf', 'score', 'gline', 'jp', 'en')) + '\n')
    c = collections.Counter(r['conf'] for r in rows)
    print('confidence:', dict(c), 'guide units:', len(G))


if __name__ == '__main__':
    main()
