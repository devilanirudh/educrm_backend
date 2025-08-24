#!/bin/bash

# Script to copy local database to deployment
# This script helps preserve your local data when deploying

echo "🚀 Preparing to copy local database to deployment..."

# Check if local database exists
if [ ! -f "eschool.db" ]; then
    echo "❌ Local database file 'eschool.db' not found!"
    echo "   Make sure you're running this script from the backend directory"
    exit 1
fi

# Check database size
DB_SIZE=$(du -h eschool.db | cut -f1)
echo "📊 Local database size: $DB_SIZE"

# Create backup
echo "💾 Creating backup of local database..."
cp eschool.db eschool.db.backup
echo "✅ Backup created: eschool.db.backup"

# Check if database is valid
echo "🔍 Validating database file..."
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('eschool.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
    tables = cursor.fetchall()
    print(f'✅ Database is valid. Found {len(tables)} tables:')
    for table in tables[:5]:  # Show first 5 tables
        print(f'   - {table[0]}')
    if len(tables) > 5:
        print(f'   ... and {len(tables) - 5} more tables')
    conn.close()
except Exception as e:
    print(f'❌ Database validation failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database validation failed. Please check your database file."
    exit 1
fi

echo ""
echo "✅ Local database is ready for deployment!"
echo ""
echo "📋 Next steps:"
echo "1. Commit your changes: git add . && git commit -m 'Include local database'"
echo "2. Push to your repository: git push"
echo "3. Deploy to Railway (or your platform)"
echo ""
echo "⚠️  Important notes:"
echo "- The database will be included in your Docker image"
echo "- This will increase your deployment size"
echo "- Make sure your database doesn't contain sensitive data"
echo "- Consider using a proper database service for production"
