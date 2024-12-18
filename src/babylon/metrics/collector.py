from collections import Counter, deque
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

class MetricsCollector:
    """Collects and analyzes performance metrics for object tracking."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        # Set up logging directory, default to logs/metrics if not specified
        self.log_dir = log_dir or Path("logs/metrics")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging with timestamp, component name, and message
        logging.basicConfig(
            filename=self.log_dir / "metrics.log",
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize metrics storage containers
        self.metrics = {
            'object_access': Counter(),  # Tracks access frequency per object
            'token_usage': deque(maxlen=1000),  # Rolling window of token counts
            'cache_performance': {
                'hits': Counter(),  # Successful cache retrievals by type
                'misses': Counter()  # Failed cache lookups by type
            },
            'latency': {
                'db_queries': deque(maxlen=100),  # Database query response times
                'context_switches': deque(maxlen=100)  # Context switch durations
            },
            'memory_usage': deque(maxlen=1000)  # Rolling window of memory samples
        }
        
        # Track current session statistics
        self.current_session = {
            'start_time': datetime.now(),  # Session start timestamp
            'total_objects': 0,  # Total objects created in session
            'active_objects': 0,  # Currently active objects
            'cached_objects': 0   # Objects currently in cache
        }

    def record_object_access(self, object_id: str, context_level: str) -> None:
        """Record an object access event."""
        self.metrics['object_access'][object_id] += 1
        logging.info(f"Object accessed: {object_id} in {context_level}")

    def record_token_usage(self, tokens_used: int) -> None:
        """Record token usage."""
        self.metrics['token_usage'].append(tokens_used)
        logging.info(f"Token usage: {tokens_used}")

    def record_cache_event(self, cache_type: str, hit: bool) -> None:
        """Record cache hit/miss."""
        if hit:
            self.metrics['cache_performance']['hits'][cache_type] += 1
        else:
            self.metrics['cache_performance']['misses'][cache_type] += 1

    def record_query_latency(self, latency_ms: float) -> None:
        """Record database query latency."""
        self.metrics['latency']['db_queries'].append(latency_ms)

    def record_context_switch(self, latency_ms: float) -> None:
        """Record context switch latency."""
        self.metrics['latency']['context_switches'].append(latency_ms)

    def record_memory_usage(self, bytes_used: int) -> None:
        """Record memory usage."""
        self.metrics['memory_usage'].append(bytes_used)

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze collected metrics and return insights."""
        analysis = {
            'cache_hit_rate': self._calculate_hit_rate(),
            'avg_token_usage': self._calculate_avg_tokens(),
            'hot_objects': self._identify_hot_objects(),
            'latency_stats': self._calculate_latency_stats(),
            'memory_profile': self._analyze_memory_usage(),
            'optimization_suggestions': self._generate_suggestions()
        }
        
        # Log analysis
        logging.info(f"Performance analysis: {json.dumps(analysis, indent=2)}")
        return analysis

    def _calculate_hit_rate(self) -> Dict[str, float]:
        """Calculate cache hit rates for different cache levels.
        
        Computes the ratio of cache hits to total accesses for each cache type.
        A higher hit rate indicates better cache efficiency.
        
        Returns:
            Dict mapping cache type to hit rate (0.0 to 1.0)
        """
        rates = {}
        for cache_type in self.metrics['cache_performance']['hits']:
            hits = self.metrics['cache_performance']['hits'][cache_type]
            misses = self.metrics['cache_performance']['misses'][cache_type]
            total = hits + misses
            # Avoid division by zero for unused cache types
            rates[cache_type] = (hits / total) if total > 0 else 0
        return rates

    def _calculate_avg_tokens(self) -> float:
        """Calculate average token usage."""
        return sum(self.metrics['token_usage']) / len(self.metrics['token_usage']) if self.metrics['token_usage'] else 0

    def _identify_hot_objects(self, threshold: int = 3) -> List[str]:
        """Identify frequently accessed objects."""
        return [obj_id for obj_id, count in self.metrics['object_access'].most_common() 
                if count >= threshold]

    def _calculate_latency_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate latency statistics."""
        stats = {}
        for metric_type in ['db_queries', 'context_switches']:
            values = list(self.metrics['latency'][metric_type])
            if values:
                stats[metric_type] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        return stats

    def _analyze_memory_usage(self) -> Dict[str, float]:
        """Analyze memory usage patterns."""
        values = list(self.metrics['memory_usage'])
        if not values:
            return {}
        return {
            'avg': sum(values) / len(values),
            'peak': max(values),
            'current': values[-1]
        }

    def _generate_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on metrics.
        
        Analyzes various performance metrics and generates actionable suggestions:
        - Cache size adjustments when hit rates are below target (80%)
        - Token usage optimizations when approaching context limits
        - Memory management recommendations when usage is high
        
        Returns:
            List of suggestion strings for system optimization
        """
        suggestions = []
        
        # Cache performance suggestions - target 80% hit rate
        hit_rates = self._calculate_hit_rate()
        for cache_type, rate in hit_rates.items():
            if rate < 0.8:  # Below target efficiency
                suggestions.append(f"Consider increasing {cache_type} cache size (current hit rate: {rate:.2%})")

        # Token usage suggestions - warn at 75% of context window
        avg_tokens = self._calculate_avg_tokens()
        if avg_tokens > 150000:  # 75% of context window
            suggestions.append("High token usage detected. Consider implementing more aggressive object summarization.")

        # Memory usage suggestions - warn at 80% of peak
        memory_stats = self._analyze_memory_usage()
        if memory_stats.get('current', 0) > 0.8 * memory_stats.get('peak', 0):
            suggestions.append("Memory usage approaching peak. Consider garbage collection.")

        return suggestions

    def save_metrics(self) -> None:
        """Save current metrics to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.log_dir / f"metrics_{timestamp}.json"
        
        # Create a copy of current_session with datetime converted to string
        session_info = dict(self.current_session)
        session_info['start_time'] = session_info['start_time'].isoformat()
        
        with open(metrics_file, 'w') as f:
            json.dump({
                'session_info': session_info,
                'metrics': {
                    'object_access': dict(self.metrics['object_access']),
                    'token_usage': list(self.metrics['token_usage']),
                    'cache_performance': {
                        'hits': dict(self.metrics['cache_performance']['hits']),
                        'misses': dict(self.metrics['cache_performance']['misses'])
                    },
                    'latency': {
                        'db_queries': list(self.metrics['latency']['db_queries']),
                        'context_switches': list(self.metrics['latency']['context_switches'])
                    },
                    'memory_usage': list(self.metrics['memory_usage'])
                }
            }, f, indent=2)
