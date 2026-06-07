import unittest
import html
from kb_builder.pre_processor import marker_pdf
from bs4 import BeautifulSoup

class TestMarkerDecodeEntities(unittest.TestCase):
    """Test solutions for decoding HTML entities from Marker"""
    
    def test_decode_html_entities_solution(self):
        """Test different approaches to decode HTML entities"""
        
        # Example of what Marker returns
        marker_html = '<p>Peer-reviewed articles published to date&lt;sup&gt;2&lt;/sup&gt;</p>'
        
        # Solution 1: Use html.unescape() before processing
        decoded_html = html.unescape(marker_html)
        print(f"Original from Marker: {marker_html}")
        print(f"After html.unescape(): {decoded_html}")
        
        # Now strip_tags_except_li will work on actual tags
        result1 = marker_pdf.strip_tags_except_li(decoded_html)
        print(f"After strip_tags_except_li: {result1}")
        
        # Solution 2: Modify strip_tags_except_li to decode first
        def strip_tags_except_li_with_decode(html_string):
            # Decode HTML entities first
            decoded = html.unescape(html_string)
            # Then process as normal
            return marker_pdf.strip_tags_except_li(decoded)
        
        result2 = strip_tags_except_li_with_decode(marker_html)
        print(f"\nWith modified function: {result2}")
        
        # Solution 3: Keep <sup> tags in the tags_to_keep list
        def strip_tags_keep_formatting(html_string):
            decoded = html.unescape(html_string)
            soup = BeautifulSoup(decoded, 'html.parser')
            tags_to_keep = ['li', 'p', 'div', 'sup', 'sub']  # Added sup and sub
            
            for tag in soup.find_all(True):
                tag.attrs = {k:v for k, v in tag.attrs.items() if k == 'role' and v == 'img'}
                if tag.name not in tags_to_keep:
                    if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        tag.insert_after(soup.new_tag('br'))
                    tag.unwrap()
            return str(soup)
        
        result3 = strip_tags_keep_formatting(marker_html)
        print(f"\nKeeping sup tags: {result3}")
        
        # Verify the results
        self.assertIn("2", result1)  # Original strips the sup tags
        self.assertIn("2", result2)  # Modified also strips sup tags
        self.assertIn("<sup>2</sup>", result3)  # This preserves sup tags

if __name__ == '__main__':
    unittest.main() 