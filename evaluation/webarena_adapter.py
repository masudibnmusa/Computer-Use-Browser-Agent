"""Optional: adapt WebArena / MiniWoB++ tasks to the benchmark runner.

Sketch: load a task's config (start URL, intent, evaluator) -> BenchTask(name, goal=intent,
start_path=start_url, check=<evaluator wrapper>). WebArena needs its own self-hosted sites; set
BA_ALLOWED_DOMAINS to those hosts before running.
"""
raise NotImplementedError("Implement once the local benchmark is stable.")