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
        self.chapter_divisions = [1, 5, 333, 555, 559, 777, 888, 2222, 4444, 4450, 5555, 6666]
        self.toc_lines = [50, 52, 54, 56, 58, 89, 90, 91, 92, 93, 94]

    def test_find_line_of_value_found(self):
        # Test to find a value that exists
        index = find_line_of_value(self.html_lines, "<body>")
        self.assertEqual(index, 2)

    def test_find_line_of_value_unfound(self):
        # Test to find a value that does not exist
        index = find_line_of_value(self.html_lines, "<footer>")
        self.assertEqual(index, -1)

    def test_find_all_lines_of_value_found(self):
        # Test to find multiple lines containing 'paragraph'
        indices = find_all_lines_of_value(self.html_lines, "paragraph")
        self.assertEqual(indices, [4, 5])

    def test_find_all_lines_of_value_unfound(self):
        # Test to find a value that does not exist
        indices = find_all_lines_of_value(self.html_lines, "nonexistent")
        self.assertEqual(indices, [])

    def test_get_section_indices_found(self):
        # Test to find sections based on lines and return their indices
        indices = get_section_indices(self.chapter_divisions)
        self.assertEqual(indices, [0, 3, 8])

    def test_get_section_indices_unfound(self):
        # Test to find sections based on lines and return their indices, none expected
        indices = get_section_indices([111, 333, 555, 777, 888, 2222, 4444])
        self.assertEqual(indices, [])

    def test_revise_toc_lines_change(self):
        # Test to revise toc indexes if needed
        toc_lines = revise_toc_lines(self.toc_lines)
        self.assertEqual(toc_lines, [50, 52, 54, 56, 58])

    def test_revise_toc_lines_no_change(self):
        # Test to revise toc indexes if needed, no revision expected
        toc_lines = revise_toc_lines([61, 62, 63, 64, 65])
        self.assertEqual(toc_lines, [61, 62, 63, 64, 65])


if __name__ == '__main__':
    unittest.main()
