import unittest

from SiteScripts.HTMLBookParser import *


class TestHTMLParser(unittest.TestCase):

    def setUp(self):
        self.html_lines = [
            "<html>",
            "<head><title>Test Page</title></head>",
            "<body>",
            "<p>Welcome to the test page.</p>",
            "<p>This is a test paragraph.</p>",
            "<p>Another paragraph for testing.</p>",
            "</body>",
            "</html>"
        ]

    def test_find_line_of_value(self):
        # Test to find a value that exists
        index = find_line_of_value(self.html_lines, "<body>")
        self.assertEqual(index, 2)

        # Test to find a value that does not exist
        index = find_line_of_value(self.html_lines, "<footer>")
        self.assertEqual(index, -1)

    def test_find_all_lines_of_value(self):
        # Test to find multiple lines containing 'paragraph'
        indices = find_all_lines_of_value(self.html_lines, "paragraph")
        self.assertEqual(indices, [4, 5])

        # Test to find a value that does not exist
        indices = find_all_lines_of_value(self.html_lines, "nonexistent")
        self.assertEqual(indices, [])


if __name__ == '__main__':
    unittest.main()
