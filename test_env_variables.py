#!/usr/bin/env python3
"""
Test Environment Variables
Verify that all required environment variables are set correctly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    print("=" * 50)
    
    # Required variables
    required_vars = {
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_ANON_KEY': 'Supabase anonymous key',
        'SUPABASE_SERVICE_ROLE_KEY': 'Supabase service role key',
        'DATABASE_URL': 'Database connection string',
        'OPENAI_API_KEY': 'OpenAI API key'
    }
    
    all_good = True
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask the value for security
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var_name}: {masked_value}")
        else:
            print(f"❌ {var_name}: MISSING")
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 All environment variables are set correctly!")
        print("✅ You can now run the pipeline scripts")
    else:
        print("❌ Some environment variables are missing")
        print("📝 Please check your .env file and ensure all variables are set")
    
    return all_good

if __name__ == "__main__":
    test_environment_variables()
