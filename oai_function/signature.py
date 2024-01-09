import inspect
from functools import wraps
from docstring_parser import parse, Docstring
from dataclasses import dataclass


@dataclass
class ParamSpec:
    name: str
    collection_type: str | None
    child_type: str | None
    description: str
    optional: bool
    # enums: list[str] | None = None


def detect_type(type_str):
    """Detects the type of a string representation of a type.

    Args:
        type_str (str): The string representation of the type.

    Returns:
        tuple: A tuple containing the type and a boolean indicating if the type is optional.
    """
    type_str = type_str.replace(" ", "")

    if type_str.startswith("None|"):
        return type_str[5:], True
    elif "|None" in type_str:
        parts = type_str.split("|None")
        return "".join(parts), True
    elif type_str.startswith("Optional[") and type_str.endswith("]"):
        return type_str[9:-1].strip(), True
    elif type_str.startswith("Union[") and type_str.endswith("]"):
        return "|".join([detect_type(t)[0] for t in type_str[6:-1].split(",")]), True
    elif type_str.lower().startswith("list[") and type_str.endswith("]"):
        return "List[" + detect_type(type_str[5:-1])[0] + "]", False
    elif type_str.lower().startswith("dict[") and type_str.endswith("]"):
        return "Dict[" + detect_type(type_str[5:-1])[0] + "]", False
    elif type_str.startswith("Annotated(") and type_str.endswith(")"):
        return detect_type(type_str[10:-1])[0], False
    # elif type_str.startswith("Literal[") and type_str.endswith("]"):
    #     return type_str

    else:
        return type_str, False


def resolve_arg_type(arg) -> ParamSpec:
    """Checks the type of an argument.

    Args:
        arg (str): The argument to check.

    Raises:
        TypeError: If the argument is not of type str.
    """
    detected_type, optional = detect_type(arg.type_name)
    if detected_type.startswith("List["):
        type_def = ParamSpec(arg.arg_name, "List", detected_type[5:-1], arg.description, optional)
    elif "[" not in detected_type:
        type_def = ParamSpec(arg.arg_name, None, detected_type, arg.description, optional)
    else:
        raise TypeError("Unsupported type: " + detected_type)

    if "str" in type_def.child_type:
        type_def.child_type = "string"
    elif "int" in type_def.child_type or "float" in type_def.child_type:
        type_def.child_type = "number"

    return type_def


def get_fn_description(signature: Docstring) -> str:
    """Gets the description of a function from parsed docstring."""
    description = ""
    if signature.long_description:
        description += signature.long_description

    if signature.short_description:
        description += f"\n{signature.short_description}"

    return description


def create_openai_signature(parsed_docstring: Docstring) -> str:
    """Creates an OpenAI signature from a parsed docstring.

    Args:
        parsed_docstring (Docstring): The parsed docstring.

    Returns:
        str: The OpenAI function signature.
    """
    signature = dict()
    signature["type"] = "function"
    specs = dict()
    specs["name"] = parsed_docstring.name
    specs["description"] = get_fn_description(parsed_docstring)
    params = dict(type="object")
    params["properties"] = dict()
    required = []
    for arg in parsed_docstring.params:
        param_spec = resolve_arg_type(arg)
        if param_spec.collection_type:
            params["properties"][param_spec.name] = dict(type="array", items=dict(type=param_spec.child_type), description=param_spec.description)
        else:
            params["properties"][param_spec.name] = dict(type=param_spec.child_type, description=param_spec.description)

        optional = param_spec.optional or "default" in param_spec.description.lower()
        if not optional:
            required.append(param_spec.name)

    params["required"] = required
    specs["params"] = params

    return specs


def oai_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Getting the docstring
    docstring = inspect.getdoc(func)
    if not docstring:
        docstring = "No docstring provided."

    parsed = parse(docstring)
    parsed.name = func.__name__

    signature = parsed

    wrapper.signature = create_openai_signature(signature)
    return wrapper
