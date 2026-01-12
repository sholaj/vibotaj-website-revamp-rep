/**
 * API Client Cache Tests
 *
 * Bug: VIBO-2026-560 not viewable after creation
 * Root cause: Cache key mismatch between get ('GET:shipments') and invalidate ('/shipments')
 */

import { describe, it, expect, beforeEach } from 'vitest';

// Simulated SimpleCache from client.ts to test the bug
class SimpleCache {
  private cache: Map<string, { data: unknown; timestamp: number; ttl: number }> = new Map();

  set<T>(key: string, data: T, ttl: number = 60000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > entry.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  invalidate(pattern?: string): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  // Helper for testing
  size(): number {
    return this.cache.size;
  }
}

describe('SimpleCache', () => {
  let cache: SimpleCache;

  beforeEach(() => {
    cache = new SimpleCache();
  });

  describe('cache invalidation bug', () => {
    it('documents the bug pattern: leading slash mismatch prevents invalidation', () => {
      // This test documents the bug pattern that was fixed:
      // - BEFORE: getShipments() cached with 'GET:shipments' but invalidated with '/shipments'
      // - AFTER: Both use 'shipments' (no leading slash)

      // Simulate old broken pattern (leading slash in pattern)
      cache.set('GET:shipments', [{ id: '1', reference: 'VIBO-2026-559' }]);
      cache.invalidate('/shipments'); // OLD buggy pattern

      // Bug demonstrated: 'GET:shipments'.includes('/shipments') === false
      expect(cache.get('GET:shipments')).not.toBeNull(); // Stale data remains!

      // Now test the FIXED pattern
      cache.invalidate('shipments'); // FIXED: no leading slash

      // Cache correctly invalidated
      expect(cache.get('GET:shipments')).toBeNull();
    });

    it('FIXED: correctly invalidates when pattern matches key format', () => {
      // This shows the expected behavior after fix:
      // Both cache key and invalidation pattern should use consistent format

      // Simulate getShipments() caching
      cache.set('GET:shipments', [{ id: '1', reference: 'VIBO-2026-559' }]);

      // Verify cache has data
      expect(cache.get('GET:shipments')).not.toBeNull();

      // Correct invalidation pattern (without leading slash)
      cache.invalidate('shipments');

      // Cache should be invalidated
      expect(cache.get('GET:shipments')).toBeNull();
      expect(cache.size()).toBe(0);
    });

    it('should invalidate shipment list when new shipment created', () => {
      // Full scenario: user creates shipment, list should refresh with new data

      // Initial load - cache populated
      const initialShipments = [{ id: '1', reference: 'VIBO-2026-559' }];
      cache.set('GET:shipments', initialShipments);

      // User creates a new shipment
      // ... API call happens ...

      // Invalidate cache (FIX: use pattern without leading slash)
      cache.invalidate('shipments');

      // Cache miss forces re-fetch
      expect(cache.get('GET:shipments')).toBeNull();
    });
  });

  describe('basic operations', () => {
    it('should store and retrieve data', () => {
      cache.set('test-key', { value: 123 });
      expect(cache.get('test-key')).toEqual({ value: 123 });
    });

    it('should return null for missing keys', () => {
      expect(cache.get('nonexistent')).toBeNull();
    });

    it('should clear all data when invalidate called without pattern', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');

      cache.invalidate();

      expect(cache.get('key1')).toBeNull();
      expect(cache.get('key2')).toBeNull();
    });
  });
});
