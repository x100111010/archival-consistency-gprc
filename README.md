# Spectred gRPC client for checking archival consistency

- starts by getting the `pruningPointHash` from `getdaginfo` which is used as the `starting_hash` to traverse the dag
- uses `getblock` to get a blocks parents and traverses the parents until the loop breaks ideally at the genesis hash. the genesis hash would report missing block because it does not have any parents
- parent traversal is done using [breadth-first](https://en.wikipedia.org/wiki/Breadth-first_search) traversal by maintaining two queues (queue and next_queue) and it processes all blocks at the current "level" before moving to older blocks
- keeps track of unique blocks in 'seen' set to avoid processing duplicates
- records parent-child relationships in the parent_child dic to track missing blocks
- progress summaries every 30 seconds showing runtime, depth and block statistics

```
========== SUMMARY ==========
Runtime: 40386.59 seconds
Depth: 9459414
Blocks processed: 28058772
Unique blocks seen: 36886
Missing blocks: 0
Current DAA score: 14215
=============================


===== FINAL REPORT =====
Blocks Seen: 28072987
Unique Blocks: 36886
Missing Blocks: 1

Missing Block Details:
Missing: f7d60970f5b6cb1e6afa04813a865a593f8e009708355f4282ab28894faa25bf -> added by 98ad15fedc5b2c545fa695395f1584f5c7d716ea83634bfecb240846dc3c1daf
Total Runtime: 40405.62 seconds
=======================
```

```python
while cache and cache[0]["daaScore"] >= max_daa_score + 36000:
    block = cache.pop(0)
    seen.discard(block["hash"])
    if block["hash"] in parent_child:
        del parent_child[block["hash"]]
```

Blocks with DAA scores that are 36000 points higher than the maximum DAA score in the current processing batch are removed from tracking.

- missing blocks are identified when getblock fails to retrieve a block that was referenced as a parent
- tracks which child block referenced each missing block
- final report shows total blocks processed, unique blocks, missing blocks and runtime
