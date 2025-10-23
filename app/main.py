from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import os
import asyncpg
from contextlib import asynccontextmanager

# 데이터베이스 연결 풀 (전역 변수)
db_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 라이프사이클 이벤트"""
    global db_pool
    
    # 시작: DB 연결 풀 생성
    database_url = os.getenv("DATABASE_URL", "postgresql://receipts_user:receipts_password@db:5432/receipts_db")
    try:
        db_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
        print("✅ Database connection pool created")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   API will run in DUMMY mode (no real DB operations)")
        db_pool = None
    
    yield
    
    # 종료: DB 연결 풀 정리
    if db_pool:
        await db_pool.close()
        print("✅ Database connection pool closed")


app = FastAPI(
    title="스팬딧 영수증 분석 API",
    description="영수증 이미지를 업로드하여 지출 내역을 분석하는 API",
    version="1.0.0",
    lifespan=lifespan
)

# 환경변수에서 설정 로드
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://receipts_user:receipts_password@db:5432/receipts_db")
PORT = int(os.getenv("PORT", "8000"))


class ReceiptResponse(BaseModel):
    """영수증 분석 응답 모델"""
    receipt_id: str
    merchant_name: str
    total_amount: float
    date: str
    status: str
    message: str


class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str
    timestamp: str
    database: str
    version: str


@app.get("/", tags=["Root"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "스팬딧 영수증 분석 API에 오신 것을 환영합니다",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    헬스체크 엔드포인트
    - 서비스 상태 확인
    - 데이터베이스 연결 상태 확인
    """
    db_status = "not configured"
    
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.now().isoformat(),
        database=db_status,
        version="1.0.0"
    )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness 체크 엔드포인트
    - Kubernetes/ECS에서 사용할 수 있는 준비 상태 확인
    """
    # 실제 환경에서는 DB 연결, 외부 API 상태 등을 체크
    return {"status": "ready", "timestamp": datetime.now().isoformat()}


@app.post("/api/receipts", response_model=ReceiptResponse, tags=["Receipts"])
async def upload_receipt(file: UploadFile = File(...)):
    """
    영수증 업로드 및 분석 엔드포인트
    
    - **file**: 영수증 이미지 파일 (jpg, png 등)
    
    실제 환경에서는:
    1. 이미지를 S3에 업로드
    2. OCR API로 텍스트 추출
    3. 분석 결과를 DB에 저장
    4. 비동기 처리를 위해 SQS 큐에 메시지 발행
    
    현재 구현:
    - 더미 데이터를 생성하여 DB에 실제로 저장합니다
    - DB 연결이 없으면 더미 응답만 반환합니다
    """
    # 파일 타입 검증
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="이미지 파일만 업로드 가능합니다"
        )
    
    # 영수증 ID 생성
    receipt_id = "RCP-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    merchant_name = "스타벅스 강남점"
    total_amount = 15000.0
    receipt_date = datetime.now().date()
    
    # 데이터베이스에 저장 시도
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                # 영수증 메인 정보 저장
                await conn.execute("""
                    INSERT INTO receipts (receipt_id, merchant_name, total_amount, receipt_date, image_url, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, receipt_id, merchant_name, total_amount, receipt_date, 
                    f"s3://receipts/{receipt_id}.jpg", "processed")
                
                # 영수증 항목 저장 (더미 데이터)
                items = [
                    ("아메리카노", 2, 4500.0),
                    ("샌드위치", 1, 6000.0)
                ]
                for item_name, quantity, price in items:
                    await conn.execute("""
                        INSERT INTO receipt_items (receipt_id, item_name, quantity, price)
                        VALUES ($1, $2, $3, $4)
                    """, receipt_id, item_name, quantity, price)
                
                print(f"✅ Receipt {receipt_id} saved to database")
                message = "영수증이 성공적으로 분석되고 저장되었습니다"
        except Exception as e:
            print(f"⚠️  Database save failed: {e}")
            message = f"영수증이 분석되었으나 저장 실패 (DB 오류)"
    else:
        message = "영수증이 분석되었습니다 (더미 모드 - DB 미연결)"
    
    return ReceiptResponse(
        receipt_id=receipt_id,
        merchant_name=merchant_name,
        total_amount=total_amount,
        date=receipt_date.isoformat(),
        status="processed",
        message=message
    )


@app.get("/api/receipts/{receipt_id}", tags=["Receipts"])
async def get_receipt(receipt_id: str):
    """
    특정 영수증 조회 엔드포인트
    
    실제 환경에서는 DB에서 영수증 정보를 조회합니다.
    현재 구현: DB가 연결되어 있으면 실제 조회, 없으면 더미 응답
    """
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                # 영수증 메인 정보 조회
                receipt = await conn.fetchrow("""
                    SELECT receipt_id, merchant_name, total_amount, receipt_date, status
                    FROM receipts
                    WHERE receipt_id = $1
                """, receipt_id)
                
                if not receipt:
                    raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다")
                
                # 영수증 항목 조회
                items = await conn.fetch("""
                    SELECT item_name, quantity, price
                    FROM receipt_items
                    WHERE receipt_id = $1
                """, receipt_id)
                
                return {
                    "receipt_id": receipt['receipt_id'],
                    "merchant_name": receipt['merchant_name'],
                    "total_amount": float(receipt['total_amount']),
                    "date": receipt['receipt_date'].isoformat(),
                    "status": receipt['status'],
                    "items": [
                        {
                            "name": item['item_name'],
                            "quantity": item['quantity'],
                            "price": float(item['price'])
                        }
                        for item in items
                    ]
                }
        except HTTPException:
            raise
        except Exception as e:
            print(f"⚠️  Database query failed: {e}")
            # DB 오류 시 더미 응답으로 폴백
    
    # 더미 응답 (DB 미연결 또는 오류 시)
    return {
        "receipt_id": receipt_id,
        "merchant_name": "스타벅스 강남점 (더미)",
        "total_amount": 15000.0,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": "processed",
        "items": [
            {"name": "아메리카노", "quantity": 2, "price": 4500},
            {"name": "샌드위치", "quantity": 1, "price": 6000}
        ]
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    메트릭 엔드포인트 (Prometheus 포맷 더미)
    
    실제 환경에서는 prometheus_client를 사용하여
    실제 메트릭을 노출합니다.
    """
    return {
        "requests_total": 1000,
        "requests_success": 950,
        "requests_failed": 50,
        "avg_response_time_ms": 120,
        "active_connections": 5
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
