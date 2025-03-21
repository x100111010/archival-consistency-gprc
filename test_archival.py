from datetime import datetime
import asyncio
import time
from spectred.SpectredClient import SpectredClient


async def get_block_dag_info(rpc_client):
    r = await rpc_client.request("getBlockDagInfoRequest")
    return r["getBlockDagInfoResponse"]


async def get_blocks(rpc_client, low_hash):
    try:
        r = await rpc_client.request(
            "getBlockRequest",
            params={
                "hash": low_hash,
                "includeTransactions": False,
            },
        )
        return r["getBlockResponse"]["block"]
    except Exception:
        # print(f"Error getting block {low_hash}: {e}")
        return None


def print_summary(
    start_time, block_count, seen_count, missing_count, depth, current_daa=None
):
    runtime = (datetime.now() - start_time).total_seconds()
    print("\n========== SUMMARY ==========")
    print(f"Runtime: {runtime:.2f} seconds")
    print(f"Depth: {depth}")
    print(f"Blocks processed: {block_count}")
    print(f"Unique blocks seen: {seen_count}")
    print(f"Missing blocks: {missing_count}")
    if current_daa is not None:
        print(f"Current DAA score: {current_daa}")
    print("=============================\n")


async def main():
    rpc_client = SpectredClient("localhost", 18110)

    dag_info = await get_block_dag_info(rpc_client)
    starting_hash = dag_info["pruningPointHash"]

    # Tracking variables
    block_count = 0
    queue = []
    next_queue = [starting_hash]
    seen = set()
    cache = []
    missing = set()
    parent_child = {}

    start_time = datetime.now()
    last_summary_time = time.time()
    depth = 0
    current_daa = None

    # Begin traversal
    while next_queue:
        current_time = time.time()
        if current_time - last_summary_time >= 30:
            print_summary(
                start_time, block_count, len(seen), len(missing), depth, current_daa
            )
            last_summary_time = current_time

        queue = next_queue
        next_queue = []
        max_daa_score = 0

        while queue:
            current_hash = queue.pop()
            if current_hash in seen:
                continue
            else:
                seen.add(current_hash)

            block_count += 1

            try:
                block = await get_blocks(rpc_client, current_hash)
                if block:
                    daa_score = int(block["header"]["daaScore"])
                    current_daa = daa_score  # Keep track of current DAA score
                    max_daa_score = max(max_daa_score, daa_score)

                    cache.append({"hash": current_hash, "daaScore": daa_score})

                    parent_dict = block["header"]["parents"][
                        0
                    ]  # Get the first parent level
                    for parent_hash in parent_dict["parentHashes"]:
                        next_queue.append(parent_hash)
                        parent_child[parent_hash] = current_hash
            except Exception:
                # just track the missing block
                missing.add(current_hash)

        depth += 1

        # Prune cache to manage memory
        while cache and cache[0]["daaScore"] >= max_daa_score + 36000:
            block = cache.pop(0)
            seen.discard(block["hash"])
            if block["hash"] in parent_child:
                del parent_child[block["hash"]]

    # Final summary
    print("\n===== FINAL REPORT =====")
    print(f"Blocks Seen: {block_count}")
    print(f"Unique Blocks: {len(seen)}")
    print(f"Missing Blocks: {len(missing)}")

    if missing:
        print("\nMissing Block Details:")
        for hash_value in missing:
            if hash_value in parent_child:
                print(f"Missing: {hash_value} -> added by {parent_child[hash_value]}")

    runtime = (datetime.now() - start_time).total_seconds()
    print(f"Total Runtime: {runtime:.2f} seconds")
    print("=======================")


if __name__ == "__main__":
    asyncio.run(main())
