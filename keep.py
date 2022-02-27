import argparse

from keeper import Keeper


def main(args):
    keeper = Keeper()

    if args["download"]:
        keeper.download()

    if args["upload"]:
        keeper.upload()


def get_parser():
    parser = argparse.ArgumentParser(
        description="Sync between Google Keep and local files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-d", "--download", action="store_true", help="Download and save notes as files"
    )
    parser.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help="Sync changes to local list files with Google Keep",
    )
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = vars(parser.parse_args())
    main(args)
