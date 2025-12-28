#!/bin/bash

echo "=========================================="
echo "  📋 ECOWAS Summit TWG System Logs"
echo "=========================================="
echo ""

if [ -z "$1" ]; then
    echo "Showing logs for ALL services (use Ctrl+C to exit)"
    echo "Tip: Use './docker-logs.sh <service>' to view specific service"
    echo "Available services: postgres, redis, backend, frontend, celery_worker, celery_beat"
    echo ""
    docker-compose logs -f
else
    echo "Showing logs for: $1"
    echo ""
    docker-compose logs -f $1
fi
