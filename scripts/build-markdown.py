#!/usr/bin/env python3
import json
import argparse


def run(package_json: str):
    with open(package_json) as f:
        data = dict(json.load(f))
    data = data["contributes"]["configuration"]["properties"]
    if "$generated-start" in data:
        data.pop("$generated-start")
    if "$generated-end" in data:
        data.pop("$generated-end")

    return data


def render_desc(key, o) -> str:
    out = ""

    if key in o:
        desc = str(o.pop(key))
        out += f"{desc}\n\n"

    return out

def render_enum_desc(key, o) -> str:
    out = ""

    e = "enum"
    if e in o and key in o:
        out += "### possible values\n"
        out += "| value | description |\n"
        out += "| :-- | :---  |\n"

        for a, b in zip(o.pop(e), o.pop(key)):
            b = b.replace('|', '\|')
            out += f"| *{a}* | {b} |\n"

    return out


def render_option(o: dict) -> str:
    # print(option)
    out = ""

    # Head
    ty = "type"
    if ty in o:
        out += f"**{ty}:** `{o.pop(ty)}`</br>\n"

    de = "default"
    if de in o:
        default = o.pop(de)
        if default.__class__ is dict and len(default.keys()) > 0:
            default = json.dumps(default, indent=2)
            out += f"**{de}:**\n```json\n"
            out += f"{default}\n"
            out += "```\n\n"
        else:
            out += f"**{de}:** `{default}`</br>\n"

    mi = "minimum"
    if mi in o:
        out += f"**{mi}:** `{o.pop(mi)}`</br>\n"

    an = "anyOf"
    if an in o:
        out += f"**{an}:**\n```\n"
        for v in o.pop(an):
            out += f"{v}\n"
        out += "```\n"

    # Body
    mdd = "markdownDescription"
    d = "description"
    out += render_desc(mdd, o)
    out += render_desc(d, o)

    ed = "enumDescriptions"
    mded = "markdownEnumDescriptions"
    out += render_enum_desc(ed, o)
    out += render_enum_desc(mded, o)

    # remaining keys
    if len(o.keys()) == 0:
        return out

    out += "\n\n"
    out += "| key | value |\n"
    out += "| :-- | :---  |\n"

    for k in o.keys():
        out += f"| {k} | {o[k]} |\n"
    # if option.get('description') is not None:
    # out += str(option['description']) + "\n"

    return out


def make_markdown(opts) -> str:
    md = "# Rust Analyzer Options\n\n"
    md += "## TOC\n\n"

    # TOC
    for k in opts.keys():
        link = k.replace(".", "_")
        link = link.lower()
        md += f"* [{k}](#{link})\n"

    md += "\n"

    # Content
    for k, v in opts.items():
        id = k.replace('.', '_')
        id = id.lower()
        md += f"## [{k}](#{id}) {{#{id}}}\n"
        md += render_option(v)
        md += "\n"

    return md


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='renders rust analyzers package.json to usable html')
    parser.add_argument('package_json', action='store', default='package.json', type=str, nargs='?', help='Path to package.json [default: package.json]')
    parser.add_argument('rendered_md', action='store', default='rendered.md', type=str, nargs='?', help='Output file for the rendered markdown [default: rendered.md]')
    args = parser.parse_args()

    opts = run(args.package_json)
    md = make_markdown(opts)
    with open(args.rendered_md, "w") as f:
        f.write(md)
        f.flush()
