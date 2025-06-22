from cache import cache, cache_result

def test_cache_result_stores():
    cache.clear()
    cache_result('job1', 'output_data')
    assert cache['job1'] == 'output_data'
