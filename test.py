from typing import Optional, Union

def fn(a: float, b: str | None = None) -> Union[int, str]:
    """_summary_

    Args:
        a (float): _description_
        b (str | None, optional): _description_. Defaults to None.

    Returns:
        Union[int, str]: _description_
    """
    
    if a is None:
        return "None"
    return a