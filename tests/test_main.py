import unittest

from main import detect_input_type


class DetectInputTypeTests(unittest.TestCase):
    def test_detects_canonical_x_hostname(self):
        self.assertEqual(
            detect_input_type("https://x.com/alice/status/123456789012345"),
            "x_twitter",
        )

    def test_does_not_classify_spoofed_hostname_as_x(self):
        self.assertEqual(
            detect_input_type(
                "https://example.com/?next=https://x.com/alice/status/123456789012345"
            ),
            "url",
        )


if __name__ == "__main__":
    unittest.main()
