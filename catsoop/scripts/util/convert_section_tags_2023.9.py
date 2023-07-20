import os
import re
import sys

section = r"((?:chapter)|(?:(?:sub){0,2}section))\*?"
section_star = r"<(?P<tag>%s)>(?P<body>.*?)</(?P=tag)>" % section
section_star = re.compile(section_star, re.MULTILINE | re.DOTALL | re.IGNORECASE)


def _replacer(m):
    d = m.groupdict()
    return "<catsoop-%s>%s</catsoop-%s>" % (d["tag"], d["body"], d["tag"])


for root, dirs, files in os.walk(sys.argv[1]):
    if "__STATIC__" in dirs:
        dirs.remove("__STATIC__")
    for f in files:
        if not any(f.endswith(i) for i in (".catsoop", ".py", ".md", ".xml")):
            continue
        fullname = os.path.join(root, f)
        try:
            with open(fullname, "r") as f:
                text = f.read()
        except:
            continue
        print(list(section_star.finditer(text)))
        text = re.sub(section_star, _replacer, text)
        with open(fullname, "w") as f:
            f.write(text)
