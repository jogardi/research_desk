#!/usr/bin/env python3
"""
Script to recursively count pages in PDF files under a local directory.
Uses pdfplumber to extract page counts from PDFs.
"""

import os
import sys
from pathlib import Path
import pdfplumber
from typing import Dict, Tuple


def count_pdf_pages(pdf_path: str) -> int:
    """
    Count the number of pages in a PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Number of pages in the PDF, or 0 if there's an error
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return 0


def scan_directory_for_pdfs(directory: str) -> Dict[str, int]:
    """
    Recursively scan directory for PDF files and count their pages.
    
    Args:
        directory: Root directory to scan
        
    Returns:
        Dictionary mapping PDF file paths to their page counts
    """
    pdf_counts = {}
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Error: Directory {directory} does not exist")
        return pdf_counts
    
    print(f"Scanning directory: {directory}")
    
    # Recursively find all PDF files
    for pdf_file in directory_path.rglob("*.pdf"):
        if pdf_file.is_file():
            print(f"Processing: {pdf_file}")
            page_count = count_pdf_pages(str(pdf_file))
            pdf_counts[str(pdf_file)] = page_count
            print(f"  → {page_count} pages")
    
    return pdf_counts


def print_summary(pdf_counts: Dict[str, int]) -> None:
    """
    Print a summary of the PDF page counts.
    
    Args:
        pdf_counts: Dictionary mapping PDF paths to page counts
    """
    if not pdf_counts:
        print("No PDF files found.")
        return
    
    total_pdfs = len(pdf_counts)
    total_pages = sum(pdf_counts.values())
    successful_pdfs = sum(1 for count in pdf_counts.values() if count > 0)
    failed_pdfs = total_pdfs - successful_pdfs
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total PDF files found: {total_pdfs}")
    print(f"Successfully processed: {successful_pdfs}")
    print(f"Failed to process: {failed_pdfs}")
    print(f"Total pages across all PDFs: {total_pages:,}")
    
    if successful_pdfs > 0:
        avg_pages = total_pages / successful_pdfs
        print(f"Average pages per PDF: {avg_pages:.1f}")
    
    # Show top 10 largest PDFs
    if pdf_counts:
        print("\nTop 10 largest PDFs:")
        sorted_pdfs = sorted(pdf_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (pdf_path, page_count) in enumerate(sorted_pdfs[:10], 1):
            filename = Path(pdf_path).name
            print(f"  {i:2d}. {filename}: {page_count:,} pages")


def main():
    """Main function to run the PDF page counting script."""
    fda_directory = os.getenv("PDF_DIRECTORY", ".")
    
    print("PDF Page Counter")
    print("="*60)
    print(f"Target directory: {fda_directory}")
    
    # Check if directory exists
    if not os.path.exists(fda_directory):
        print(f"Error: Directory '{fda_directory}' does not exist.")
        sys.exit(1)
    
    # Scan for PDFs and count pages
    pdf_counts = scan_directory_for_pdfs(fda_directory)
    
    # Print summary
    print_summary(pdf_counts)
    
    # Optionally save results to a file
    output_file = "pdf_page_counts.txt"
    try:
        with open(output_file, 'w') as f:
            f.write("PDF Page Count Report\n")
            f.write("="*60 + "\n")
            f.write(f"Directory scanned: {fda_directory}\n\n")
            
            for pdf_path, page_count in sorted(pdf_counts.items()):
                f.write(f"{pdf_path}: {page_count} pages\n")
            
            f.write(f"\nTotal PDFs: {len(pdf_counts)}\n")
            f.write(f"Total Pages: {sum(pdf_counts.values()):,}\n")
        
        print(f"\nDetailed results saved to: {output_file}")
    except Exception as e:
        print(f"Warning: Could not save results to file: {e}")


if __name__ == "__main__":
    main() 
