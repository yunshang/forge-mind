from unittest.mock import patch

from backend.utils.solc_detector import SolcDetector


class TestSolcDetector:
    @patch("backend.utils.solc_detector.shutil.which")
    @patch("backend.utils.solc_detector.Path.is_file")
    def test_find_solc_returns_existing_candidate(self, mock_is_file, mock_which):
        mock_which.return_value = "/usr/bin/solc"
        mock_is_file.side_effect = [False, True]

        result = SolcDetector.find_solc()

        assert result == "/usr/local/bin/solc"

    @patch("backend.utils.solc_detector.shutil.which")
    @patch("backend.utils.solc_detector.Path.is_file")
    def test_find_solc_returns_none_when_missing(self, mock_is_file, mock_which):
        mock_which.return_value = None
        mock_is_file.return_value = False

        result = SolcDetector.find_solc()

        assert result is None

    def test_get_install_instructions_returns_non_empty_string(self):
        result = SolcDetector.get_install_instructions()

        assert isinstance(result, str)
        assert result
        assert "Foundry" in result
