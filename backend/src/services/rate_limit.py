import asyncio
import time

class InMemoryStore:
    def __init__(self):
        self.store = {}
    async def incr(self, key):
        val = self.store.get(key, 0) + 1
        self.store[key] = val
        return val
    async def expire(self, key, seconds):
        # simple expiration using timestamps
        self.store.setdefault("_exp", {})[key] = time.time() + seconds
    async def get(self, key):
        exp = self.store.get("_exp", {}).get(key)
        if exp and time.time() > exp:
            self.store.pop(key, None)
            self.store["_exp"].pop(key, None)
            return None
        return self.store.get(key)
    async def set(self, key, val, ex=None):
        self.store[key] = val
        if ex:
            await self.expire(key, ex)
    async def delete(self, key):
        self.store.pop(key, None)
        if "_exp" in self.store:
            self.store["_exp"].pop(key, None)

class RateLimiter:
    def __init__(self, redis_url=None):
        self.redis_url = redis_url
        self.prefix = "rl:"
        self.limit = 5
        self.block_seconds = 300
        self._redis = None
        self._inmem = InMemoryStore()
        self._use_redis = None  # None = unknown, False = fallback to inmem, True = use redis

    async def _get_redis(self):
        if self._use_redis is False:
            return None
        if self._redis:
            return self._redis
        try:
            import aioredis
            self._redis = await aioredis.from_url(self.redis_url or "redis://localhost:6379/0", decode_responses=True)
            self._use_redis = True
            return self._redis
        except Exception:
            # fallback to in-memory storage
            self._use_redis = False
            return None

    async def register_failure(self, key):
        r = await self._get_redis()
        if r:
            cnt = await r.incr(self.prefix + key)
            if cnt == 1:
                await r.expire(self.prefix + key, self.block_seconds)
            if cnt >= self.limit:
                await r.set(self.prefix + "blocked:" + key, "1", ex=self.block_seconds)
        else:
            cnt = await self._inmem.incr(self.prefix + key)
            if cnt == 1:
                await self._inmem.expire(self.prefix + key, self.block_seconds)
            if cnt >= self.limit:
                await self._inmem.set(self.prefix + "blocked:" + key, "1", ex=self.block_seconds)

    async def is_blocked(self, key):
        r = await self._get_redis()
        if r:
            v = await r.get(self.prefix + "blocked:" + key)
            return v is not None
        else:
            v = await self._inmem.get(self.prefix + "blocked:" + key)
            return v is not None

    async def reset(self, key):
        r = await self._get_redis()
        if r:
            await r.delete(self.prefix + key)
            await r.delete(self.prefix + "blocked:" + key)
        else:
            await self._inmem.delete(self.prefix + key)
            await self._inmem.delete(self.prefix + "blocked:" + key)
