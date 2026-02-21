"""
Unit tests for demo topology.json files.

Validates that every demo's topology.json:
  - Exists and is valid JSON
  - Contains required 'nodes' and 'edges' arrays
  - Has unique node IDs
  - Has edges that reference valid node IDs
  - Has a 'pattern' and 'title' string

Run:
    python -m pytest tests/test_topology.py -v
or:
    python tests/test_topology.py
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIR = REPO_ROOT / "demos"

DEMO_IDS = [
    "maker_checker",
    "hierarchical_research",
    "handoff_support",
    "network_brainstorm",
    "supervisor_router",
    "swarm_auditor",
]


def load_topology(demo_id: str) -> dict:
    path = DEMOS_DIR / demo_id / "topology.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestTopologyFiles(unittest.TestCase):

    def test_topology_files_exist(self):
        for demo_id in DEMO_IDS:
            path = DEMOS_DIR / demo_id / "topology.json"
            self.assertTrue(path.exists(), f"topology.json missing for {demo_id}")

    def test_topology_valid_json(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                self.assertIsInstance(topology, dict)

    def test_topology_has_required_fields(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                self.assertIn("nodes", topology, f"{demo_id}: missing 'nodes'")
                self.assertIn("edges", topology, f"{demo_id}: missing 'edges'")
                self.assertIsInstance(topology["nodes"], list, f"{demo_id}: 'nodes' must be a list")
                self.assertIsInstance(topology["edges"], list, f"{demo_id}: 'edges' must be a list")

    def test_topology_has_metadata(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                self.assertIn("pattern", topology, f"{demo_id}: missing 'pattern'")
                # topology files use either 'title' or 'name' for the display name
                has_name = "title" in topology or "name" in topology
                self.assertTrue(has_name, f"{demo_id}: missing 'title' or 'name'")
                self.assertIsInstance(topology["pattern"], str)

    def test_nodes_have_ids(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                for i, node in enumerate(topology["nodes"]):
                    node_id = node.get("id") or node.get("name")
                    self.assertTrue(node_id, f"{demo_id}: node[{i}] missing 'id' or 'name'")

    def test_node_ids_are_unique(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                ids = [n.get("id") or n.get("name") for n in topology["nodes"]]
                self.assertEqual(len(ids), len(set(ids)), f"{demo_id}: duplicate node IDs: {ids}")

    def test_edges_reference_valid_nodes(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                node_ids = {n.get("id") or n.get("name") for n in topology["nodes"]}
                for i, edge in enumerate(topology["edges"]):
                    src = edge.get("source") or edge.get("from")
                    tgt = edge.get("target") or edge.get("to")
                    self.assertIn(src, node_ids, f"{demo_id}: edge[{i}] source '{src}' not in nodes")
                    self.assertIn(tgt, node_ids, f"{demo_id}: edge[{i}] target '{tgt}' not in nodes")

    def test_nodes_have_at_least_one(self):
        for demo_id in DEMO_IDS:
            with self.subTest(demo=demo_id):
                topology = load_topology(demo_id)
                self.assertGreater(len(topology["nodes"]), 0, f"{demo_id}: must have at least one node")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    unittest.main(verbosity=2)
