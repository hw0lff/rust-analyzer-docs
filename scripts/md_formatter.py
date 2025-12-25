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
        attrs = map(lambda attr: tuple([attr, getattr(prop, attr)]), attrs)
        attrs = filter(lambda t: t[1] is not None, attrs)

        # remaining keys
        attrs = list(attrs)
        if len(attrs) == 0:
            return
        # table head
        self.md += "\n"
        self.md += "| key | value |"
        self.md += "| :-- | :---  |"
        # table body
        for attr, value in attrs:
            self.formatted_attrs.add(attr)
            self.md += f"| {attr} | {value} |"


def encode_link(link: str, prefix: str = "") -> str:
    link = link.replace('.', '_').replace(' ', '_')
    link = f"{prefix}{link}"
    return link.lower()


class ConfigurationFormatter:
    def __init__(self, conf: VscConfiguration):
        self.conf = conf

    def render_toc_header(self) -> str:
        self.md = MdBuffer()
        self.make_toc_section_header()
        return "\n".join(self.md.buffer)

    def render_toc_body(self) -> str:
        self.md = MdBuffer()
        self.make_toc_section_body()
        return "\n".join(self.md.buffer)

    def render_content_header(self) -> str:
        self.md = MdBuffer()
        self.make_content_section_header()
        return "\n".join(self.md.buffer)

    def render_content_body(self) -> str:
        self.md = MdBuffer()
        self.make_content_section_body()
        return "\n".join(self.md.buffer)

    # TOC section
    def make_toc_section_header(self):
        if self.conf.title is not None:
            link = encode_link(self.conf.title, "configuration_")
            self.md += f"### [{self.conf.title}](#{link})"
        else:
            link = encode_link("untitled", "configuration_")
            self.md += f"### [untitled configuration](#{link})"

    # TOC section
    def make_toc_section_body(self):
        for prop in self.conf.properties_named:
            link = encode_link(prop.name)
            self.md += f"* [{prop.name}](#{link})"

    # Content section
    def make_content_section_header(self):
        if self.conf.title is not None:
            link = encode_link(self.conf.title, "configuration_")
            self.md += f"## [{self.conf.title}](#{link}) {{#{link}}}"
        else:
            link = encode_link("untitled", "configuration_")
            self.md += f"## [untitled configuration](#{link}) {{#{link}}}"

    # Content section
    def make_content_section_body(self):
        for name, prop in self.conf.properties.items():
            id = encode_link(name)
            self.md += f"### [{name}](#{id}) {{#{id}}}"
            prop_fmt = PropertyFormatter(prop)
            self.md += prop_fmt.render()
            self.md += ""


# with the special $untitled key for configurations without a title
def group_configurations_by_title(
    configurations: list[VscConfiguration],
) -> dict[str, VscConfiguration]:
    grouped = {}
    untitled = "$untitled"
    for conf in configurations:
        if conf.title is None:
            if untitled not in grouped:
                grouped[untitled] = []
            grouped[untitled].append(conf)
        else:
            if conf.title not in grouped:
                grouped[conf.title] = []
            grouped[conf.title].append(conf)
    return grouped


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
        configurations = group_configurations_by_title(
            self.ext.contributes.configuration
        )
        conf_content_formatters = {}
        untitled_confs = []
        if "$untitled" in configurations:
            untitled_confs = configurations.pop("$untitled")

        # TOC
        for title, confs in configurations.items():
            conf_formatters = [ConfigurationFormatter(conf) for conf in confs]

            self.md += conf_formatters[0].render_toc_header()
            for conf_fmt in conf_formatters:
                self.md += conf_fmt.render_toc_body()
            self.md += ""

            conf_content_formatters[title] = conf_formatters

        # Untitled TOC will be placed at the end
        if len(untitled_confs) > 0:
            untitled_fmts = [ConfigurationFormatter(conf) for conf in untitled_confs]
            self.md += untitled_fmts[0].render_toc_header()
            for conf_fmt in untitled_fmts:
                self.md += conf_fmt.render_toc_body()
            self.md += ""

        # Content
        for title, conf_fmts in conf_content_formatters.items():
            self.md += conf_fmts[0].render_content_header()
            for conf_fmt in conf_fmts:
                self.md += conf_fmt.render_content_body()

        # Untitled Content will be placed at the end to
        if len(untitled_confs) > 0:
            self.md += untitled_fmts[0].render_content_header()
            for conf_fmt in untitled_fmts:
                self.md += conf_fmt.render_content_body()


def render_package_json_to_markdown(package_json: str) -> str:
    with open(package_json) as f:
        data = dict(json.load(f))
    vsc_ext = VscExtensionManifest.from_dict(data)
    fmt = MdFormatter(vsc_ext)
    md = fmt.render()
    return md


def write_markdown_to_file(rendered_md, file):
    with open(file, "w") as f:
        f.write(rendered_md)
        f.flush()


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

    rendered_md = render_package_json_to_markdown(args.package_json)
    write_markdown_to_file(rendered_md, args.rendered_md)
