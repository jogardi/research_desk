import unittest
import html
from kb_builder.pre_processor import marker_pdf
from bs4 import BeautifulSoup

class TestMarkerLiteralHtmlEdgeCases(unittest.TestCase):
    """Test edge cases where PDFs contain literal HTML-like text"""
    
    def test_literal_html_entities_in_pdf(self):
        """Test what happens when a PDF literally contains &lt;sup&gt;2&lt;/sup&gt;"""
        
        # Scenario 1: PDF literally shows "&lt;sup&gt;2&lt;/sup&gt;" as visible text
        # Marker would need to double-escape this to preserve it
        marker_response_literal_entities = '<p>The formula is x&amp;lt;sup&amp;gt;2&amp;lt;/sup&amp;gt; + y</p>'
        
        print("=== Scenario 1: PDF contains literal '&lt;sup&gt;2&lt;/sup&gt;' ===")
        print(f"Marker returns (double-escaped): {marker_response_literal_entities}")
        
        # Decode once
        decoded_once = html.unescape(marker_response_literal_entities)
        print(f"After one unescape: {decoded_once}")
        
        # Process with strip_tags
        result1 = marker_pdf.strip_tags_except_li(decoded_once)
        print(f"After strip_tags: {result1}")
        print()
        
        # Scenario 2: PDF literally shows "<sup>2</sup>" as visible text
        # Marker would escape this to preserve it as literal text
        marker_response_literal_tags = '<p>The formula is x&lt;sup&gt;2&lt;/sup&gt; + y</p>'
        
        print("=== Scenario 2: PDF contains literal '<sup>2</sup>' ===")
        print(f"Marker returns (escaped): {marker_response_literal_tags}")
        
        # If we decode this...
        decoded = html.unescape(marker_response_literal_tags)
        print(f"After unescape: {decoded}")
        
        # And then strip tags...
        result2 = marker_pdf.strip_tags_except_li(decoded)
        print(f"After strip_tags: {result2}")
        print("WARNING: The literal '<sup>2</sup>' was stripped!")
        print()
        
        # Scenario 3: PDF has actual superscript formatting
        # Marker returns it as HTML entities (current behavior)
        marker_response_superscript = '<p>The formula is x&lt;sup&gt;2&lt;/sup&gt; + y</p>'
        
        print("=== Scenario 3: PDF has actual superscript 2 ===")
        print(f"Marker returns: {marker_response_superscript}")
        print("This is indistinguishable from Scenario 2!")
        print()
        
        # Test mixed content
        print("=== Scenario 4: Mixed content ===")
        # PDF might have: "Use <sup>2</sup> for x²"
        # Where <sup>2</sup> is literal text and ² is a superscript
        marker_mixed = '<p>Use &lt;sup&gt;2&lt;/sup&gt; for x&lt;sup&gt;2&lt;/sup&gt;</p>'
        print(f"Marker returns: {marker_mixed}")
        
        decoded_mixed = html.unescape(marker_mixed)
        print(f"After unescape: {decoded_mixed}")
        
        result_mixed = marker_pdf.strip_tags_except_li(decoded_mixed)
        print(f"After strip_tags: {result_mixed}")
        print("Both instances are treated the same!")
        
    def test_potential_solutions(self):
        """Test potential solutions to distinguish literal HTML from formatting"""
        
        print("\n=== Potential Solutions ===")
        
        # Solution 1: Don't decode - preserve everything as-is
        print("\n1. Keep entities as-is (current behavior):")
        text = '<p>Formula: x&lt;sup&gt;2&lt;/sup&gt; and literal &lt;sup&gt;2&lt;/sup&gt;</p>'
        result = marker_pdf.strip_tags_except_li(text)
        print(f"Result: {result}")
        print("Pro: Preserves literal text. Con: Formatting codes visible.")
        
        # Solution 2: Selective decoding based on context
        print("\n2. Trust Marker's encoding:")
        print("- Single-encoded (&lt;) = formatting")
        print("- Double-encoded (&amp;lt;) = literal text")
        
        def smart_decode_and_strip(html_string):
            # First pass: decode double-encoded to single-encoded
            pass1 = html.unescape(html_string)
            # This converts &amp;lt; to &lt;
            
            # Now process, which will preserve &lt; as literal
            soup = BeautifulSoup(pass1, 'html.parser')
            
            # For this example, just return as-is to show the concept
            return str(soup)
        
        text_with_both = '<p>Superscript: x&lt;sup&gt;2&lt;/sup&gt; vs literal: &amp;lt;sup&amp;gt;2&amp;lt;/sup&amp;gt;</p>'
        print(f"\nInput: {text_with_both}")
        result = smart_decode_and_strip(text_with_both)
        print(f"After smart decode: {result}")
        
        # Solution 3: Keep formatting tags
        print("\n3. Preserve <sup> and <sub> tags:")
        def strip_but_keep_formatting(html_string):
            decoded = html.unescape(html_string)
            soup = BeautifulSoup(decoded, 'html.parser')
            tags_to_keep = ['li', 'p', 'div', 'sup', 'sub', 'b', 'i', 'strong', 'em']
            
            for tag in soup.find_all(True):
                if tag.name not in tags_to_keep:
                    tag.unwrap()
            return str(soup)
        
        text = '<p>Keep formatting: x&lt;sup&gt;2&lt;/sup&gt; + y&lt;sub&gt;1&lt;/sub&gt;</p>'
        decoded = html.unescape(text)
        result = strip_but_keep_formatting(text)
        print(f"Result: {result}")
        print("Pro: Preserves formatting. Con: Might keep unwanted tags.")

if __name__ == '__main__':
    unittest.main() 