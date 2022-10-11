import json
from pathlib import Path
import re
from typing import Any

import requests
import yaml

from src.winget.winget_manifests import Architecture, DefaultLocaleManifest_1_2_0, InstallMode, Installer, InstallerManifest_1_2_0, InstallerType, Locale, Scope, UpgradeBehavior, VersionManifest

BASE_URI = "https://api.github.com/repos/microsoft/winget-pkgs/contents/manifests"
BASIC_SEMVER_REGEX = re.compile(r'^\d+\.\d+\.\d+$')

__all__ = ["WinGetPackage", "WinGetPackageVersion"]

class WinGetPackage:
    def __init__(self, id_) -> None:
        self.id = id_
        self.publisher, self.name = id_.split('.', maxsplit=1)
        self.api_url = f"{BASE_URI}/{id_[0].lower()}/{id_.replace('.','/')}"
        self.versions = set()
        self.find_versions()
        self.__package_versions = {}


    def find_versions(self):
        if self.versions:
            return self.versions
        r = requests.get(self.api_url)
        json_res = r.json()
        if "message" in json_res:
            error_string = f"error getting versions\n{json.dumps(json_res, indent=2)}"
            raise ValueError(error_string)
        self.versions = set([f["name"] for f in json_res if f["type"] == "dir"])
        return self.versions

    def get_latest_version(self):
        return self[get_latest_semver(self.versions)]

    def __getitem__(self, indices):
        # if not isinstance(indices, tuple):
        # print(indices)
        if not self.versions:
            self.find_versions()
        if not isinstance(indices, str):
            raise TypeError(f"Arguments to {WinGetPackage.__getitem__.__qualname__} must be Strings not {type(indices)}.")
        if indices not in self.versions:
            return KeyError(f"{indices} not found in {self.__class__.__name__}.versions.")
        if indices in self.__package_versions:
            return self.__package_versions[indices]
        wgpv = WingetPackageVersion(self.id, indices)
        self.__package_versions[indices] = wgpv
        return wgpv

