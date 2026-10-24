@echo off
chcp 65001 >nul
title iBanking TDTU - Khởi chạy Hệ Thống Microservices
color 0b

echo ==============================================================================
echo        🏛️  iBANKING TDTU - HỆ THỐNG THANH TOÁN HỌC PHÍ MICROSERVICES
echo ==============================================================================
echo.

cd /d "%~dp0"

:: 1. Kiểm tra file .env
echo [1/5] Kiểm tra cấu hình môi trường (.env)...
if not exist ".env" (
    echo     -- Chưa tìm thấy file .env, đang tự động tạo từ .env.example...
    copy ".env.example" ".env" >nul
    echo     -- Đã tạo file .env thành công!
) else (
    echo     -- File .env đã sẵn sàng.
)
echo.

:: 2. Kiểm tra Docker
echo [2/5] Kiểm tra Docker Daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ [LỖI] Docker chưa được khởi động hoặc chưa cài đặt!
    echo    Vui lòng bật ứng dụng Docker Desktop rồi click chạy lại file này.
    echo.
    pause
    exit /b 1
)
echo     -- Docker đang hoạt động tốt.
echo.

:: 3. Khởi chạy Docker Compose
echo [3/5] Đang build và khởi động tất cả 6 Microservices, Gateway, DB và RabbitMQ...
echo     (Quá trình này có thể mất 1-2 phút trong lần chạy đầu tiên)
echo.
docker compose up --build -d
if %errorlevel% neq 0 (
    echo.
    echo ❌ [LỖI] Khởi động Docker Compose thất bại.
    pause
    exit /b 1
)
echo.

:: 4. Chờ Gateway & Services sẵn sàng
echo [4/5] Chờ hệ thống khởi động hoàn tất (Health Check)...
set max_retries=30
set count=0

:health_loop
set /a count+=1
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo     -- API Gateway và các Microservices đã sẵn sàng!
    goto seed_data
)
if %count% geq %max_retries% (
    echo     -- Đã hết thời gian chờ, tiếp tục sang bước nạp dữ liệu...
    goto seed_data
)
<nul set /p=.
timeout /t 2 /nobreak >nul
goto health_loop

:seed_data
echo.
echo.
:: 5. Nạp dữ liệu mẫu
echo [5/5] Tự động nạp dữ liệu mẫu sinh viên và học phí (Seed Data)...
docker compose exec -T -e GATEWAY_URL=http://gateway:8000/api payment-service python -c "import os, sys; os.system('python /app/scripts/seed_data.py') if os.path.exists('/app/scripts/seed_data.py') else None" >nul 2>&1
:: Dự phòng nếu chưa mount scripts: copy trực tiếp vào container
docker compose cp scripts/seed_data.py payment-service:/app/seed_data.py >nul 2>&1
docker compose exec -T -e GATEWAY_URL=http://gateway:8000/api payment-service python /app/seed_data.py
echo     -- Dữ liệu mẫu đã được nạp thành công!
echo.

:: 6. Mở trình duyệt
echo ==============================================================================
echo 🎉 HỆ THỐNG ĐÃ SẴN SÀNG! ĐANG MỞ TRÌNH DUYỆT...
echo ==============================================================================
echo.
echo  🌐 Giao diện Web:      http://localhost:3000
echo  📖 Swagger API Docs:   http://localhost:8000/docs
echo  🐰 RabbitMQ Panel:     http://localhost:15672 (user: ibanking / pass: rabbitmq_secret_2026)
echo.
echo  ⚡ Tài khoản dùng thử (Đã có sẵn nút bấm tự điền trên giao diện):
echo     1. student1  / password123 (Số dư: 15.000.000 ₫)
echo     2. parent1   / password123 (Số dư: 25.000.000 ₫)
echo     3. rich_user / password123 (Số dư: 100.000.000 ₫)
echo.
echo ==============================================================================

start http://localhost:3000
start http://localhost:8000/docs

echo Để dừng hệ thống khi không dùng nữa, chạy lệnh: docker compose down
echo.
pause
