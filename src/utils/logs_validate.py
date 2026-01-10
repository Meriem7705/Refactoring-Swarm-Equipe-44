#!/usr/bin/env python3
"""
    Log Validation Script - Data Officer
    Validate the logs/experiment_data.json file for correctness and completeness.
"""
import json
import os
import sys

def logs_validate():
    """Validate experiment_data.json file"""
    log_file = "../logs/experiment_data.json"
    
    print("🔍 LOG VALIDATION - Data Officer")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(log_file):
        print("❌ ERROR: File not found: logs/experiment_data.json")
        print("   Make sure the file exists in the logs/ directory")
        return False
    
    print(f"✅ File found: {log_file}")
    
    try:
        # Read and parse JSON
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Total entries: {len(data)}")
        
        # Validate that data is a list
        if not isinstance(data, list):
            print("❌ ERROR: JSON root must be a list (array)")
            return False
        
        if len(data) == 0:
            print("⚠️ WARNING: Log file is empty")
            print("   No logs have been recorded yet")
            return True  # Empty but valid
        
        # Define valid values
        VALID_ACTIONS = {"CODE_ANALYSIS", "CODE_GEN", "DEBUG", "FIX"}
        VALID_STATUSES = {"SUCCESS", "FAILURE"}
        
        print("\n📝 Validating each entry...")
        print("-" * 50)
        
        issues = []
        entry_count = 0
        
        for i, entry in enumerate(data):
            entry_count += 1
            print(f"\nEntry #{i+1}:")
            
            # 1. Check required fields
            required_fields = ["id", "timestamp", "agent", "model", "action", "details", "status"]
            missing_fields = []
            
            for field in required_fields:
                if field not in entry:
                    missing_fields.append(field)
            
            if missing_fields:
                issue_msg = f"  ❌ Missing fields: {missing_fields}"
                print(issue_msg)
                issues.append(f"Entry {i+1}: {issue_msg}")
                continue  # Skip further checks for this entry
            
            print(f"  ✅ All required fields present")
            
            # 2. Validate action type
            action = entry["action"]
            if action not in VALID_ACTIONS:
                issue_msg = f"  ❌ Invalid action: '{action}' (valid: {', '.join(VALID_ACTIONS)})"
                print(issue_msg)
                issues.append(f"Entry {i+1}: {issue_msg}")
            else:
                print(f"  ✅ Action: {action}")
            
            # 3. Validate status
            status = entry["status"]
            if status not in VALID_STATUSES:
                issue_msg = f"  ❌ Invalid status: '{status}' (valid: {', '.join(VALID_STATUSES)})"
                print(issue_msg)
                issues.append(f"Entry {i+1}: {issue_msg}")
            else:
                print(f"  ✅ Status: {status}")
            
            # 4. Validate details structure
            details = entry["details"]
            if not isinstance(details, dict):
                issue_msg = f"  ❌ 'details' must be a dictionary, got {type(details).__name__}"
                print(issue_msg)
                issues.append(f"Entry {i+1}: {issue_msg}")
                continue  # Skip prompt validation
            
            print(f"  ✅ Details is a dictionary")
            
            # 5. Validate input_prompt and output_response for critical actions
            if action in VALID_ACTIONS:
                missing_prompts = []
                
                if "input_prompt" not in details:
                    missing_prompts.append("input_prompt")
                else:
                    if not details["input_prompt"] or details["input_prompt"].strip() == "":
                        issue_msg = "  ❌ 'input_prompt' is empty"
                        print(issue_msg)
                        issues.append(f"Entry {i+1}: {issue_msg}")
                    else:
                        # Truncate for display
                        prompt_preview = details["input_prompt"][:50] + "..." if len(details["input_prompt"]) > 50 else details["input_prompt"]
                        print(f"  ✅ input_prompt: '{prompt_preview}'")
                
                if "output_response" not in details:
                    missing_prompts.append("output_response")
                else:
                    if not details["output_response"] or details["output_response"].strip() == "":
                        issue_msg = "  ❌ 'output_response' is empty"
                        print(issue_msg)
                        issues.append(f"Entry {i+1}: {issue_msg}")
                    else:
                        # Truncate for display
                        response_preview = details["output_response"][:50] + "..." if len(details["output_response"]) > 50 else details["output_response"]
                        print(f"  ✅ output_response: '{response_preview}'")
                
                if missing_prompts:
                    issue_msg = f"  ❌ Missing required prompt fields: {missing_prompts}"
                    print(issue_msg)
                    issues.append(f"Entry {i+1}: {issue_msg}")
            
            # 6. Validate timestamp format (basic check)
            timestamp = entry["timestamp"]
            if "T" not in timestamp or len(timestamp) < 10:
                print(f"  ⚠️  Warning: Timestamp format may be incorrect: {timestamp}")
            
            # 7. Validate UUID format (basic check)
            entry_id = entry["id"]
            if len(entry_id) != 36 or entry_id.count("-") != 4:
                print(f"  ⚠️  Warning: ID format may be incorrect: {entry_id}")
            else:
                print(f"  ✅ ID format looks valid")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        if issues:
            print(f"❌ VALIDATION FAILED")
            print(f"   Found {len(issues)} issue(s) in {entry_count} entries")
            print("\nIssues found:")
            for issue in issues:
                print(f"  • {issue}")
            
            print(f"\n⚠️  Recommendation:")
            print(f"   1. Fix the issues listed above")
            print(f"   2. Run validation again")
            print(f"   3. Make sure to use ActionType enum from logger.py")
            
            return False
        else:
            print(f"✅ VALIDATION SUCCESSFUL!")
            print(f"   All {entry_count} entries are valid")
            print(f"\n🎯 Log file is ready for submission!")
            print(f"   This ensures 30% of the 'Data Quality' grade")
            
            # Additional statistics
            actions_count = {}
            agents_count = {}
            status_count = {}
            
            for entry in data:
                action = entry["action"]
                agent = entry["agent"]
                status = entry["status"]
                
                actions_count[action] = actions_count.get(action, 0) + 1
                agents_count[agent] = agents_count.get(agent, 0) + 1
                status_count[status] = status_count.get(status, 0) + 1
            
            print(f"\n📈 Statistics:")
            print(f"  Actions distribution:")
            for action, count in actions_count.items():
                print(f"    • {action}: {count}")
            
            print(f"  Agents distribution:")
            for agent, count in agents_count.items():
                print(f"    • {agent}: {count}")
            
            print(f"  Status distribution:")
            for status, count in status_count.items():
                print(f"    • {status}: {count}")
            
            return True
            
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON format")
        print(f"   Details: {e}")
        print(f"\n💡 Tip: Check for missing commas, brackets, or quotes")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error")
        print(f"   Details: {e}")
        return False

""""
def main():
    #Main function
    # Check if logs directory exists
    if not os.path.exists("logs"):
        print("❌ ERROR: 'logs' directory not found")
        print("   Create it with: mkdir logs")
        return 1
    
    success = validate_logs()
    
    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
"""
    
if __name__ == "__main__":
    if logs_validate():
        exit(0)  # Succès
    else:
        exit(1)  # Échec