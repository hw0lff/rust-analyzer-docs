#!/usr/bin/env python3
import json
import argparse
from vscode_extension import (
    VscExtensionManifest,
    VscConfiguration,
    VscConfigurationProperty,
)


class MdBuffer:
    def __init__(self):
        self.buffer = []

    def __iadd__(self, other):
        if not isinstance(other, list):
            other = [other]
        self.buffer += other
        return self

    def prepend(self, prefix):
        self.buffer = [prefix, *self.buffer]
        return self


class PropertyFormatter:
    def __init__(self, prop: VscConfigurationProperty):
        self.md = MdBuffer()
        self.formatted_attrs: set[str] = set()
        self.prop = prop

    def render(self) -> str:
        self.make_type(self.prop)
        self.make_default(self.prop)
        self.make_minimum_maximum(self.prop)
        self.make_anyOf(self.prop)
        self.make_description(self.prop)
        self.make_enum_descriptions(self.prop)
        self.make_rest(self.prop)
        return "\n".join(self.md.buffer)

    # Head
    def make_type(self, prop: VscConfigurationProperty):
        ty = "type"
        if prop.type is not None:
            self.formatted_attrs.add(ty)
            self.md += f"**{ty}:** `{prop.type}`</br>"

    # Head
    def make_default(self, prop: VscConfigurationProperty):
        de = "default"
        if prop.default is not None:
            self.formatted_attrs.add(de)
            default = prop.default
            if default.__class__ is dict and len(default.keys()) > 0:
                default = json.dumps(default, indent=2)
                self.md += f"**{de}:**\n```json"
                self.md += f"{default}"
                self.md += "```\n"
            else:
                self.md += f"**{de}:** `{default}`</br>"

    # Head
    def make_minimum_maximum(self, prop: VscConfigurationProperty):
        mi = "minimum"
        if prop.minimum is not None:
            self.formatted_attrs.add(mi)
            self.md += f"**{mi}:** `{prop.minimum}`</br>"

        ma = "maximum"
        if prop.maximum is not None:
            self.formatted_attrs.add(ma)
            self.md += f"**{ma}:** `{prop.maximum}`</br>"

    # Head
    def make_anyOf(self, prop: VscConfigurationProperty):
        an = "anyOf"
        if prop.anyOf is not None:
            self.formatted_attrs.add(an)
            self.md += f"**{an}:**\n```"
            for v in prop.anyOf:
                self.md += f"{v}"
            self.md += "```"

    # Body
    def make_description(self, prop: VscConfigurationProperty):
        kinds = ["markdownDescription", "description"]
        for kind in kinds:
            if hasattr(prop, kind) and getattr(prop, kind) is not None:
                self.formatted_attrs.add(kind)
                desc = str(getattr(prop, kind))
                self.md += f"{desc}\n"

    # Body
    def make_enum_descriptions(self, prop: VscConfigurationProperty):
        kinds = ["enumDescriptions", "markdownEnumDescriptions"]
        for kind in kinds:
            if (
                prop.enum is not None
                and hasattr(prop, kind)
                and getattr(prop, kind) is not None
            ):
                self.formatted_attrs.add("enum")
                self.formatted_attrs.add(kind)
                self.md += "### possible values"
                self.md += "| value | description |"
                self.md += "| :-- | :---  |"

                for a, b in zip(prop.enum, getattr(prop, kind)):
                    self.md += f"| *{a}* | {b} |"

    # Tail
    def make_rest(self, prop: VscConfigurationProperty):
        attrs = filter(lambda attr: not attr.startswith("__"), dir(prop))
        attrs = filter(lambda attr: not callable(getattr(prop, attr)), attrs)
        attrs = filter(lambda attr: attr not in self.formatted_attrs, attrs)
        attrs = map(lambda attr: tuple([attr, getattr(prop,attr)]), attrs)
        attrs = filter(lambda t: t[1] is not None, attrs)
        attrs = list(attrs)
        # remaining keys
        if len(attrs) == 0:
            return

        self.md += "\n"
        self.md += "| key | value |"
        self.md += "| :-- | :---  |"

        for attr, value in attrs:
            print(type(attr), type(value))
            print(attr, value)
            self.formatted_attrs.add(attr)
            self.md += f"| {attr} | {value} |"


class ConfigurationFormatter:
    def __init__(self, conf: VscConfiguration):
        self.conf = conf

    def render_toc(self) -> str:
        self.md = MdBuffer()
        self.make_toc_section()
        return "\n".join(self.md.buffer)

    def render_content(self) -> str:
        self.md = MdBuffer()
        self.make_content_section()
        return "\n".join(self.md.buffer)

    # TOC section
    def make_toc_section(self):
        if self.conf.title is not None:
            link = self.conf.title.replace(".", "_")
            link = f"configuration_{link}"
            self.md += f"### [configuration {self.conf.title}](#{link})"
        for prop in self.conf.properties_named:
            link = prop.name.replace(".", "_")
            link = link.lower()
            self.md += f"* [{prop.name}](#{link})"

        self.md += "\n"

    # Content section
    def make_content_section(self):
        for name, prop in self.conf.properties.items():
            id = name.replace(".", "_")
            id = id.lower()
            self.md += f"## [{name}](#{id}) {{#{id}}}"
            prop_fmt = PropertyFormatter(prop)
            self.md += prop_fmt.render()
            self.md += ""


class MdFormatter:
    def __init__(self, ext: VscExtensionManifest):
        self.md = MdBuffer()
        self.ext = ext

    def render(self) -> str:
        self.make_markdown_header()
        self.make_document()
        return "\n".join(self.md.buffer)

    def make_markdown_header(self):
        self.md += "Rust Analyzer Options\n"
        self.md += "## TOC\n"

    def make_document(self):
        conf_formatters = [
            ConfigurationFormatter(conf) for conf in self.ext.contributes.configuration
        ]

        for conf_fmt in conf_formatters:
            self.md += conf_fmt.render_toc()

        for conf_fmt in conf_formatters:
            self.md += conf_fmt.render_content()


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

    ma = "maximum"
    if ma in o:
        out += f"**{ma}:** `{o.pop(ma)}`</br>\n"

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
        id = k.replace(".", "_")
        id = id.lower()
        md += f"## [{k}](#{id}) {{#{id}}}\n"
        md += render_option(v)
        md += "\n"

    return md


def render_with_classes(package_json: str) -> str:
    from vscode_extension import VscExtensionManifest

    with open(package_json) as f:
        data = dict(json.load(f))
    vsc_ext = VscExtensionManifest.from_dict(data)
    fmt = MdFormatter(vsc_ext)
    md = fmt.render()
    return md
    # print(vsc_ext.contributes.configuration[0].properties_named[0].name)
    # print(md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="renders rust analyzers package.json to usable html"
    )
    parser.add_argument(
        "package_json",
        action="store",
        default="package.json",
        type=str,
        nargs="?",
        help="Path to package.json [default: package.json]",
    )
    parser.add_argument(
        "rendered_md",
        action="store",
        default="rendered.md",
        type=str,
        nargs="?",
        help="Output file for the rendered markdown [default: rendered.md]",
    )
    args = parser.parse_args()

    md = render_with_classes(args.package_json)
    with open(args.rendered_md, "w") as f:
        f.write(md)
        f.flush()

    import sys
    sys.exit(0)

    opts = run(args.package_json)
    md = make_markdown(opts)
    with open(args.rendered_md, "w") as f:
        f.write(md)
        f.flush()
