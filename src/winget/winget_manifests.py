"""
winget_manifests.py

A first attempt at converting manifest schemas to python classes.
"""

import enum
from dataclasses import dataclass

@dataclass
class VersionManifest:
    """
    PackageIdentifier: Python.Python.3.10
    PackageVersion: 3.10.7
    DefaultLocale: en-US
    ManifestType: version
    ManifestVersion: 1.2.0
    """
    package_identifier: str
    package_version: str
    default_locale: str
    manifest_type: str
    manifest_version: str


@dataclass
class DefaultLocaleManifest_1_2_0:
    package_identifier: str # Python.Python.3.10
    package_version: str # 3.10.7
    package_locale: str # en-US
    publisher: str # Python Software Foundation
    publisher_url: str # https://www.python.org
    publisher_support_url: str # https://www.python.org/doc/
    privacy_url: str # https://www.python.org/privacy/
    author: str # Python Software Foundation
    package_name: str # Python 3
    package_url: str # https://www.python.org
    license: str # PSF LICENSE AGREEMENT FOR PYTHON
    license_url: str # https://docs.python.org/3/license.html
    copyright: str # Copyright ©2001-2022. Python Software Foundation.
    copyright_url: str # https://docs.python.org/3/license.html
    short_description: str # Python is a programming language that lets you work more quickly and integrate your systems more effectively.
    moniker: str # python3.10
    tags: list[str] # python, programming-language
    manifest_type: str # defaultLocale
    manifest_version: str # 1.2.0

@dataclass
class InstallerManifest_1_2_0:
    manifest_type: str # installer
    manifest_version: str # 1.2.0
    package_identifier: str # Python.Python.3.10
    package_version: str # 3.10.7
    minimum_os_version: str # 10.0.0.0
    install_modes: list["InstallMode"] # InstallMode
    commands: list[str] # py, python
    file_extensions: list[str] # py, pyw, pyc, pyo
    installers: list["Installer"]
    
@dataclass
class Installer:
    installer_locale: "Locale"
    architecture: "Architecture"
    installer_type: "InstallerType"
    scope: "Scope"
    installer_url: str
    installer_sha256: str
    installer_switches: dict[str, str]
    upgrade_behavior: "UpgradeBehavior"
    apps_and_features_entries: dict[str, str]

class InstallMode(enum.Enum):
    INTERACTIVE = "interactive"
    SILENT = "silent"
    SILENT_WITH_PROGRESS = "silentWithProgress"



class Locale(enum.Enum):
    EN_US = "en-US"

class Architecture(enum.Enum):
    x64 = "x64"
    x86 = "x86"

class InstallerType(enum.Enum):
    BURN = "burn"
    NULLSOFT = "nullsoft"
    
class Scope (enum.Enum):
    USER = "user"
    MACHINE = "machine"

class UpgradeBehavior(enum.Enum):
    INSTALL = "install"
    UNINSTALL_PREVIOUS = "uninstallPrevious"


class ManifestVersion(enum.Enum):
    ONE_POINT_TWO = "1.2.0"
    ONE_POINT_ONE = "1.1.0"
    ONE_POINT_ZERO = "1.0.0"

class ManifestType(enum.Enum):
    INSTALLER = "installer"
    VERSION = "version"
    DEFAULT_LOCALE = "defaultLocale"
