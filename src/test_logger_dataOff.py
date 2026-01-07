import sys
import os
# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import log_experiment, ActionType

def test_logger_normal():
    """Test 1: Normal log (should work)"""
    print("🧪 Test 1: Normal log with all fields...")
    try:
        log_experiment(
            agent_name="DataOfficer_Test",
            model_used="gemini-2.5-flash",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "Logger test by Data Officer",
                "output_response": "✅ Logger functional",
                "note": "Initial test successful"
            },
            status="SUCCESS"
        )
        print("✅ Test 1 SUCCESS: Normal log recorded")
        return True
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False

def test_logger_missing_prompt():
    """Test 2: Without input_prompt (should fail)"""
    print("\n🧪 Test 2: Log WITHOUT input_prompt...")
    try:
        log_experiment(
            agent_name="DataOfficer_Test",
            model_used="gemini-2.5-flash",
            action=ActionType.FIX,  # Critical action
            details={
                "output_response": "I fixed the bug",  # ❌ MISSING input_prompt!
                "file": "bug.py"
            },
            status="SUCCESS"
        )
        print("❌ Test 2: SHOULD FAIL but succeeded!")
        return False
    except ValueError as e:
        print(f"✅ Test 2 SUCCESS: Error detected as expected")
        print(f"   Error message: {e}")
        return True

def test_logger_missing_response():
    """Test 3: Without output_response (should fail)"""
    print("\n🧪 Test 3: Log WITHOUT output_response...")
    try:
        log_experiment(
            agent_name="DataOfficer_Test",
            model_used="gemini-2.5-flash",
            action=ActionType.GENERATION,
            details={
                "input_prompt": "Generate a unit test",  # ❌ MISSING output_response!
                "file": "test.py"
            },
            status="SUCCESS"
        )
        print("❌ Test 3: SHOULD FAIL but succeeded!")
        return False
    except ValueError as e:
        print(f"✅ Test 3 SUCCESS: Error detected as expected")
        print(f"   Error message: {e}")
        return True

def test_different_actions():
    """Test 4: All action types"""
    print("\n🧪 Test 4: All action types...")
    actions = [
        (ActionType.ANALYSIS, "Analyzing code"),
        (ActionType.GENERATION, "Generating tests"),
        (ActionType.DEBUG, "Debugging an error"),
        (ActionType.FIX, "Fixing a bug")
    ]
    
    success_count = 0
    for action_type, description in actions:
        try:
            log_experiment(
                agent_name="DataOfficer_Test",
                model_used="gemini-2.5-flash",
                action=action_type,
                details={
                    "input_prompt": f"Test {description}",
                    "output_response": f"Response for {description}",
                    "test_note": f"Test of {action_type.value}"
                },
                status="SUCCESS"
            )
            print(f"✅ {action_type.value}: OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {action_type.value}: Failed - {e}")
    
    return success_count == len(actions)

def main():
    """Main function"""
    print("=" * 60)
    print("🧪 LOGGER TESTS - Data Officer")
    print("=" * 60)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run tests
    results = []
    
    results.append(test_logger_normal())
    results.append(test_logger_missing_prompt())
    results.append(test_logger_missing_response())
    results.append(test_different_actions())
    
    # Display summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("📁 Check the file: logs/experiment_data.json")
        
        # Show file preview
        try:
            import json
            with open("logs/experiment_data.json", "r") as f:
                data = json.load(f)
            print(f"\n📝 Preview: {len(data)} log entries")
            for i, entry in enumerate(data[-3:]):  # Last 3 entries
                print(f"  {i+1}. {entry['agent']} - {entry['action']}")
        except:
            print("⚠️ Unable to read log file")
        
        return 0  # Success code
    else:
        print("❌ Some tests failed. Check the logger.")
        return 1  # Error code

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)