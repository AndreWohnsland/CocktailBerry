from __future__ import annotations

from typing import Self


class Version:
    """Class to compare semantic version numbers."""

    def __init__(self, version_number: str | None) -> None:
        self.version = version_number
        # no version was found, just assume the worst, so using first version
        if version_number is None:
            version_number = "1.0.0"
        # remove "v" from version string
        if version_number.startswith("v"):
            version_number = version_number[1:]
        # otherwise split version for later comparison
        major_str, minor_str, *patch_str = version_number.split(".")
        major = int(major_str)
        minor = int(minor_str)
        # Some version like 1.0 or 1.1 don't got a patch property
        # List unpacking will return an empty list or a list of one
        # Future version should contain patch (e.g. 1.1.0) as well
        patch = int(patch_str[0]) if patch_str else 0
        self.major = major
        self.minor = minor
        self.patch = patch

    def __gt__(self, __o: Self, /) -> bool:
        return (self.major, self.minor, self.patch) > (__o.major, __o.minor, __o.patch)

    def __ge__(self, __o: Self, /) -> bool:
        return (self.major, self.minor, self.patch) >= (__o.major, __o.minor, __o.patch)

    def __eq__(self, __o: object, /) -> bool:
        if not isinstance(__o, Version):
            return False
        return self.version == __o.version

    def __str__(self) -> str:
        if self.version is None:
            return "No defined Version"
        return f"v{self.version}"

    def __repr__(self) -> str:
        if self.version is None:
            return "Version(not defined)"
        return f"Version({self.version})"

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))
