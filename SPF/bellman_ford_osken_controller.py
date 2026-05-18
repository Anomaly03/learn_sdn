#!/usr/bin/env python3
"""Bellman-Ford SPF OpenFlow controller."""

import json
import os
import sys

from base_controller import SPFBaseController
from algorithms.bellman_ford import bellman_ford

BF_FLOW_COOKIE = 0x42464F5200000001
BF_FLOW_COOKIE_MASK = 0xFFFFFFFFFFFFFFFF
BF_FLOW_PRIORITY = 100

# Optional static weight file
WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "link_weights.json")


def _load_weights(path):
    """Load link weights from JSON."""
    try:
        with open(path) as f:
            data = json.load(f)
        raw = data.get("links", {})
        return {
            tuple(int(x) for x in k.split(":")): v.get("bandwidth_mbps", 1)
            for k, v in raw.items()
        }
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {}


class BellmanFordSwitch(SPFBaseController):
    """Shortest path forwarding using the Bellman-Ford relaxation algorithm."""

    FLOW_COOKIE = BF_FLOW_COOKIE

    def __init__(self, *args, **kwargs):
        super(BellmanFordSwitch, self).__init__(*args, **kwargs)
        raw_weights = _load_weights(WEIGHTS_FILE)
        self._link_weights = raw_weights
        if raw_weights:
            self.logger.info("[BF-WEIGHTS] loaded %d link weights", len(raw_weights))
        else:
            self.logger.info("[BF-WEIGHTS] no weight file; using hop-count metric")

    def _build_weight_dict(self):
        """Build weights dict keyed by (u, v) from current adjacency."""
        if not self._link_weights:
            return None
        weights = {}
        for u in self.adjacency:
            for v, _ in self.adjacency[u]:
                key = (min(u, v), max(u, v))
                weights[(u, v)] = self._link_weights.get(key, 1)
                weights[(v, u)] = self._link_weights.get(key, 1)
        return weights

    def compute_path(self, src, dst, first_port, final_port):
        """Compute shortest path using Bellman-Ford edge-relaxation."""
        self.logger.debug("[PATH-QUERY] Bellman-Ford: s%d -> s%d", src, dst)

        weights = self._build_weight_dict()

        # --- Phase 1+2: Relax all edges V-1 times ---
        distance, previous, has_neg_cycle = bellman_ford(
            self.adjacency, src, weights=weights
        )

        # --- Phase 3: Report negative cycle ---
        if has_neg_cycle:
            self.logger.warning("[BF-NEGCYCLE] negative-weight cycle detected!")

        reachable = sum(1 for d in distance.values() if d != float("inf"))
        
        # Log hasil SPF
        self.logger.info("[SPF-DONE] BF s%d->s%d reachable=%d/%d",
                         src, dst, reachable, len(distance))

        # --- Phase 4: Reconstruct path ---
        path_result = self._reconstruct_path(src, dst, first_port, final_port, distance, previous)

        # --- MODIFIKASI: Visual Separator ---
        # Memberikan baris kosong dan pembatas agar log mudah dibaca per iterasi
        print("\n" + "="*60)
        print(" [ITERATION COMPLETED] Bellman-Ford Calculation Cycle")
        print("="*60 + "\n")

        return path_result


if __name__ == '__main__':
    current_file = os.path.abspath(__file__)
    passthrough_args = sys.argv[1:]
    if '--observe-links' not in passthrough_args:
        passthrough_args = ['--observe-links'] + passthrough_args
    sys.argv = ['bellman_ford_osken_controller', *passthrough_args, current_file]
    from os_ken.cmd.manager import main
    sys.exit(main())