class WingetPackageVersion:
    def __init__(self, id_: str, version: str) -> None:
        self.id = id_
        self.version = version
        self.publisher, self.name = id_.split('.', maxsplit=1)
        self.api_url = f"{BASE_URI}/{id_[0].lower()}/{id_.replace('.','/')}/{version}"

        self.api_contents = None
        self.manifests = {}

        self.version_manifest = None
        self.default_locale_manifest = None
        self.installer_manifest = None

        self.__get_api_contents()

    def __get_api_contents(self):
        if self.api_contents:
            return self.api_contents
        r = requests.get(self.api_url)
        json_res = r.json()
        if "message" in json_res:
            error_string = f"error getting api content\n{json.dumps(json_res, indent=2)}"
            raise ValueError(error_string)
        self.api_contents = json_res
        return self.api_contents

    def get_manifests(self):
        if self.manifests:
            return self.manifests
        if not self.api_contents:
            error_string = f"error getting manifests, self.api_contents not set"
            raise ValueError(error_string)
        files = [f for f in self.api_contents if f["type"] == "file"]
        for file_ in files:
            name = file_["name"]
            url = file_["download_url"]

            r = requests.get(url)
            text_res = r.text
            self.manifests[name] = text_res
        return self.manifests

    def parse_manifests(self):
        self.__parse_version_manifest()
        self.__parse_default_locale_manifest()
        self.__parse_installer_manifest()

    def __parse_version_manifest(self):
        if not self.manifests:
            raise ValueError("Cannot parse version manifest, no manifests found.")
        expected_name = f"{self.id}.yaml"
        dd = yaml.safe_load(self.manifests[expected_name])
        self.version_manifest = VersionManifest(
            dd["PackageIdentifier"],
            dd["PackageVersion"],
            dd["DefaultLocale"],
            dd["ManifestType"],
            dd["ManifestVersion"]
        )
        return self.version_manifest

    def __parse_default_locale_manifest(self):
        if not self.manifests:
            raise ValueError("Cannot parse default locale manifest, no manifests found.")
        if not self.version_manifest:
            raise ValueError("Cannot parse default locale manifest, no version manifest found.")
        locale_string = self.version_manifest.default_locale
        expected_name = f"{self.id}.locale.{locale_string}.yaml"
        dd = yaml.safe_load(self.manifests[expected_name])
        if dd["ManifestVersion"] != "1.2.0":
            raise NotImplementedError("Only 1.2.0 currently supported")
        self.default_locale_manifest = DefaultLocaleManifest_1_2_0(
            package_identifier = dd["PackageIdentifier"],
            package_version = dd["PackageVersion"],
            package_locale=dd["PackageLocale"],
            publisher = dd["Publisher"],
            publisher_url = dd["PublisherUrl"],
            publisher_support_url= dd["PublisherSupportUrl"],
            privacy_url=dd["PrivacyUrl"],
            author=dd["Author"],
            package_name=dd["PackageName"],
            package_url=dd["PackageUrl"],
            license=dd["License"],
            license_url=dd["LicenseUrl"],
            copyright=dd["Copyright"],
            copyright_url=dd["CopyrightUrl"],
            short_description=dd["ShortDescription"],
            moniker=dd["Moniker"],
            tags=dd["Tags"],
            manifest_type=dd["ManifestType"],
            manifest_version=dd["ManifestVersion"]
        )
        return self.default_locale_manifest

    def __parse_installer_manifest(self):
        if not self.manifests:
            raise ValueError("Cannot parse default locale manifest, no manifests found.")
        expected_name = f"{self.id}.installer.yaml"
        dd = yaml.safe_load(self.manifests[expected_name])
        manifest_type = dd["ManifestType"]
        manifest_version = dd["ManifestVersion"]
        if manifest_version != "1.2.0":
            raise NotImplementedError("Only 1.2.0 currently supported")
        package_identifier = dd["PackageIdentifier"]
        package_version = dd["PackageVersion"]
        minimum_os_version = dd["MinimumOSVersion"]
        install_mode_strings = dd["InstallModes"]
        install_modes = []
        for im in install_mode_strings:
            if im not in [v.value for v in InstallMode]:
                raise ValueError(f"Unknown InstallMode specified: {im}")
            if im == InstallMode.INTERACTIVE:
                install_modes.append(InstallMode.INTERACTIVE)
            elif im == InstallMode.SILENT:
                install_modes.append(InstallMode.SILENT)
            elif im == InstallMode.SILENT_WITH_PROGRESS:
                install_modes.append(InstallMode.SILENT_WITH_PROGRESS) 
        commands = dd["Commands"]
        file_extensions = dd["FileExtensions"]
        installers = self.__parse_installers(dd["Installers"])
        self.installer_manifest = InstallerManifest_1_2_0(
            manifest_type=manifest_type,
            manifest_version=manifest_version,
            package_identifier=package_identifier,
            package_version=package_version,
            minimum_os_version=minimum_os_version,
            install_modes=install_modes,
            commands=commands,
            file_extensions=file_extensions,
            installers=installers
        )
        return self.installer_manifest

    def __parse_installers(self, installer_dicts: list[dict[str, Any]]):
        installers: list[Installer] = []
        for installer_dict in installer_dicts:
            installers.append(self.__parse_installer(installer_dict))
        return installers

    def __parse_installer(self, installer_dict):
        i = installer_dict
        installer_locale = i["InstallerLocale"]
        if installer_locale not in [v.value for v in Locale]:
            raise ValueError(f"Unknown InstallerLocale specified: {installer_locale}")
        architecture = i["Architecture"]
        if architecture not in [v.value for v in Architecture]:
            raise ValueError(f"Unknown Architecture specified: {architecture}")
        installer_type = i["InstallerType"]
        if installer_type not in [v.value for v in InstallerType]:
            raise ValueError(f"Unknown InstallerType specified: {installer_type}")
        scope = i["Scope"]
        if scope not in [v.value for v in Scope]:
            raise ValueError(f"Unknown Scope specified: {scope}")
        installer_url = i["InstallerUrl"]
        installer_sha256 = i["InstallerSha256"]
        installer_switches = i["InstallerSwitches"]
        upgrade_behavior = i["UpgradeBehavior"]
        if upgrade_behavior not in [v.value for v in UpgradeBehavior]:
            raise ValueError(f"Unknown UpgradeBehaviour specified: {upgrade_behavior}")
        apps_and_features_entries = i["AppsAndFeaturesEntries"]
        
        return Installer(
            installer_locale=installer_locale,
            architecture=architecture,
            installer_type=installer_type,
            scope=scope,
            installer_url=installer_url,
            installer_sha256=installer_sha256,
            installer_switches=installer_switches,
            upgrade_behavior=upgrade_behavior,
            apps_and_features_entries=apps_and_features_entries
        )

    def save_manifests(self, root_dir: Path):
        base_dir = Path(root_dir).absolute()
        base_dir.mkdir(exist_ok=True)
        publisher_package_dir = base_dir / f"{self.publisher}.{self.name}" 
        publisher_package_dir.mkdir(exist_ok=True)
        version_dir = publisher_package_dir / self.version
        version_dir.mkdir(exist_ok=True)
        for file_name, manifest in self.get_manifests().items():
            file_path = Path(version_dir / file_name).absolute()
            with file_path.open("w") as f:
                f.write(manifest)


def get_latest_semver(versions: set) -> str:
    semver_versions = [v for v in versions if BASIC_SEMVER_REGEX.match(v)]
    if not semver_versions:
        raise ValueError('Unable to find semver versions. Perhaps package does not use semantic versioning?')
    tuples = []
    for v in semver_versions:
        major, minor, patch = v.split('.', maxsplit=2)
        tuples.append((major, minor, patch))
    int_tuples = []
    for t in tuples:
        nt = (int(t[0]), int(t[1]), int(t[2]))
        int_tuples.append(nt)
    sorted_tuples = sorted(int_tuples)
    most_recent = sorted_tuples[-1]
    return f"{most_recent[0]}.{most_recent[1]}.{most_recent[2]}"


