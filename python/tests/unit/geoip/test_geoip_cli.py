import unittest
from unittest.mock import patch, MagicMock
import argparse
from sof_elk.geoip.cli import register_subcommand, update_command

class TestGeoIPCLI(unittest.TestCase):
    def test_register_subcommand(self):
        parser = argparse.ArgumentParser()
        # The parent parser usually has add_subparsers called on it
        subparsers = parser.add_subparsers(dest="command")
        register_subcommand(subparsers)
        
        # Check if we can parse 'geoip'
        # 'geoip' subparser has required 'geoip_command' (e.g. 'update')
        args = parser.parse_args(['geoip', 'update'])
        self.assertEqual(args.command, 'geoip')
        self.assertEqual(args.geoip_command, 'update')
        self.assertEqual(args.func, update_command)

    @patch('sof_elk.geoip.cli.GeoIPUpdater')
    def test_update_command(self, MockUpdater):
        mock_instance = MockUpdater.return_value
        
        args = MagicMock()
        update_command(args)
        
        MockUpdater.assert_called_once()
        mock_instance.update.assert_called_once()

if __name__ == '__main__':
    unittest.main()
