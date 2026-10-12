r"""Phase 7 review helpers.

  python tools\review.py sheets          -> phase7\sheets\<file>.txt (for reviewers)
  python tools\review.py validate        -> checks tools-resources\final\*.json
  python tools\review.py merge           -> phase7\final_all.json

final\<file>.json = [{"idx": n, "gline": L, "en": "..."} or {"idx": n, "en": null, "note": "..."}]
Every "en" must be a verbatim substring (whitespace-normalised) of the guide
unit starting at line "gline" (the speaker line incl. its continuation lines).
"""
import json, os, re, sys, glob, collections
sys.path.insert(0, os.path.dirname(__file__))
import align

SPKN = {k: v for k, v in align.SPK.items()}


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def units_by_line():
    return {u['line']: u for u in align.guide_units()}


def sheets():
    rows = json.load(open('phase7/alignment.json', encoding='utf-8'))
    L = open(align.GUIDE, encoding='utf-8', errors='replace').read().split('\n')
    os.makedirs('phase7/sheets', exist_ok=True)
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r['file'], []).append(r)
    for f, rs in by.items():
        gl = [r['gline'] for r in rs if r.get('gline')]
        out = ['FILE %s  (%d strings, dialogue order)' % (f, len(rs)), '']
        for r in rs:
            out.append('idx=%d  spk=%s(%s)  auto_gline=%s' % (
                r['idx'], SPKN.get(r['speaker'], '?'), r['speaker'], r.get('gline')))
            out.append('  JP: ' + r['jp'])
            out.append('  EN: ' + (r['en'] or '-'))
        if gl:
            # guide excerpt: every run of matched lines with margin
            lines = set()
            for g in gl:
                lines.update(range(max(340, g - 15), min(len(L), g + 15)))
            out += ['', '=' * 30 + ' GUIDE EXCERPT (line numbers) ' + '=' * 30]
            prev = None
            for n in sorted(lines):
                if prev is not None and n != prev + 1:
                    out.append('   ...')
                out.append('%5d| %s' % (n + 1, L[n]))
                prev = n
        open('phase7/sheets/%s.txt' % f, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('wrote', len(by), 'sheets')


def validate(verbose=True):
    U = units_by_line()
    rows = json.load(open('phase7/alignment.json', encoding='utf-8'))
    idxs = collections.defaultdict(set)
    for r in rows:
        idxs[r['file']].add(r['idx'])
    errs, stats = [], collections.Counter()
    for p in sorted(glob.glob('tools-resources/final/*.json')):
        f = os.path.basename(p)[:-5]
        try:
            data = json.load(open(p, encoding='utf-8'))
        except Exception as e:
            errs.append('%s: bad json %s' % (f, e)); continue
        seen = set()
        for e in data:
            i = e.get('idx')
            if i not in idxs[f]:
                errs.append('%s idx %s: not a string of this file' % (f, i)); continue
            if i in seen:
                errs.append('%s idx %s: duplicate' % (f, i))
            seen.add(i)
            en = e.get('en')
            if en is None:
                stats['untranslated'] += 1; continue
            u = U.get(e.get('gline'))
            if not u:
                errs.append('%s idx %s: gline %s is not a guide speaker line' % (f, i, e.get('gline')))
                continue
            if norm(en) not in norm(u['en']) or not norm(en):
                errs.append('%s idx %s: EN not verbatim in guide line %s: %r' % (f, i, u['line'], en))
                continue
            stats['ok'] += 1
        miss = idxs[f] - seen
        if miss:
            errs.append('%s: missing idx %s' % (f, sorted(miss)))
    if verbose:
        for e in errs:
            print('ERR', e)
        print(dict(stats), 'files:', len(glob.glob('tools-resources/final/*.json')), 'errors:', len(errs))
    return errs


def merge():
    if validate(False):
        sys.exit('validate first')
    out = {}
    for p in sorted(glob.glob('tools-resources/final/*.json')):
        out[os.path.basename(p)[:-5]] = json.load(open(p, encoding='utf-8'))
    json.dump(out, open('phase7/final_all.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('merged', len(out))


if __name__ == '__main__':
    {'sheets': sheets, 'validate': validate, 'merge': merge}[sys.argv[1]]()
