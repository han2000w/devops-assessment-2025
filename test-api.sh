#!/bin/bash

echo "=== 스팬딧 영수증 API 테스트 ==="
echo ""

# 1. 헬스체크
echo "1. 헬스체크 테스트..."
curl -s http://localhost:8000/health | jq .
echo ""

# 2. Readiness 체크
echo "2. Readiness 체크..."
curl -s http://localhost:8000/ready | jq .
echo ""

# 3. 영수증 업로드
echo "3. 영수증 업로드 테스트..."
RECEIPT_ID=$(curl -s -X POST "http://localhost:8000/api/receipts" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test-receipt.png" | jq -r '.receipt_id')

echo "업로드된 영수증 ID: $RECEIPT_ID"
echo ""

# 4. 영수증 조회
echo "4. 영수증 조회 테스트..."
curl -s "http://localhost:8000/api/receipts/$RECEIPT_ID" | jq .
echo ""

# 5. 메트릭 확인
echo "5. 메트릭 확인..."
curl -s http://localhost:8000/metrics | jq .
echo ""

echo "=== 테스트 완료 ==="
echo "Swagger UI: http://localhost:8000/docs"
