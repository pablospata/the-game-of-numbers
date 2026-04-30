"""Analyze the raw JSON text to find hidden paragraph markers."""
import urllib.request, json, unicodedata

req = urllib.request.Request(
    'https://nickmurraynewsletters.s3.amazonaws.com/TGON-2021/files/data/search.json',
    headers={'User-Agent': 'Mozilla/5.0'}
)
data = json.load(urllib.request.urlopen(req))
pages = {p['pageNumber']: p['data'] for p in data['results']['page']}

# Page 54 = chapter 11 Authenticity
text = pages[54]

# Known paragraph breaks from user's manual formatting:
# Break after 'type of pen.' before 'This is a perfect'
# Break after 'any given moment.' before 'You have to be'
breaks = [
    ('type of pen.', 'This is a perfect'),
    ('any given moment.', 'You have to be'),
]

for before, after in breaks:
    idx_b = text.find(before)
    idx_a = text.find(after)
    if idx_b > 0 and idx_a > 0:
        # Get the text between the end of 'before' and start of 'after'
        gap_start = idx_b + len(before)
        gap_end = idx_a
        gap = text[gap_start:gap_end]
        print(f"Between '{before}' and '{after}':")
        print(f"  Gap text: {repr(gap)}")
        print(f"  Gap length: {len(gap)}")
        print()

# Also check a known NON-break (within same paragraph)
# "who you are." -> "At exactly that moment" is NOT a paragraph break
non_break = ('who you are.', 'At exactly')
idx_b = text.find(non_break[0])
idx_a = text.find(non_break[1])
if idx_b > 0 and idx_a > 0:
    gap_start = idx_b + len(non_break[0])
    gap_end = idx_a
    gap = text[gap_start:gap_end]
    print(f"NON-BREAK between '{non_break[0]}' and '{non_break[1]}':")
    print(f"  Gap text: {repr(gap)}")
    print(f"  Gap length: {len(gap)}")
    print()

# Check ALL special characters in the page
print("All special/non-ASCII characters in page 54:")
special = set()
for i, c in enumerate(text):
    cat = unicodedata.category(c)
    if cat not in ('Lu', 'Ll', 'Nd', 'Zs', 'Po', 'Ps', 'Pe'):  # not letter/digit/space/punct
        special.add((c, repr(c), cat, unicodedata.name(c, '?')))
for s in sorted(special, key=lambda x: x[2]):
    print(f"  {s[1]:10} cat={s[2]} name={s[3]}")

# Now check multiple pages to see if there's a pattern
print("\n\nChecking for double-spaces or other patterns across several pages:")
for pn in [23, 24, 25, 54, 55, 79, 80]:
    t = pages[pn]
    double_spaces = t.count('  ')
    tabs = t.count('\t')
    newlines = t.count('\n')
    print(f"  Page {pn}: double_spaces={double_spaces}, tabs={tabs}, newlines={newlines}, len={len(t)}")
