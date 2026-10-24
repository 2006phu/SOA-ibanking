#!/bin/bash
# ==============================================================================
# iBanking TDTU — 1-Click Launcher for macOS & Linux
# Double-click this file in macOS Finder to launch the whole system!
# ==============================================================================

# Ensure working directory is the project root
cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}       🏛️  iBANKING TDTU - HỆ THỐNG THANH TOÁN HỌC PHÍ MICROSERVICES         ${NC}"
echo -e "${BLUE}==============================================================================${NC}\n"

# 1. Check .env file
echo -e "${YELLOW}[1/5] Kiểm tra cấu hình môi trường (.env)...${NC}"
if [ ! -f ".env" ]; then
    echo "    -- Chưa tìm thấy file .env, đang tự động tạo từ .env.example..."
    cp .env.example .env
    echo "    -- Đã tạo file .env thành công!"
else
    echo "    -- File .env đã sẵn sàng."
fi
echo ""

# 2. Check Docker
echo -e "${YELLOW}[2/5] Kiểm tra Docker Daemon...${NC}"
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ [LỖI] Docker chưa được khởi động hoặc chưa cài đặt!${NC}"
    echo "   Vui lòng mở ứng dụng Docker Desktop trên máy rồi chạy lại file này."
    read -p "Nhấn Enter để thoát..."
    exit 1
fi
echo -e "${GREEN}    -- Docker đang hoạt động tốt.${NC}\n"

# 3. Docker Compose Build & Up
echo -e "${YELLOW}[3/5] Đang build và khởi động tất cả Microservices, Gateway, DB và RabbitMQ...${NC}"
echo "    (Quá trình này có thể mất 1-2 phút trong lần chạy đầu tiên)"
echo ""
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

$DOCKER_COMPOSE up --build -d
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ [LỖI] Khởi động Docker Compose thất bại.${NC}"
    read -p "Nhấn Enter để thoát..."
    exit 1
fi
echo ""

# 4. Wait for Gateway Health
echo -e "${YELLOW}[4/5] Chờ hệ thống khởi động hoàn tất (Health Check)...${NC}"
max_retries=30
count=0
while [ $count -lt $max_retries ]; do
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}    -- API Gateway và các Microservices đã sẵn sàng!${NC}"
        break
    fi
    count=$((count+1))
    echo -n "."
    sleep 2
done
echo ""

# 5. Seed initial data
echo -e "${YELLOW}[5/5] Tự động nạp dữ liệu mẫu sinh viên và học phí (Seed Data)...${NC}"
$DOCKER_COMPOSE cp scripts/seed_data.py payment-service:/app/seed_data.py >/dev/null 2>&1
$DOCKER_COMPOSE exec -T -e GATEWAY_URL=http://gateway:8000/api payment-service python /app/seed_data.py
echo -e "${GREEN}    -- Dữ liệu mẫu đã được nạp thành công!${NC}\n"

# 6. Done & Open Browser
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}🎉 HỆ THỐNG ĐÃ SẴN SÀNG! ĐANG MỞ TRÌNH DUYỆT...                               ${NC}"
echo -e "${GREEN}==============================================================================${NC}\n"
echo " 🌐 Giao diện Web:      http://localhost:3000"
echo " 📖 Swagger API Docs:   http://localhost:8000/docs"
echo " 🐰 RabbitMQ Panel:     http://localhost:15672 (user: ibanking / pass: rabbitmq_secret_2026)"
echo ""
echo " ⚡ Tài khoản dùng thử (Đã có sẵn nút bấm tự điền trên giao diện):"
echo "    1. student1  / password123 (Số dư: 15.000.000 ₫)"
echo "    2. parent1   / password123 (Số dư: 25.000.000 ₫)"
echo "    3. rich_user / password123 (Số dư: 100.000.000 ₫)"
echo -e "\n=============================================================================="

# Open browser on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000
    open http://localhost:8000/docs
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:3000 >/dev/null 2>&1 &
    xdg-open http://localhost:8000/docs >/dev/null 2>&1 &
fi

echo -e "\nĐể dừng hệ thống khi không dùng nữa, chạy lệnh: docker compose down"
echo ""
read -p "Nhấn Enter để đóng cửa sổ này..."
