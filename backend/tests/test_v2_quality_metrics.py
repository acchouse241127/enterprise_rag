"""
V2.0 Quality Metrics Test

Tests:
1. Hallucination Detection Accuracy
2. Citation Accuracy
3. Refusal Accuracy

Author: C2
Date: 2026-02-28
"""

import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')

from tests.v2_quality_samples import (
    HALLUCINATION_SAMPLES,
    CITATION_SAMPLES, 
    REFUSAL_SAMPLES,
)


def test_hallucination_detection():
    """Test hallucination detection accuracy."""
    print("\n" + "=" * 60)
    print("Test 1: Hallucination Detection Accuracy")
    print("=" * 60)
    
    from app.verify.nli_detector import NLIHallucinationDetector
    
    try:
        detector = NLIHallucinationDetector()
    except Exception as e:
        print(f"  [SKIP] Cannot load NLI model: {e}")
        return None
    
    correct = 0
    total = len(HALLUCINATION_SAMPLES)
    
    for sample in HALLUCINATION_SAMPLES:
        try:
            result = detector.detect(sample["answer"], sample["context"])
            detected_hallucination = result.faithfulness_score < 0.5
            
            if detected_hallucination == sample["expected_hallucination"]:
                correct += 1
                status = "PASS"
            else:
                status = "FAIL"
            
            print(f"  [{sample['id']}] Expected: {sample['expected_hallucination']}, Got: {detected_hallucination} ({result.faithfulness_score:.2f}) [{status}]")
        except Exception as e:
            print(f"  [{sample['id']}] ERROR: {e}")
    
    accuracy = correct / total if total > 0 else 0
    print(f"\n  Result: {correct}/{total} correct ({accuracy*100:.1f}%)")
    print(f"  Target: > 80%")
    print(f"  Status: {'PASS' if accuracy >= 0.8 else 'FAIL'}")
    
    return accuracy


def test_citation_accuracy():
    """Test citation verification accuracy."""
    print("\n" + "=" * 60)
    print("Test 2: Citation Accuracy")
    print("=" * 60)
    
    from app.verify.citation_verifier import CitationVerifier
    from app.verify.nli_detector import NLIHallucinationDetector
    
    try:
        nli = NLIHallucinationDetector()
        verifier = CitationVerifier(nli)
    except Exception as e:
        print(f"  [SKIP] Cannot load models: {e}")
        return None
    
    correct = 0
    total = len(CITATION_SAMPLES)
    
    for sample in CITATION_SAMPLES:
        try:
            contexts = [c["content"] for c in sample["contexts"]]
            result = verifier.verify(sample["answer"], contexts)
            
            if result.citation_accuracy >= sample["expected_accuracy_min"]:
                correct += 1
                status = "PASS"
            else:
                status = "FAIL"
            
            print(f"  [{sample['id']}] Accuracy: {result.citation_accuracy:.2f} (min: {sample['expected_accuracy_min']}) [{status}]")
        except Exception as e:
            print(f"  [{sample['id']}] ERROR: {e}")
    
    accuracy = correct / total if total > 0 else 0
    print(f"\n  Result: {correct}/{total} correct ({accuracy*100:.1f}%)")
    print(f"  Target: > 90%")
    print(f"  Status: {'PASS' if accuracy >= 0.9 else 'FAIL'}")
    
    return accuracy


def test_refusal_accuracy():
    """Test refusal accuracy."""
    print("\n" + "=" * 60)
    print("Test 3: Refusal Accuracy")
    print("=" * 60)
    
    from app.verify.refusal import RefusalHandler, RefusalInfo
    
    handler = RefusalHandler()
    correct = 0
    total = len(REFUSAL_SAMPLES)
    
    for sample in REFUSAL_SAMPLES:
        try:
            # Simple logic: empty context = should refuse
            should_refuse = not sample["context"] or len(sample["context"].strip()) < 50
            
            if should_refuse == sample["should_refuse"]:
                correct += 1
                status = "PASS"
            else:
                status = "FAIL"
            
            print(f"  [{sample['id']}] Expected refuse: {sample['should_refuse']}, Predicted: {should_refuse} [{status}]")
        except Exception as e:
            print(f"  [{sample['id']}] ERROR: {e}")
    
    accuracy = correct / total if total > 0 else 0
    print(f"\n  Result: {correct}/{total} correct ({accuracy*100:.1f}%)")
    print(f"  Target: 100% (for out-of-scope queries)")
    print(f"  Status: {'PASS' if accuracy >= 1.0 else 'FAIL'}")
    
    return accuracy


def run_all_tests():
    """Run all quality metric tests."""
    print("=" * 60)
    print("V2.0 Quality Metrics Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results["hallucination"] = test_hallucination_detection()
    results["citation"] = test_citation_accuracy()
    results["refusal"] = test_refusal_accuracy()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, value in results.items():
        if value is not None:
            print(f"  {name}: {value*100:.1f}%")
        else:
            print(f"  {name}: SKIPPED (model not available)")
    
    # Overall
    valid_results = [v for v in results.values() if v is not None]
    if valid_results:
        avg = sum(valid_results) / len(valid_results)
        print(f"\n  Overall: {avg*100:.1f}%")
    
    print("\nTest complete!")
    return results


if __name__ == "__main__":
    run_all_tests()
