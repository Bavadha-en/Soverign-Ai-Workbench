import io
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image

from backend.documents.pid_preprocessor import pid_preprocessor
from backend.documents.ocr import ocr_engine
from backend.documents.pid_symbol_detector import pid_symbol_detector
from backend.documents.pid_topology import pid_topology_extractor
from backend.models.schemas import LLMGenerateRequest
from backend.llm.factory import get_llm_provider


class PIDHybridPipeline:
    """
    Sovereign Hybrid P&ID Analysis Pipeline.
    Combines:
      1. Arbitrary-resolution image preprocessing & multi-scale overlapping tiling
      2. Local RapidOCR with ISA-5.1 engineering tag normalization
      3. Deterministic symbol detection & Eng_Diagrams template classification
      4. Morphological line & graph topology extraction
      5. Targeted crop-level Moondream VLM disambiguation (structured JSON)
      6. Synthesis into an evidence-grounded P&ID_CONTEXT representation
    """

    def __init__(self):
        self.preprocessor = pid_preprocessor
        self.ocr = ocr_engine
        self.symbol_detector = pid_symbol_detector
        self.topology_extractor = pid_topology_extractor

    async def analyze(
        self,
        image_source: Union[str, bytes, np.ndarray],
        query: Optional[str] = None,
        use_vlm_disambiguation: bool = True
    ) -> Dict[str, Any]:
        """
        Execute end-to-end hybrid analysis of a P&ID diagram.
        """
        start_time = time.time()

        # Step 1: Preprocessing & Multi-scale Tiling
        prep = self.preprocessor.preprocess(image_source)
        original_bgr = prep["original"]
        h, w = original_bgr.shape[:2]
        tiles = self.preprocessor.generate_tiles(original_bgr, tile_size=512, overlap_ratio=0.20)

        # Step 2: High-Precision OCR for Engineering Tags
        # Run OCR on the OCR-friendly preprocessed diagram
        ocr_tags = self.ocr.extract_engineering_tags(prep["ocr_friendly"], min_confidence=0.50)

        # Step 3: Deterministic Engineering Symbol Detection
        detected_symbols = self.symbol_detector.detect_symbols_in_diagram(original_bgr)

        # Step 4: Topology, Line & Connectivity Graph Extraction
        topology = self.topology_extractor.extract_topology(
            original_bgr,
            detected_tags=ocr_tags,
            detected_symbols=detected_symbols
        )

        # Categorize detected nodes into equipment, valves, instruments
        equipment = []
        valves = []
        instruments = []
        uncertain_items = []

        for node in topology.get("nodes", []):
            ntype = node.get("type", "component")
            nid = node.get("id", "")
            conf = node.get("confidence", 0.70)

            item_entry = {
                "id": nid,
                "label": node.get("label", nid),
                "type": ntype,
                "confidence": conf,
                "bbox": node.get("bbox", [0, 0, 0, 0]),
                "source": node.get("source", "hybrid")
            }

            if conf < 0.65 or "UNKNOWN" in nid:
                uncertain_items.append(item_entry)

            if ntype in ("pump", "vessel", "equipment"):
                equipment.append(item_entry)
            elif ntype in ("valve",) or "valve" in nid.lower() or "valve" in node.get("label", "").lower():
                valves.append(item_entry)
            elif ntype in ("instrument", "instrument_bubble") or any(nid.startswith(p) for p in ["PT-", "PI-", "FT-", "LT-", "TI-", "FO-", "SPG-", "SPN-", "SPA-", "SPD-"]):
                instruments.append(item_entry)
            else:
                equipment.append(item_entry)

        # Step 5: Targeted Crop-Level Moondream VLM Disambiguation (if query targets specific region)
        vlm_observations = []
        conflicts = []
        has_conflicts = False

        if use_vlm_disambiguation and query:
            vlm_res = await self._targeted_vlm_query(original_bgr, tiles, query, ocr_tags, detected_symbols)
            if vlm_res:
                vlm_observations.append(vlm_res)
                # Conflict detection: check if VLM component_type or notes contradicts OCR tags in this tile
                v_notes = (vlm_res.get("notes", "") + " " + vlm_res.get("component_type", "")).upper()
                tile_id = vlm_res.get("tile_id")
                # Find OCR tags in this tile
                matched_tile = next((t for t in tiles if t["tile_id"] == tile_id), None)
                if matched_tile:
                    t_tags = [
                        t["text"] for t in ocr_tags
                        if matched_tile["x"] <= t["bbox"][0] <= matched_tile["x"] + matched_tile["width"]
                        and matched_tile["y"] <= t["bbox"][1] <= matched_tile["y"] + matched_tile["height"]
                    ]
                    # Check for contradictory tag numbers (e.g. OCR has P-101 but VLM notes P-102)
                    v_tags = re.findall(r"\b[A-Z]{1,4}[-_]?[0-9]{2,5}\b", v_notes)
                    for vt in v_tags:
                        vt_norm = vt.replace("_", "-")
                        if t_tags and not any(vt_norm in tt or tt in vt_norm for tt in t_tags):
                            has_conflicts = True
                            conflicts.append(
                                f"CONFLICT in Tile {tile_id}: OCR detected tags {t_tags} but visual inspection reported {vt_norm}."
                            )

        total_latency = round(time.time() - start_time, 2)

        # Step 6: Construct Structured P&ID Representation with segregated evidence
        structured_evidence = {
            "visual_evidence": {
                "symbols_count": len(detected_symbols),
                "symbols": detected_symbols,
                "vlm_observations": vlm_observations,
                "intersections_count": topology.get("intersections_count", 0),
                "has_dashed_instrument_lines": topology.get("has_dashed_lines", False)
            },
            "ocr_evidence": {
                "tags_count": len(ocr_tags),
                "tags": ocr_tags
            },
            "topology_evidence": {
                "nodes_count": len(topology.get("nodes", [])),
                "edges_count": len(topology.get("edges", [])),
                "nodes": topology.get("nodes", []),
                "connections": topology.get("edges", [])
            },
            "knowledge_evidence": [],
            "model_inference": {
                "assumptions": ["Piping connections require continuous morphological line traces."],
                "uncertainty_notes": [f"Uncertain item: {u['label']} (conf: {u['confidence']})" for u in uncertain_items],
                "has_conflicts": has_conflicts,
                "conflicts": conflicts
            }
        }

        pid_context = {
            "image_metadata": prep["metadata"],
            "equipment": equipment,
            "valves": valves,
            "instruments": instruments,
            "connections": topology.get("edges", []),
            "ocr_tags": ocr_tags,
            "detected_symbols": detected_symbols,
            "topology_stats": topology.get("statistics", {}),
            "intersections_count": topology.get("intersections_count", 0),
            "process_segments_count": topology.get("process_segments_count", 0),
            "has_dashed_instrument_lines": topology.get("has_dashed_lines", False),
            "visual_observations": vlm_observations,
            "uncertain_items": uncertain_items,
            "structured_evidence": structured_evidence,
            "has_conflicts": has_conflicts,
            "conflicts": conflicts,
            "pipeline_latency_sec": total_latency
        }

        # Step 7: Answer question if provided
        if query:
            qa_res = self.answer_engineering_question(pid_context, query)
            pid_context["engineering_qa"] = qa_res

        return pid_context

    def answer_engineering_question(
        self,
        pid_context: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Deterministic, explainable engineering QA engine grounded strictly on structured evidence.
        Produces explicit ANSWER, CONFIDENCE, EVIDENCE, SOURCES, and VERIFICATION STATUS.
        Never hallucinates connections or equipment that lack ground evidence.
        """
        q_lower = query.lower()
        ocr_tags = pid_context.get("ocr_tags", [])
        equipment = pid_context.get("equipment", [])
        valves = pid_context.get("valves", [])
        instruments = pid_context.get("instruments", [])
        connections = pid_context.get("connections", [])
        vlm_obs = pid_context.get("visual_observations", [])
        has_conflicts = pid_context.get("has_conflicts", False)
        conflicts = pid_context.get("conflicts", [])

        # Extract mentioned tag(s) in query: e.g. P-101, PI-1027, FO-1035, T-101, etc.
        mentioned_tags = []
        for m in re.finditer(r"\b([A-Z]{1,5})[\s_\-]?([0-9]{2,5}[A-Z]?)\b", query.upper()):
            pfx, num = m.group(1), m.group(2)
            mentioned_tags.append(f"{pfx}-{num}")
        mentioned_tags = list(dict.fromkeys(mentioned_tags))

        # Check for query about nonexistent / unsupported items
        unsupported_mention = False
        target_item = None
        if mentioned_tags:
            target_tag = mentioned_tags[0]
            # Search in OCR tags and equipment
            matching = [t for t in ocr_tags if t["text"] == target_tag or target_tag in t["text"]]
            if not matching:
                matching = [e for e in equipment + valves + instruments if target_tag in e.get("id", "") or target_tag in e.get("label", "")]
            if matching:
                target_item = matching[0]
            else:
                unsupported_mention = True

        # Case 1: Unsupported / Missing Tag (e.g., P-999, T-999)
        if unsupported_mention and ("where" in q_lower or "connected" in q_lower or "upstream" in q_lower or "downstream" in q_lower or "valve" in q_lower or "instrument" in q_lower or "line" in q_lower):
            tag_name = mentioned_tags[0]
            return {
                "answer": f"Unable to locate or establish '{tag_name}' from the available diagram evidence. Tag was not detected in OCR or symbol extraction.",
                "confidence": 0.10,
                "confidence_level": "UNKNOWN",
                "evidence": [f"Tag '{tag_name}' not found in {len(ocr_tags)} detected OCR tags or {len(equipment) + len(valves)} components."],
                "sources": [{"type": "ocr", "status": "NOT_FOUND"}],
                "verification_status": "NEEDS_REVIEW",
                "has_conflicts": False,
                "conflicts": []
            }

        # Case 2: Conflict handling
        if has_conflicts:
            c_desc = "; ".join(conflicts) if conflicts else "Discrepancy detected between visual symbols and OCR tags."
            return {
                "answer": f"CONFLICT WARNING: {c_desc} Manual engineering review required.",
                "confidence": 0.40,
                "confidence_level": "LOW",
                "evidence": conflicts or ["Discrepancy detected between visual symbols and OCR tags."],
                "sources": [{"type": "conflict_monitor", "details": conflicts}],
                "verification_status": "NEEDS_REVIEW",
                "has_conflicts": True,
                "conflicts": conflicts
            }

        # Case 3: "What equipment is present?" / "List equipment"
        if any(w in q_lower for w in ["what equipment", "equipment present", "list equipment", "what components"]):
            eq_labels = [e["label"] for e in equipment]
            v_labels = [v["label"] for v in valves[:6]]
            ins_labels = [i["label"] for i in instruments[:6]]
            ans_parts = []
            if eq_labels:
                ans_parts.append(f"Primary process equipment: {', '.join(eq_labels[:6])}")
            if v_labels:
                ans_parts.append(f"Valves: {', '.join(v_labels)}")
            if ins_labels:
                ans_parts.append(f"Instrumentation: {', '.join(ins_labels)}")
            if not ans_parts:
                return {
                    "answer": "No equipment symbols or alphanumeric tags were detected in the diagram with sufficient confidence.",
                    "confidence": 0.20,
                    "confidence_level": "LOW",
                    "evidence": ["No symbols or tags detected in the provided image."],
                    "sources": [],
                    "verification_status": "NEEDS_REVIEW",
                    "has_conflicts": False,
                    "conflicts": []
                }
            ans_str = "; ".join(ans_parts)
            ev = [f"OCR tags ({len(ocr_tags)} items)", f"Valves detected ({len(valves)} items)", f"Equipment detected ({len(equipment)} items)"]
            return {
                "answer": ans_str,
                "confidence": 0.92,
                "confidence_level": "HIGH",
                "evidence": ev,
                "sources": [{"type": "ocr_tags", "count": len(ocr_tags)}, {"type": "cv_symbols", "count": len(valves) + len(equipment)}],
                "verification_status": "SUPPORTED",
                "has_conflicts": False,
                "conflicts": []
            }

        # Case 4: "Where is [Tag]?" / "Location of [Tag]"
        if any(w in q_lower for w in ["where is", "location of", "find "]) and target_item:
            bbox = target_item.get("bbox", [0, 0, 0, 0])
            lbl = target_item.get("label", target_item.get("text", mentioned_tags[0]))
            conf = target_item.get("confidence", 0.90)
            return {
                "answer": f"'{lbl}' is located at coordinates x={bbox[0]}, y={bbox[1]} (width={bbox[2]}px, height={bbox[3]}px) in the diagram.",
                "confidence": conf,
                "confidence_level": "HIGH" if conf >= 0.85 else "MEDIUM",
                "evidence": [f"OCR Tag extraction '{lbl}' at bbox {bbox} (confidence: {conf:.2f})"],
                "sources": [{"type": "ocr", "tag": lbl, "bbox": bbox}],
                "verification_status": "SUPPORTED_BY_OCR",
                "has_conflicts": False,
                "conflicts": []
            }

        # Case 5: "What line connects [A] and [B]?"
        if len(mentioned_tags) >= 2 and any(w in q_lower for w in ["line connects", "connects", "connection between", "pipe between"]):
            tagA, tagB = mentioned_tags[0], mentioned_tags[1]
            matching_edges = [
                e for e in connections
                if (tagA in e["source"] and tagB in e["destination"]) or (tagB in e["source"] and tagA in e["destination"])
                   or (tagA in e["source"] and tagB in e.get("target", "")) or (tagB in e["source"] and tagA in e.get("target", ""))
            ]
            if matching_edges:
                edge = matching_edges[0]
                return {
                    "answer": f"Piping line '{edge['line_id']}' ({edge['line_type']} line) connects '{tagA}' and '{tagB}'.",
                    "confidence": edge["confidence"],
                    "confidence_level": edge.get("confidence_level", "HIGH"),
                    "evidence": [edge["evidence"], f"Coordinates: {edge.get('evidence_coords')}"],
                    "sources": [{"type": "topology_edge", "source": tagA, "destination": tagB, "line_id": edge["line_id"]}],
                    "verification_status": "SUPPORTED_BY_TOPOLOGY",
                    "has_conflicts": False,
                    "conflicts": []
                }
            else:
                return {
                    "answer": f"Unable to establish a direct connection between '{tagA}' and '{tagB}' confidently from the available evidence.",
                    "confidence": 0.35,
                    "confidence_level": "LOW",
                    "evidence": [f"No continuous line trace found linking '{tagA}' and '{tagB}'."],
                    "sources": [{"type": "topology_search", "status": "NO_DIRECT_EDGE"}],
                    "verification_status": "NEEDS_REVIEW",
                    "has_conflicts": False,
                    "conflicts": []
                }

        # Case 6: "What is connected to [Tag]?"
        if ("connected to" in q_lower or "connections" in q_lower) and mentioned_tags:
            tag_name = mentioned_tags[0]
            related_edges = [
                e for e in connections
                if tag_name in e["source"] or tag_name in e["destination"] or tag_name in e.get("target", "")
            ]
            if related_edges:
                conn_descs = []
                ev_list = []
                for e in related_edges[:4]:
                    other = e["destination"] if tag_name in e["source"] else e["source"]
                    conn_descs.append(f"{other} through line {e['line_id']} ({e['line_type']})")
                    ev_list.append(e["evidence"])
                return {
                    "answer": f"'{tag_name}' is connected to: {'; '.join(conn_descs)}.",
                    "confidence": round(sum(e["confidence"] for e in related_edges[:4]) / len(related_edges[:4]), 2),
                    "confidence_level": "HIGH",
                    "evidence": ev_list,
                    "sources": [{"type": "topology_edges", "count": len(related_edges)}],
                    "verification_status": "SUPPORTED_BY_TOPOLOGY",
                    "has_conflicts": False,
                    "conflicts": []
                }
            else:
                return {
                    "answer": f"Unable to establish connections for '{tag_name}' confidently from the available evidence.",
                    "confidence": 0.30,
                    "confidence_level": "LOW",
                    "evidence": [f"No verified continuous line traces found connecting '{tag_name}' to other components."],
                    "sources": [{"type": "topology_search", "status": "NO_EDGES"}],
                    "verification_status": "NEEDS_REVIEW",
                    "has_conflicts": False,
                    "conflicts": []
                }

        # Case 7: "What is upstream of [Tag]?"
        if "upstream" in q_lower and mentioned_tags:
            tag_name = mentioned_tags[0]
            # Upstream means component is destination/target of line coming into it
            in_edges = [e for e in connections if tag_name in e["destination"] or tag_name in e.get("target", "")]
            if in_edges:
                e = in_edges[0]
                up_item = e["source"]
                return {
                    "answer": f"'{up_item}' is upstream of '{tag_name}' via line {e['line_id']}.",
                    "confidence": e["confidence"],
                    "confidence_level": e.get("confidence_level", "HIGH"),
                    "evidence": [e["evidence"]],
                    "sources": [{"type": "topology_edge", "upstream": up_item, "target": tag_name}],
                    "verification_status": "SUPPORTED_BY_TOPOLOGY",
                    "has_conflicts": False,
                    "conflicts": []
                }
            else:
                return {
                    "answer": f"Unable to establish upstream connections for '{tag_name}' confidently from the available evidence.",
                    "confidence": 0.30,
                    "confidence_level": "LOW",
                    "evidence": [f"No incoming line trace detected terminating at '{tag_name}'."],
                    "sources": [{"type": "topology_search", "status": "NO_INCOMING_EDGE"}],
                    "verification_status": "NEEDS_REVIEW",
                    "has_conflicts": False,
                    "conflicts": []
                }

        # Case 8: "What is downstream of [Tag]?"
        if "downstream" in q_lower and mentioned_tags:
            tag_name = mentioned_tags[0]
            # Downstream means component is source of line going out of it
            out_edges = [e for e in connections if tag_name in e["source"]]
            if out_edges:
                e = out_edges[0]
                down_item = e["destination"]
                return {
                    "answer": f"'{down_item}' is downstream of '{tag_name}' via line {e['line_id']}.",
                    "confidence": e["confidence"],
                    "confidence_level": e.get("confidence_level", "HIGH"),
                    "evidence": [e["evidence"]],
                    "sources": [{"type": "topology_edge", "source": tag_name, "downstream": down_item}],
                    "verification_status": "SUPPORTED_BY_TOPOLOGY",
                    "has_conflicts": False,
                    "conflicts": []
                }
            else:
                return {
                    "answer": f"Unable to establish downstream connections for '{tag_name}' confidently from the available evidence.",
                    "confidence": 0.30,
                    "confidence_level": "LOW",
                    "evidence": [f"No outgoing line trace detected originating from '{tag_name}'."],
                    "sources": [{"type": "topology_search", "status": "NO_OUTGOING_EDGE"}],
                    "verification_status": "NEEDS_REVIEW",
                    "has_conflicts": False,
                    "conflicts": []
                }

        # Case 9: "Which valve is associated with [Tag]?"
        if "valve" in q_lower and mentioned_tags:
            tag_name = mentioned_tags[0]
            valves_found = [v for v in valves if tag_name in v.get("label", "") or tag_name in v.get("id", "")]
            if not valves_found:
                # Look for valve connected in topology
                conn_valves = [
                    e["destination"] if tag_name in e["source"] else e["source"]
                    for e in connections
                    if (tag_name in e["source"] or tag_name in e["destination"])
                    and any(v.get("id") in (e["source"], e["destination"]) for v in valves)
                ]
                if conn_valves:
                    return {
                        "answer": f"Valve '{conn_valves[0]}' is directly associated with '{tag_name}' along the process piping line.",
                        "confidence": 0.88,
                        "confidence_level": "HIGH",
                        "evidence": [f"Topological connectivity between {tag_name} and valve {conn_valves[0]}."],
                        "sources": [{"type": "topology_edge", "valve": conn_valves[0]}],
                        "verification_status": "SUPPORTED_BY_TOPOLOGY",
                        "has_conflicts": False,
                        "conflicts": []
                    }
            if valves_found:
                v = valves_found[0]
                return {
                    "answer": f"Valve symbol '{v['label']}' is associated with tag '{tag_name}' at bbox {v['bbox']}.",
                    "confidence": v.get("confidence", 0.90),
                    "confidence_level": "HIGH",
                    "evidence": [f"Valve symbol detected at {v['bbox']} with confidence {v.get('confidence', 0.9)}"],
                    "sources": [{"type": "symbol_detector", "label": v["label"]}],
                    "verification_status": "SUPPORTED_BY_IMAGE",
                    "has_conflicts": False,
                    "conflicts": []
                }
            return {
                "answer": f"No valve was confidently identified for '{tag_name}' in the available diagram evidence.",
                "confidence": 0.30,
                "confidence_level": "LOW",
                "evidence": ["No associated valve node detected in local topology."],
                "sources": [{"type": "topology_search", "status": "NO_VALVE_FOUND"}],
                "verification_status": "NEEDS_REVIEW",
                "has_conflicts": False,
                "conflicts": []
            }

        # Case 10: "What instruments are around [Tag]?"
        if ("instrument" in q_lower or "transmitter" in q_lower or "sensor" in q_lower) and mentioned_tags:
            tag_name = mentioned_tags[0]
            # Check instruments sharing signal line or adjacent
            inst_list = [i["label"] for i in instruments if tag_name in i.get("id", "") or tag_name in i.get("label", "")]
            if not inst_list:
                inst_list = [
                    e["destination"] if tag_name in e["source"] else e["source"]
                    for e in connections
                    if (tag_name in e["source"] or tag_name in e["destination"])
                    and e.get("line_type") == "instrument_dashed"
                ]
            if inst_list:
                return {
                    "answer": f"The following instrumentation is associated with '{tag_name}': {', '.join(inst_list[:4])}.",
                    "confidence": 0.88,
                    "confidence_level": "HIGH",
                    "evidence": [f"Instrument tags identified in signal loop connected to {tag_name}."],
                    "sources": [{"type": "topology", "instruments": inst_list[:4]}],
                    "verification_status": "SUPPORTED_BY_TOPOLOGY",
                    "has_conflicts": False,
                    "conflicts": []
                }
            return {
                "answer": f"No instruments were detected in the immediate loop of '{tag_name}'.",
                "confidence": 0.35,
                "confidence_level": "LOW",
                "evidence": ["No dashed signal lines or instrument bubbles connected."],
                "sources": [{"type": "topology_search", "status": "NO_INSTRUMENT_FOUND"}],
                "verification_status": "NEEDS_REVIEW",
                "has_conflicts": False,
                "conflicts": []
            }

        # Case 11: General RAG / Operating / Purpose Query
        from backend.rag.retriever import retriever
        chunks = retriever.retrieve(query, top_k=2)

        # Extract standard designation if mentioned in query, e.g. ISO-99999, ASME B31.3
        std_match = re.search(r"\b(ISO[-\s]?\d+|ASME[-\s]?[A-Z0-9\.]+|API[-\s]?\d+|ISA[-\s]?\d+)\b", query, re.IGNORECASE)
        target_std = std_match.group(1).upper() if std_match else None

        if chunks and chunks[0].get("score", 0) >= 0.50:
            c = chunks[0]
            # If a specific standard was requested, verify the standard is actually in the retrieved content
            if target_std and target_std.replace(" ", "-") not in (c.get("content", "") + " " + c.get("document", "")).upper():
                return {
                    "answer": f"Standard '{target_std}' was not found in local sovereign technical manuals or SOPs.",
                    "confidence": 0.25,
                    "confidence_level": "LOW",
                    "evidence": [f"Nearest document '{c.get('document')}' does not contain specification for {target_std}."],
                    "sources": [{"type": "rag_miss", "requested": target_std}],
                    "verification_status": "NEEDS_REVIEW",
                    "has_conflicts": False,
                    "conflicts": []
                }

            doc_name = c.get("document", "Manual")
            page = c.get("page", 1)
            content_snippet = c.get("content", "")[:350].strip()
            return {
                "answer": f"Operating reference from {doc_name} (Page {page}): {content_snippet}",
                "confidence": round(float(c.get("score", 0.85)), 2),
                "confidence_level": "HIGH",
                "evidence": [f"RAG Chunk from {doc_name} page {page}: {content_snippet[:150]}..."],
                "sources": [{"type": "rag", "document": doc_name, "page": page, "score": c.get("score")}],
                "verification_status": "SUPPORTED_BY_RAG",
                "has_conflicts": False,
                "conflicts": []
            }

        # Fallback
        return {
            "answer": "Unable to establish this engineering query confidently from the available evidence.",
            "confidence": 0.20,
            "confidence_level": "LOW",
            "evidence": ["Insufficient topological or OCR evidence in diagram."],
            "sources": [],
            "verification_status": "NEEDS_REVIEW",
            "has_conflicts": False,
            "conflicts": []
        }

    async def _targeted_vlm_query(
        self,
        full_image: np.ndarray,
        tiles: List[Dict[str, Any]],
        query: str,
        ocr_tags: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke Moondream on a targeted tile crop to resolve visual ambiguity,
        enforcing strictly structured JSON response.
        """
        try:
            from backend.llm.ollama_provider import OllamaLLMProvider
            provider = OllamaLLMProvider()
            query_lower = query.lower()

            # Find most relevant tile
            target_tile = tiles[0]
            # Check if query mentions a specific tag
            matching_tags = [t for t in ocr_tags if t["text"].lower() in query_lower]
            if matching_tags:
                tag_bbox = matching_tags[0]["bbox"]
                tx, ty = tag_bbox[0] + tag_bbox[2] / 2, tag_bbox[1] + tag_bbox[3] / 2
                # Find tile containing this coordinate
                for t in tiles:
                    if t["x"] <= tx <= t["x"] + t["width"] and t["y"] <= ty <= t["y"] + t["height"]:
                        target_tile = t
                        break
            elif "valve" in query_lower:
                # Find tile with valves
                for t in tiles:
                    for s in symbols:
                        if s.get("category") == "valve":
                            sx, sy = s["bbox"][0], s["bbox"][1]
                            if t["x"] <= sx <= t["x"] + t["width"] and t["y"] <= sy <= t["y"] + t["height"]:
                                target_tile = t
                                break

            # Prepare tile base64
            tile_b64 = self.preprocessor.cv2_to_base64(target_tile["image"], ".png")

            # Local OCR tags in this tile
            tile_tags = [
                t["text"] for t in ocr_tags
                if target_tile["x"] <= t["bbox"][0] <= target_tile["x"] + target_tile["width"]
                and target_tile["y"] <= t["bbox"][1] <= target_tile["y"] + target_tile["height"]
            ]

            prompt = (
                f"You are an industrial P&ID diagram analyzer examining a cropped region of a P&ID.\n"
                f"Question: {query}\n"
                f"Known OCR Tags in this region: {', '.join(tile_tags) if tile_tags else 'None'}\n\n"
                "Respond ONLY with a JSON object with this exact schema:\n"
                '{"component_type": "...", "features": ["..."], "confidence": 0.8, "notes": "..."}'
            )

            req = LLMGenerateRequest(
                prompt=prompt,
                model="moondream:latest",
                images=[tile_b64],
                temperature=0.1,
                max_tokens=200
            )

            resp = await provider.generate(req)
            raw = resp.text.strip()

            # Parse structured JSON from response
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                parsed["tile_id"] = target_tile["tile_id"]
                parsed["source"] = "targeted_vlm"
                return parsed

            return {
                "component_type": "observed_feature",
                "notes": raw[:120],
                "confidence": 0.70,
                "tile_id": target_tile["tile_id"],
                "source": "targeted_vlm"
            }
        except Exception:
            return None


pid_hybrid_pipeline = PIDHybridPipeline()

