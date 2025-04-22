import unicodedata


def sanitize_input(text):
    # give me code to convert full width text to half:
    unicodedata.normalize('NFKC', text)
    print(f"[AUDIT] raw input: {text}")  # <-- new logging
    return ''.join(c for c in text if c not in {'<', '>'})

if __name__ == '__main__':
    s = "Ｆｕｌｌ－ｗｉｄｔｈ　＜ｓｃｒｉｐｔ＞ and half width <script>"
    rslt = sanitize_input(s)
    print(rslt)