#!/usr/bin/env python3
"""
Quick test script for MCP tools
"""
import asyncio
from database_tools import list_tables_tool, describe_table_tool, execute_sql_tool

async def test_tools():
    print("🔧 Testing MCP Tools...\n")
    
    # Test 1: List tables
    print("1️⃣ Testing list_tables_tool...")
    try:
        result = await list_tables_tool._arun()
        print(f"✅ Status: {result.get('status')}")
        if result.get('status') == 'success':
            tables = result.get('tables', [])
            print(f"📊 Found {len(tables)} tables:")
            for table_name, description in tables[:3]:  # Show first 3
                print(f"   - {table_name}: {description}")
            if len(tables) > 3:
                print(f"   ... and {len(tables) - 3} more")
        else:
            print(f"❌ Error: {result.get('message')}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Describe a table (if we found any)
    print("2️⃣ Testing describe_table_tool...")
    try:
        # First get a table name
        tables_result = await list_tables_tool._arun()
        if tables_result.get('status') == 'success' and tables_result.get('tables'):
            table_name = tables_result['tables'][0][0]  # First table name
            print(f"📋 Describing table: {table_name}")
            
            result = await describe_table_tool._arun(table_name=table_name)
            print(f"✅ Status: {result.get('status')}")
            
            if result.get('status') == 'success':
                columns = result.get('data', [])
                print(f"📊 Found {len(columns)} columns:")
                for col in columns[:5]:  # Show first 5 columns
                    col_name = col.get('COLUMN_NAME', 'Unknown')
                    col_type = col.get('DATA_TYPE', 'Unknown')
                    print(f"   - {col_name}: {col_type}")
                if len(columns) > 5:
                    print(f"   ... and {len(columns) - 5} more columns")
            else:
                print(f"❌ Error: {result.get('message')}")
        else:
            print("⚠️ No tables found to describe")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Execute a simple SQL query
    print("3️⃣ Testing execute_sql_tool...")
    try:
        # Try a simple query that should work on most databases
        simple_queries = [
            "SELECT 1 as test_column",
            "SELECT COUNT(*) as total_tables FROM information_schema.tables",
            "SHOW TABLES"  # MySQL/MariaDB
        ]
        
        for query in simple_queries:
            print(f"🔍 Trying query: {query}")
            result = await execute_sql_tool._arun(query=query)
            
            if result.get('status') == 'success':
                print(f"✅ Query succeeded!")
                data = result.get('data', [])
                if data:
                    print(f"📊 Returned {len(data)} rows:")
                    print(f"   First row: {data[0]}")
                break
            else:
                print(f"⚠️ Query failed: {result.get('message')}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run the tests"""
    print("🚀 Starting MCP Tools Test\n")
    asyncio.run(test_tools())
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()