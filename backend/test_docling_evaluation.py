"""
Docling PDF Parser Evaluation Script

Evaluates Docling parsing quality compared to legacy parser.

Author: C2
Date: 2026-03-06
"""

import sys
from pathlib import Path
from pprint import pprint

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.document_parser.factory import ParserFactory, get_parser
from app.document_parser.models import ContentType
from app.document_parser.docling_pdf_parser import DOCLING_AVAILABLE


def evaluate_pdf(file_path: Path):
    """Evaluate both parsers on the same PDF file.

    Args:
        file_path: Path to the PDF file to evaluate
    """
    print(f"\n{'='*60}")
    print(f"Evaluating: {file_path.name}")
    print(f"{'='*60}\n")

    # Check Docling availability
    print(f"Docling available: {DOCLING_AVAILABLE}")
    print()

    # Test 1: Docling parser (if available)
    if DOCLING_AVAILABLE:
        print("-" * 60)
        print("1. Docling Parser Results")
        print("-" * 60)
        try:
            docling_parser = get_parser(str(file_path))
            docling_result = docling_parser.parse(file_path)

            print(f"\nTotal items parsed: {len(docling_result)}")
            print(f"Parser type: {type(docling_parser).__name__}")

            # Group by content type
            type_counts = {}
            for item in docling_result:
                type_name = item.content_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

            print("\nContent type distribution:")
            for content_type, count in sorted(type_counts.items()):
                print(f"  {content_type}: {count}")

            # Show first few items
            print("\nFirst 5 parsed items:")
            for i, item in enumerate(docling_result[:5], 1):
                print(f"\n  [{i}] Type: {item.content_type.value}")
                print(f"      Page: {item.page_number}")
                text_preview = item.text[:100] + "..." if len(item.text) > 100 else item.text
                print(f"      Text: {text_preview}")
                if item.metadata:
                    print(f"      Metadata: {list(item.metadata.keys())}")

            # Check for specific content types
            has_table = any(c.content_type == ContentType.TABLE for c in docling_result)
            has_image = any(c.content_type == ContentType.IMAGE for c in docling_result)
            has_equation = any(c.content_type == ContentType.EQUATION for c in docling_result)

            print(f"\nSpecial content detected:")
            print(f"  Tables: {has_table}")
            print(f"  Images: {has_image}")
            print(f"  Equations: {has_equation}")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

    else:
        print("Docling not installed. Install with: pip install docling\n")

    # Test 2: Legacy parser
    print("\n" + "-" * 60)
    print("2. Legacy Parser Results")
    print("-" * 60)
    try:
        from app.document_parser.pdf_parser import PdfDocumentParser

        legacy_parser = PdfDocumentParser()
        legacy_result = legacy_parser.parse(file_path)

        print(f"\nTotal items parsed: {len(legacy_result)}")
        print(f"Parser type: {type(legacy_parser).__name__}")

        # Show first few items
        print("\nFirst 5 parsed items:")
        for i, item in enumerate(legacy_result[:5], 1):
            print(f"\n  [{i}] Type: {item.content_type.value}")
            print(f"      Page: {item.page_number}")
            text_preview = item.text[:100] + "..." if len(item.text) > 100 else item.text
            print(f"      Text: {text_preview}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Comparison summary
    if DOCLING_AVAILABLE:
        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)
        print(f"Docling items: {len(docling_result)}")
        print(f"Legacy items: {len(legacy_result)}")
        print(f"Difference: {len(docling_result) - len(legacy_result)} items")


def main():
    """Main evaluation function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate Docling PDF parser quality"
    )
    parser.add_argument(
        "pdf_file",
        nargs="?",
        help="Path to PDF file to evaluate (default: uses test fixture)"
    )
    parser.add_argument(
        "--use-fixture",
        action="store_true",
        help="Use test fixture PDF"
    )
    args = parser.parse_args()

    # Determine PDF path
    if args.pdf_file:
        pdf_path = Path(args.pdf_file)
    elif args.use_fixture or not args.pdf_file:
        # Use test fixture
        fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "test_normal.pdf"
        if fixture_path.exists():
            pdf_path = fixture_path
            print(f"Using test fixture: {pdf_path}")
        else:
            print(f"Test fixture not found: {fixture_path}")
            print("Please provide a PDF file path.")
            return 1

    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return 1

    # Run evaluation
    evaluate_pdf(pdf_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
