#!/bin/bash

echo "=========================================="
echo "  🧹 Cleaning Docker Resources"
echo "=========================================="
echo ""

echo "⚠️  WARNING: This will:"
echo "  - Stop all containers"
echo "  - Remove all containers"
echo "  - Remove all volumes (INCLUDING DATABASE DATA)"
echo "  - Clean up unused Docker resources"
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🗑️  Stopping and removing containers with volumes..."
    docker-compose down -v

    echo ""
    echo "🧹 Cleaning up Docker system..."
    docker system prune -f

    echo ""
    echo "✅ Cleanup complete!"
    echo ""
    echo "📝 Note: Database data has been removed."
    echo "   Run './docker-start.sh' to start fresh."
else
    echo ""
    echo "❌ Cleanup cancelled"
fi

echo ""
