import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from models import HealingDecision
from config import settings

# Async Database Components
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import select, update, func, String, Integer, BigInt, Float, DateTime, Text, desc, Identity

logger = logging.getLogger(__name__)

Base = declarative_base()

class DBAlert(Base):
    """
    PostgreSQL alerts table modeled using wshobson/agents@postgresql-table-design
    """
    __tablename__ = 'alerts'
    id: Mapped[int] = mapped_column(BigInt, Identity(always=True), primary_key=True)
    alertname: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    namespace: Mapped[str] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=True)
    analysis: Mapped[str] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str] = mapped_column(Text, default="", nullable=True)
    risk_level: Mapped[str] = mapped_column(String(50), default="medium")
    status: Mapped[str] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class DBAuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(BigInt, Identity(always=True), primary_key=True)
    action_title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    operator: Mapped[str] = mapped_column(String(100), nullable=True)
    log_type: Mapped[str] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class DatabaseService:
    def __init__(self):
        self.postgres_url = settings.POSTGRES_URL
        self.redis_url = settings.REDIS_URL
        self.engine = create_async_engine(self.postgres_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        self.redis_client = None

    async def init_db(self):
        """Initializes PostgreSQL schemas and Redis connections."""
        # 1. Initialize Postgres Schema
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 2. Initialize Redis Caching Layer
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        # Test Redis ping
        await self.redis_client.ping()

    async def record_alert(self, alert_name: str, decision: HealingDecision, status: str) -> int:
        async with self.async_session() as session:
            new_alert = DBAlert(
                alertname=alert_name,
                target=decision.target.name,
                namespace=decision.target.namespace,
                confidence=decision.confidence,
                action=decision.action,
                analysis=decision.analysis,
                root_cause=decision.root_cause,
                risk_level=decision.risk_level,
                status=status
            )
            session.add(new_alert)
            await session.commit()
            return new_alert.id

    async def update_alert_status(self, alert_id: int, new_status: str):
        async with self.async_session() as session:
            stmt = update(DBAlert).where(DBAlert.id == alert_id).values(status=new_status)
            await session.execute(stmt)
            await session.commit()

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(DBAlert).order_by(desc(DBAlert.timestamp)).limit(limit)
            result = await session.execute(stmt)
            alerts = result.scalars().all()
            return [{
                "id": a.id, "alertname": a.alertname, "target": a.target, "namespace": a.namespace,
                "confidence": a.confidence, "action": a.action, "analysis": a.analysis,
                "root_cause": a.root_cause, "risk_level": a.risk_level, "status": a.status,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None
            } for a in alerts]
    
    async def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(DBAlert).where(DBAlert.id == alert_id)
            result = await session.execute(stmt)
            a = result.scalars().first()
            if a:
                return {
                    "id": a.id, "alertname": a.alertname, "target": a.target, "namespace": a.namespace,
                    "confidence": a.confidence, "action": a.action, "analysis": a.analysis,
                    "root_cause": a.root_cause, "risk_level": a.risk_level, "status": a.status,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None
                }
            return None

    async def record_audit(self, title: str, description: str, operator: str, log_type: str = "info"):
        async with self.async_session() as session:
            new_audit = DBAuditLog(
                action_title=title,
                description=description,
                operator=operator,
                log_type=log_type
            )
            session.add(new_audit)
            await session.commit()

    async def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(DBAuditLog).order_by(desc(DBAuditLog.timestamp)).limit(limit)
            result = await session.execute(stmt)
            logs = result.scalars().all()
            return [{
                "id": l.id, "action_title": l.action_title, "description": l.description,
                "operator": l.operator, "type": l.log_type, 
                "timestamp": l.timestamp.isoformat() if l.timestamp else None
            } for l in logs]

    # ---- Stats caching with Redis Implementation mindrally/skills@redis-best-practices ----

    async def get_today_alert_count(self) -> int:
        cache_key = f"stats:today_alert_count:{datetime.utcnow().strftime('%Y-%m-%d')}"
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached: return int(cached)
            
        async with self.async_session() as session:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = select(func.count()).select_from(DBAlert).where(DBAlert.timestamp >= today_start)
            result = await session.execute(stmt)
            count = result.scalar() or 0
        
        if self.redis_client:
            await self.redis_client.setex(cache_key, 60, str(count)) # cache for 60s
        return count

    async def get_auto_healed_count(self) -> int:
        async with self.async_session() as session:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = select(func.count()).select_from(DBAlert).where(
                DBAlert.timestamp >= today_start,
                DBAlert.status.like('%自动执行%')
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_pending_approval_count(self) -> int:
        async with self.async_session() as session:
            stmt = select(func.count()).select_from(DBAlert).where(DBAlert.status == '待审批')
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_healing_success_rate(self) -> float:
        async with self.async_session() as session:
            stmt_total = select(func.count()).select_from(DBAlert).where(DBAlert.action.notin_(['no_action', 'investigate']))
            res_total = await session.execute(stmt_total)
            total = res_total.scalar() or 0
            
            if total == 0: return 0.0

            stmt_success = select(func.count()).select_from(DBAlert).where(
                DBAlert.action.notin_(['no_action', 'investigate']),
                (DBAlert.status.like('%自动执行%') | DBAlert.status.like('%授权%'))
            )
            res_success = await session.execute(stmt_success)
            success = res_success.scalar() or 0
            
            return round((success / total) * 100, 1)

    async def get_action_distribution(self) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(DBAlert.action, func.count(DBAlert.id).label('count')).where(
                DBAlert.action.notin_(['no_action'])
            ).group_by(DBAlert.action).order_by(desc('count'))
            result = await session.execute(stmt)
            rows = result.all()
            return [{"name": row[0], "value": row[1]} for row in rows]

    async def check_cooldown(self, target_name: str, namespace: str) -> bool:
        """
        O(1) Rate limiting using Redis TTL. Massively improves Postgres throughput.
        """
        if not self.redis_client:
            return False
        
        cooldown_key = f"cooldown:{namespace}:{target_name}"
        is_cooling = await self.redis_client.get(cooldown_key)
        if is_cooling:
            return True
        
        await self.redis_client.setex(cooldown_key, settings.HEALING_COOLDOWN_SECONDS, "1")
        return False
