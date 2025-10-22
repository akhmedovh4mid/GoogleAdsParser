from typing import NotRequired, TypedDict


class NodeSelector(TypedDict):
    className: NotRequired[str]
    resourceId: NotRequired[str]
    description: NotRequired[str]
    descriptionStartsWith: NotRequired[str]
