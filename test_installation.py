"""
Simple test script to verify the web scraping pipeline is working correctly.
Run this after installing dependencies to make sure everything is set up properly.
"""

import sys


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import requests
        import bs4
        import lxml
        import trafilatura
        import readability
        import html2text
        import langdetect
        import nltk
        import tiktoken
        from fake_useragent import UserAgent
        
        print("  ✓ All dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def test_nltk_data():
    """Test that NLTK data is available."""
    print("\nTesting NLTK data...")
    
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        print("  ✓ NLTK punkt tokenizer found")
        return True
    except LookupError:
        print("  ✗ NLTK punkt tokenizer not found")
        print("\nPlease download NLTK data:")
        print("  python -c \"import nltk; nltk.download('punkt')\"")
        return False


def test_scraper_modules():
    """Test that our scraper modules can be imported."""
    print("\nTesting scraper modules...")
    
    try:
        from scraper.config import ScraperConfig
        from scraper.fetcher import ContentFetcher
        from scraper.parser import ContentParser
        from scraper.cleaner import ContentCleaner
        from scraper.chunker import ContentChunker
        from utils.exceptions import ScraperError
        from utils.validators import URLValidator
        from main import WebScraper
        
        print("  ✓ All scraper modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic scraper functionality."""
    print("\nTesting basic functionality...")
    
    try:
        from main import WebScraper
        from scraper.config import ScraperConfig
        
        # Create scraper
        config = ScraperConfig.create_default()
        scraper = WebScraper(config)
        
        print("  ✓ WebScraper created successfully")
        
        scraper.close()
        print("  ✓ WebScraper closed successfully")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_configuration():
    """Test configuration system."""
    print("\nTesting configuration...")
    
    try:
        from scraper.config import ScraperConfig
        
        # Test presets
        default = ScraperConfig.create_default()
        fast = ScraperConfig.create_fast()
        thorough = ScraperConfig.create_thorough()
        articles = ScraperConfig.create_for_articles()
        llm = ScraperConfig.create_for_llm()
        
        # Validate configurations
        default.validate()
        fast.validate()
        thorough.validate()
        articles.validate()
        llm.validate()
        
        print("  ✓ All configuration presets valid")
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def test_live_scraping():
    """Test actual web scraping (requires internet connection)."""
    print("\nTesting live scraping (this may take a moment)...")
    print("  Note: This requires an internet connection")
    
    try:
        from main import WebScraper
        
        # Use a reliable, simple page
        test_url = "https://en.wikipedia.org/wiki/Web_scraping"
        
        with WebScraper() as scraper:
            result = scraper.scrape(test_url, enable_chunking=False)
            
            # Verify result structure
            assert 'url' in result, "Missing 'url' in result"
            assert 'content' in result, "Missing 'content' in result"
            assert 'metadata' in result, "Missing 'metadata' in result"
            assert 'raw' in result['content'], "Missing 'raw' content"
            
            # Verify content was extracted
            content = result['content']['raw']
            assert len(content) > 100, "Content too short"
            
            print(f"  ✓ Successfully scraped {result['url']}")
            print(f"  ✓ Extracted {len(content)} characters")
            print(f"  ✓ Title: {result['metadata'].get('title', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"  ✗ Live scraping test failed: {e}")
        print("  Note: This test requires internet connection")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("WEB SCRAPING PIPELINE - INSTALLATION TEST")
    print("="*60)
    
    tests = [
        ("Import dependencies", test_imports),
        ("NLTK data", test_nltk_data),
        ("Scraper modules", test_scraper_modules),
        ("Basic functionality", test_basic_functionality),
        ("Configuration", test_configuration),
        ("Live scraping", test_live_scraping),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\nUnexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed")
    print("-"*60)
    
    if passed == total:
        print("\n🎉 All tests passed! The scraper is ready to use.")
        print("\nNext steps:")
        print("  1. Read QUICKSTART.md for usage examples")
        print("  2. Run: python examples.py")
        print("  3. Try: python main.py https://example.com")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Download NLTK data: python -c \"import nltk; nltk.download('punkt')\"")
        return 1


if __name__ == '__main__':
    sys.exit(main())
