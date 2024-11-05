#!/bin/bash

# 确保在正确的目录
cd "$(dirname "$0")"

# 检查命令
case "$1" in
"start")
    echo "Starting face detection service..."
    docker-compose up -d
    ;;
"stop")
    echo "Stopping face detection service..."
    docker-compose down
    ;;
"restart")
    echo "Restarting face detection service..."
    docker-compose restart
    ;;
"logs")
    echo "Showing logs..."
    docker-compose logs -f
    ;;
"build")
    echo "Building service..."
    docker-compose build
    ;;
*)
    echo "Usage: $0 {start|stop|restart|logs|build}"
    exit 1
    ;;
esac
