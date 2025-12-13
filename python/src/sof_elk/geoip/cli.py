from .update import GeoIPUpdater


def register_subcommand(subparsers):
    parser = subparsers.add_parser("geoip", help="GeoIP Utilities")
    sub_subparsers = parser.add_subparsers(dest="geoip_command", required=True)

    update_parser = sub_subparsers.add_parser("update", help="Update GeoIP databases")
    update_parser.set_defaults(func=update_command)


def update_command(args):
    updater = GeoIPUpdater()
    updater.update()
