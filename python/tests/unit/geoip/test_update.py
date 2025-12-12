import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from sof_elk.geoip.update import GeoIPUpdater

class TestGeoIPUpdate(unittest.TestCase):
    @patch('sof_elk.api.client.SOFElkSession.get_session')
    @patch('sof_elk.geoip.update.GeoIPUpdater._parse_config')
    @patch('subprocess.run')
    def test_update(self, mock_subprocess, mock_parse_config, mock_session):
        mock_parse_config.return_value = True
        
        updater = GeoIPUpdater()
        updater.databases = ["GeoLite2-City", "GeoLite2-ASN"]
        updater.update()
        
        # Should call subprocess
        mock_subprocess.assert_called()
        args, _ = mock_subprocess.call_args
        self.assertEqual(args[0][0], "geoipupdate")

if __name__ == '__main__':
    unittest.main()
