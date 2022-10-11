from argparse import ArgumentParser
from pathlib import Path

from ..src.winget.winget import WinGetPackage



def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--id', type=str, required=True, help="Id for winget")
    parser.add_argument('-v', '--version', type=str, help="specify a version. If not supplied, latest version will be retrieved")
    parser.add_argument('-o', '--outfolder', type=str, required=True, help="path to place download manifest files to.")

    return parser.parse_args()



def main():
    args = parse_args()
    winget_package = WinGetPackage(args.id)
    if args.version:
        package = winget_package[args.version]
    else:
        package = winget_package.get_latest_version()
    package.save_manifests(Path(args.outfolder))



if __name__ == "__main__":
    main()