from dataclasses import dataclass


JSONSchemaType = dict | str | list | int | bool
IJSONSchemaMap = dict
IJSONSchema = dict
IJSONSchemaSnippet = dict


@dataclass
class VscConfigurationProperty:
    id: None | str = None
    # "$id": None | str = None
    # "$schema": None | str = None
    type: None | JSONSchemaType | list[JSONSchemaType] = None
    title: None | str = None
    default: None = None
    definitions: None | IJSONSchemaMap = None
    description: None | str = None
    properties: None | IJSONSchemaMap = None
    patternProperties: None | IJSONSchemaMap = None
    additionalProperties: None | bool | IJSONSchema = None
    minProperties: None | int = None
    maxProperties: None | int = None
    dependencies: None | IJSONSchemaMap | dict[str, list[str]] = None
    items: None | IJSONSchema | list[IJSONSchema] = None
    minItems: None | int = None
    maxItems: None | int = None
    uniqueItems: None | bool = None
    additionalItems: None | bool | IJSONSchema = None
    pattern: None | str = None
    minLength: None | int = None
    maxLength: None | int = None
    minimum: None | int = None
    maximum: None | int = None
    exclusiveMinimum: None | bool | int = None
    exclusiveMaximum: None | bool | int = None
    multipleOf: None | int = None
    required: None | list[str] = None
    # "$ref": None | str = None
    anyOf: None | list[IJSONSchema] = None
    allOf: None | list[IJSONSchema] = None
    oneOf: None | list[IJSONSchema] = None
    # "not": None | IJSONSchema = None
    enum: None | list = None
    format: None | str = None

    # schema draft 06
    const: None = None
    contains: None | IJSONSchema = None
    propertyNames: None | IJSONSchema = None
    examples: None | list = None

    # schema draft 07
    # "$comment": None | str = None
    # "if": None | IJSONSchema = None
    # "then": None | IJSONSchema = None
    # "else": None | IJSONSchema = None

    # schema 2019-09
    unevaluatedProperties: None | bool | IJSONSchema = None
    unevaluatedItems: None | bool | IJSONSchema = None
    minContains: None | int = None
    maxContains: None | int = None
    deprecated: None | bool = None
    dependentRequired: None | dict[str, list[str]] = None
    dependentSchemas: None | IJSONSchemaMap = None
    # "$defs": None | { [name: str]: IJSONSchema } = None
    # "$anchor": None | str = None
    # "$recursiveRef": None | str = None
    # "$recursiveAnchor": None | str = None
    # "$vocabulary": None | any = None

    # schema 2020-12
    prefixItems: None | list[IJSONSchema] = None
    # "$dynamicRef": None | str = None
    # "$dynamicAnchor": None | str = None

    # VSCode extensions

    defaultSnippets: None | list[IJSONSchemaSnippet] = None
    errorMessage: None | str = None
    patternErrorMessage: None | str = None
    deprecationMessage: None | str = None
    markdownDeprecationMessage: None | str = None
    enumDescriptions: None | list[str] = None
    markdownEnumDescriptions: None | list[str] = None
    markdownDescription: None | str = None
    doNotSuggest: None | bool = None
    suggestSortText: None | str = None
    allowComments: None | bool = None
    allowTrailingCommas: None | bool = None

    # my own findings
    scope: None | str = None

    @staticmethod
    def from_dict(data: dict) -> "VscConfigurationProperty":
        return VscConfigurationProperty(**data)


@dataclass
class VscConfigurationPropertyNamed:
    name: str
    prop: VscConfigurationProperty


@dataclass
class VscConfiguration:
    properties: dict[str, VscConfigurationProperty]
    properties_named: list[VscConfigurationPropertyNamed]
    id: str | None
    order: int | None
    title: str | None

    @staticmethod
    def from_dict(data: dict) -> "VscConfiguration":
        id = data.get("id")
        order = data.get("order")
        title = data.get("title")
        properties = data.pop("properties")
        # remove unused properties
        if "$generated-start" in properties:
            properties.pop("$generated-start")
        if "$generated-end" in properties:
            properties.pop("$generated-end")
        properties = {
            name: VscConfigurationProperty.from_dict(prop)
            for name, prop in properties.items()
        }
        properties_named = [
            VscConfigurationPropertyNamed(name, prop)
            for name, prop in properties.items()
        ]
        return VscConfiguration(properties, properties_named, id, order, title)


@dataclass
class VscExtensionContributions:
    # configuration: VscConfiguration | [VscConfiguration]
    configuration: list[VscConfiguration]
    rest: dict | None

    @staticmethod
    def from_dict(data: dict) -> "VscExtensionContributions":
        configuration = data.pop("configuration")
        # make it always into a list
        if not isinstance(configuration, list):
            configuration = [configuration]
        configuration = filter(
            lambda conf: not conf.get("title").startswith("$generated"), configuration
        )
        configuration = filter(
            lambda conf: conf.get("properties") is not None, configuration
        )
        configuration = [VscConfiguration.from_dict(conf) for conf in configuration]
        return VscExtensionContributions(configuration, data)


@dataclass
class VscExtensionManifest:
    name: str
    contributes: VscExtensionContributions
    rest: dict | None

    @staticmethod
    def from_dict(data: dict) -> "VscExtensionManifest":
        # contributes = data["contributes"]["configuration"]["properties"]
        name = data.pop("name")
        contributes = data.pop("contributes")
        contributes = VscExtensionContributions.from_dict(contributes)
        return VscExtensionManifest(name, contributes, data)
