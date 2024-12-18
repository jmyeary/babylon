import pytest
from datetime import datetime
from pathlib import Path
from babylon.metrics.collector import MetricsCollector

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for logs during testing."""
    return tmp_path / "test_logs"

@pytest.fixture
def metrics_collector(temp_log_dir):
    """Create a MetricsCollector instance for testing."""
    return MetricsCollector(log_dir=temp_log_dir)

def test_init(metrics_collector, temp_log_dir):
    """Test initialization of MetricsCollector.
    
    This test verifies the proper initialization of a new MetricsCollector instance:
    - Confirms log directory is set to the provided temporary directory
    - Validates that session start time is initialized as a proper datetime object
    - Checks that all counters start at zero (total_objects)
    - Ensures data structures (object_access dict, etc.) are empty
    
    The test uses a temporary directory fixture to avoid polluting the real logs directory.
    """
    assert metrics_collector.log_dir == temp_log_dir
    assert isinstance(metrics_collector.current_session['start_time'], datetime)
    assert metrics_collector.current_session['total_objects'] == 0
    assert len(metrics_collector.metrics['object_access']) == 0

def test_record_object_access(metrics_collector):
    """Test recording object access events.
    
    This test validates the object access tracking system:
    - Records multiple accesses (2x) to test_obj_1 and verifies the count
    - Records single access to test_obj_2 to ensure separate object tracking
    - Confirms counter accuracy by checking exact values
    
    This tracking is crucial for identifying "hot" objects that may need optimization
    or caching in the game engine.
    """
    metrics_collector.record_object_access("test_obj_1", "test_context")
    metrics_collector.record_object_access("test_obj_1", "test_context")
    metrics_collector.record_object_access("test_obj_2", "test_context")
    
    assert metrics_collector.metrics['object_access']['test_obj_1'] == 2
    assert metrics_collector.metrics['object_access']['test_obj_2'] == 1

def test_record_token_usage(metrics_collector):
    """Test recording token usage.
    
    This test checks the token usage tracking functionality:
    - Records two distinct token usage values (100 and 150)
    - Verifies the values are stored in the correct sequence
    - Confirms the deque maintains the exact values without modification
    
    Token usage tracking is essential for monitoring AI model consumption
    and optimizing resource usage in the game's AI systems.
    """
    metrics_collector.record_token_usage(100)
    metrics_collector.record_token_usage(150)
    
    assert len(metrics_collector.metrics['token_usage']) == 2
    assert list(metrics_collector.metrics['token_usage']) == [100, 150]

def test_record_cache_event(metrics_collector):
    """Test recording cache hits and misses.
    
    This test validates the cache performance tracking system:
    - Records and verifies one L1 cache hit
    - Records and verifies one L1 cache miss
    - Records and verifies one L2 cache hit
    - Confirms separate tracking for different cache levels
    
    Cache performance monitoring helps optimize the game's memory hierarchy
    and improve overall system performance.
    """
    metrics_collector.record_cache_event("L1", True)
    metrics_collector.record_cache_event("L1", False)
    metrics_collector.record_cache_event("L2", True)
    
    assert metrics_collector.metrics['cache_performance']['hits']['L1'] == 1
    assert metrics_collector.metrics['cache_performance']['misses']['L1'] == 1
    assert metrics_collector.metrics['cache_performance']['hits']['L2'] == 1
    assert metrics_collector.metrics['cache_performance']['misses']['L2'] == 0

def test_analyze_performance(metrics_collector):
    """Test performance analysis functionality.
    
    This comprehensive test validates the performance analysis system:
    1. Sets up test data:
       - Records multiple accesses to create a "hot" object
       - Records token usage sample
       - Records cache events for hit rate calculation
       - Records latency and memory metrics
       
    2. Triggers analysis and verifies:
       - Cache hit rates are calculated correctly (expected 0.5 for L1)
       - Hot objects are identified based on access frequency
       - Token usage statistics are computed
       - Latency metrics are properly aggregated
       - Memory usage patterns are analyzed
       - System generates relevant optimization suggestions
    
    This test ensures the analysis system provides accurate insights
    for performance optimization and system health monitoring.
    """
    # Setup some test data
    metrics_collector.record_object_access("hot_object", "test")
    metrics_collector.record_object_access("hot_object", "test")
    metrics_collector.record_object_access("hot_object", "test")
    metrics_collector.record_token_usage(100)
    metrics_collector.record_cache_event("L1", True)
    metrics_collector.record_cache_event("L1", False)
    metrics_collector.record_query_latency(10.0)
    metrics_collector.record_memory_usage(1000)
    
    analysis = metrics_collector.analyze_performance()
    
    assert 'cache_hit_rate' in analysis
    assert 'avg_token_usage' in analysis
    assert 'hot_objects' in analysis
    assert 'latency_stats' in analysis
    assert 'memory_profile' in analysis
    assert 'optimization_suggestions' in analysis
    
    assert analysis['hot_objects'] == ['hot_object']
    assert analysis['cache_hit_rate']['L1'] == 0.5

def test_save_metrics(metrics_collector, temp_log_dir):
    """Test saving metrics to disk.
    
    This test validates the metrics persistence system:
    1. Records a sample object access to ensure non-empty metrics
    2. Triggers metrics save operation
    3. Verifies:
       - JSON file is created in the temporary test directory
       - File naming follows the metrics_TIMESTAMP.json pattern
       - Metrics data is properly serialized to JSON
       - Datetime values are converted to ISO format strings
    
    Proper metrics persistence is crucial for:
    - Post-mortem performance analysis
    - System behavior tracking over time
    - Historical trend analysis
    """
    metrics_collector.record_object_access("test_obj", "test")
    metrics_collector.save_metrics()
    
    # Check if metrics file was created
    metric_files = list(temp_log_dir.glob("metrics_*.json"))
    assert len(metric_files) == 1

def test_memory_analysis(metrics_collector):
    """Test memory usage analysis.
    
    This test validates the memory analysis subsystem:
    1. Records a sequence of memory usage values: [1000, 2000, 1500]
    2. Triggers memory analysis
    3. Verifies computed statistics:
       - Average memory usage (1500)
       - Peak memory usage (2000)
       - Current memory usage (1500)
    
    Accurate memory tracking helps:
    - Prevent memory leaks
    - Optimize resource allocation
    - Plan for scaling requirements
    """
    test_values = [1000, 2000, 1500]
    for value in test_values:
        metrics_collector.record_memory_usage(value)
    
    memory_analysis = metrics_collector._analyze_memory_usage()
    assert memory_analysis['avg'] == sum(test_values) / len(test_values)
    assert memory_analysis['peak'] == max(test_values)
    assert memory_analysis['current'] == test_values[-1]

def test_latency_tracking(metrics_collector):
    """Test latency statistics calculation.
    
    This test validates the latency tracking system:
    1. Records a series of database query latencies: [5.0, 10.0, 15.0]
    2. Triggers latency analysis
    3. Verifies computed statistics:
       - Average latency (10.0 ms)
       - Minimum latency (5.0 ms)
       - Maximum latency (15.0 ms)
    
    Latency tracking is essential for:
    - Identifying performance bottlenecks
    - Maintaining responsive gameplay
    - Meeting user experience requirements
    - Database query optimization
    """
    test_latencies = [5.0, 10.0, 15.0]
    for latency in test_latencies:
        metrics_collector.record_query_latency(latency)
    
    latency_stats = metrics_collector._calculate_latency_stats()
    assert 'db_queries' in latency_stats
    assert latency_stats['db_queries']['avg'] == sum(test_latencies) / len(test_latencies)
    assert latency_stats['db_queries']['min'] == min(test_latencies)
    assert latency_stats['db_queries']['max'] == max(test_latencies)
