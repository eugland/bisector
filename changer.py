def sanitize_input(text):
    return ''.join(c for c in text if c not in {'<', '>'})

if __name__ == '__main__':
    s = "Ｆｕｌｌ－ｗｉｄｔｈ　＜ｓｃｒｉｐｔ＞ and half width <script>"
    rslt = sanitize_input(s)
    print(rslt)