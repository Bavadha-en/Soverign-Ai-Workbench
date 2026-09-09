import json
import re
from typing import Any, Dict, List, Optional

from backend.agents.schemas import FactClaimVerification, FactVerificationStatus, VerificationSummary


class Verifier:
    """
    Verification Engine for ConfigIQ Sovereign Agent.
    Implements:
      1. Fact-checking of extracted claims against retrieved context and sources.
      2. Calculation-checking of code sandbox execution outputs.
      3. Generation of verification summaries with SUPPORTED / UNSUPPORTED / NEEDS REVIEW flags.
    """

    async def _llm_verify_claim(
        self,
        claim: str,
        context_text: str,
        source_doc: str,
        page: int,
    ) -> Optional[FactClaimVerification]:
        """Use local LLM to semantically verify a claim against context."""
        try:
            from backend.llm.factory import get_llm_provider
            from backend.models.schemas import LLMGenerateRequest

            provider = get_llm_provider()
            if provider.__class__.__name__ == "MockLLMProvider":
                return None
            prompt = (
                "You are a fact-verification engine. Given a CLAIM and SOURCE CONTEXT, determine if the claim is supported.\n\n"
                f"CLAIM: {claim}\n\n"
                f"SOURCE CONTEXT:\n{context_text[:3000]}\n\n"
                "Respond with EXACTLY one JSON object: "
                '{"verdict": "SUPPORTED"|"UNSUPPORTED"|"NEEDS_REVIEW", "confidence": 0.0-1.0, "evidence": "brief quote or reason"}'
            )
            request = LLMGenerateRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=256,
            )
            response = await provider.generate(request)
            raw = response.text.strip()
            match = re.search(r"\{[^}]+\}", raw)
            if not match:
                return None
            parsed = json.loads(match.group(0))
            verdict = parsed.get("verdict", "").upper().replace(" ", "_")
            status_map = {
                "SUPPORTED": FactVerificationStatus.SUPPORTED,
                "UNSUPPORTED": FactVerificationStatus.UNSUPPORTED,
                "NEEDS_REVIEW": FactVerificationStatus.NEEDS_REVIEW,
            }
            status = status_map.get(verdict)
            if status is None:
                return None
            return FactClaimVerification(
                claim=claim,
                status=status,
                source_document=source_doc,
                page=page,
                confidence=round(float(parsed.get("confidence", 0.7)), 2),
                evidence=parsed.get("evidence", ""),
            )
        except Exception:
            return None

    def verify_facts(
        self,
        claims: List[str],
        retrieved_context: List[Dict[str, Any]],
        document_text: Optional[str] = None
    ) -> VerificationSummary:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self._verify_facts_async(claims, retrieved_context, document_text),
                )
                return future.result(timeout=120)
        return asyncio.run(self._verify_facts_async(claims, retrieved_context, document_text))

    async def _verify_facts_async(
        self,
        claims: List[str],
        retrieved_context: List[Dict[str, Any]],
        document_text: Optional[str] = None
    ) -> VerificationSummary:
        """
        Verify each claim against retrieved RAG chunks and document text.
        Attempts LLM-powered semantic verification first, falls back to keyword matching.
        """
        verified_claims: List[FactClaimVerification] = []
        supported_count = 0
        unsupported_count = 0
        needs_review_count = 0
        llm_verified = 0

        all_context_text = " ".join([
            chunk.get("content", "") for chunk in retrieved_context
        ]).lower()
        if document_text:
            all_context_text += " " + document_text.lower()

        all_context_raw = " ".join([chunk.get("content", "") for chunk in retrieved_context])
        if document_text:
            all_context_raw += " " + document_text

        primary_source = "retrieved_sop"
        primary_page = 1
        if retrieved_context:
            first_meta = retrieved_context[0].get("metadata", {})
            primary_source = first_meta.get("document", retrieved_context[0].get("document", "retrieved_sop"))
            primary_page = first_meta.get("page", retrieved_context[0].get("page", 1))

        for claim in claims:
            if not claim or not claim.strip():
                continue

            claim_clean = claim.strip()
            claim_lower = claim_clean.lower()

            # Try LLM semantic verification first
            llm_result = await self._llm_verify_claim(
                claim_clean, all_context_raw, primary_source, primary_page
            )
            if llm_result is not None:
                verified_claims.append(llm_result)
                llm_verified += 1
                if llm_result.status == FactVerificationStatus.SUPPORTED:
                    supported_count += 1
                elif llm_result.status == FactVerificationStatus.UNSUPPORTED:
                    unsupported_count += 1
                else:
                    needs_review_count += 1
                continue

            # Fallback: keyword-based verification
            keywords = [w for w in re.findall(r"\b[a-zA-Z0-9\-_]{3,}\b", claim_lower) if w not in {
                "the", "and", "for", "with", "this", "that", "from", "are", "was", "were", "been", "have", "has", "must", "should"
            }]

            if not keywords:
                verified_claims.append(FactClaimVerification(
                    claim=claim_clean,
                    status=FactVerificationStatus.NEEDS_REVIEW,
                    source_document=primary_source,
                    page=primary_page,
                    confidence=0.5,
                    evidence="Claim contains insufficient specific terms for automated provenance matching."
                ))
                needs_review_count += 1
                continue

            matches = [kw for kw in keywords if kw in all_context_text]
            match_ratio = len(matches) / len(keywords)

            matched_source_doc = primary_source
            matched_page = primary_page
            evidence_snippet = None

            for chunk in retrieved_context:
                content = chunk.get("content", "").lower()
                chunk_matches = [kw for kw in keywords if kw in content]
                if len(chunk_matches) >= 2 or (len(keywords) == 1 and len(chunk_matches) == 1):
                    meta = chunk.get("metadata", {})
                    matched_source_doc = meta.get("document", chunk.get("document", primary_source))
                    matched_page = meta.get("page", chunk.get("page", 1))
                    evidence_snippet = chunk.get("content", "")[:120] + "..."
                    break

            if match_ratio >= 0.4 or evidence_snippet is not None:
                # Classify granular engineering provenance
                is_topology_match = any(t in claim_lower for t in ["connect", "upstream", "downstream", "line l-", "piping line", "piping connection", "signal line", "traces"])
                is_ocr_match = any(t in claim_lower for t in ["tag", "pt-", "pi-", "fo-", "p-", "v-", "cv-", "spg-", "spn-", "spa-", "spd-", "cbj-"]) or "ocr" in all_context_text
                is_image_match = any(w in claim_lower for w in ["valve", "pump", "symbol", "diagram", "dashed", "junction", "triangle", "circle"])
                is_rag_match = any(s in claim_lower for s in ["sop", "iso", "api", "standard", "code", "procedure", "asme", "limit", "criterion"]) or (evidence_snippet and "sop" in matched_source_doc.lower())

                if is_topology_match and ("line" in all_context_text or "connection" in all_context_text):
                    status = FactVerificationStatus.SUPPORTED_BY_TOPOLOGY
                elif is_ocr_match and ("ocr" in all_context_text or re.search(r"[A-Z]{1,4}-[0-9]{2,5}", claim_clean)):
                    status = FactVerificationStatus.SUPPORTED_BY_OCR
                elif is_rag_match or "retrieved" in matched_source_doc.lower() or "sop" in matched_source_doc.lower():
                    status = FactVerificationStatus.SUPPORTED_BY_RAG
                elif is_image_match:
                    status = FactVerificationStatus.SUPPORTED_BY_IMAGE
                else:
                    status = FactVerificationStatus.SUPPORTED

                confidence = round(max(0.75, min(0.99, match_ratio + 0.3)), 2)
                supported_count += 1
            elif any(w in claim_lower for w in ["recommend", "infer", "suggest", "indicates", "conclude", "consistent with", "assumption", "hypothes"]):
                status = FactVerificationStatus.MODEL_INFERENCE
                confidence = 0.70
            elif match_ratio > 0.15 or "unable to" in claim_lower or "insufficient" in claim_lower:
                status = FactVerificationStatus.NEEDS_REVIEW
                confidence = 0.55
                needs_review_count += 1
            else:
                status = FactVerificationStatus.UNSUPPORTED
                confidence = 0.20
                unsupported_count += 1


            verified_claims.append(FactClaimVerification(
                claim=claim_clean,
                status=status,
                source_document=matched_source_doc,
                page=matched_page,
                confidence=confidence,
                evidence=evidence_snippet
            ))

        total = len(verified_claims)
        is_valid = (unsupported_count == 0) and (total > 0)

        notes = []
        if total > 0:
            notes.append(f"{supported_count}/{total} claims verified as SUPPORTED.")
        if llm_verified > 0:
            notes.append(f"{llm_verified}/{total} claims verified via LLM semantic grounding.")
        if unsupported_count > 0:
            notes.append(f"{unsupported_count} claims flagged as UNSUPPORTED against local knowledge base.")
        if needs_review_count > 0:
            notes.append(f"{needs_review_count} claims flagged as NEEDS REVIEW.")

        return VerificationSummary(
            is_valid=is_valid,
            total_claims=total,
            supported_claims=supported_count,
            unsupported_claims=unsupported_count,
            needs_review_claims=needs_review_count,
            claims=verified_claims,
            notes=notes
        )

    # Operating envelopes for quantities the verifier can recognise in stdout.
    # "hard" bounds are physically impossible to leave, so breaching one fails the
    # step and triggers a retry. "typical" is the band a healthy machine sits in;
    # a value inside "hard" but outside "typical" is possible yet implausible, so
    # it is escalated for human review rather than silently accepted.
    QUANTITY_RULES: Dict[str, Dict[str, Any]] = {
        "efficiency": {
            "hard": (0.0, 100.0),
            "typical": (20.0, 95.0),
            "unit": "%",
            "typical_reason": "a centrifugal pump operating normally sits between 20% and 95%",
        },
    }

    @staticmethod
    def _extract_labelled_values(stdout: str, keyword: str, unit: str = "") -> List[tuple]:
        """
        Pull out `<label>: <number><unit>` pairs whose label mentions `keyword`.

        Reading the last number in stdout is not safe — that is whatever the script
        printed last, not the quantity being checked. The label may not span a
        colon or equals sign, so `Final Result: Pump Efficiency = 74.3%` yields the
        label "Pump Efficiency" rather than the whole line.

        When the quantity carries a unit, the unit must follow the number. Scripts
        commonly print their working ("Efficiency = 2.675 * 100"), and those
        intermediate values are not the result being verified.
        """
        pattern = re.compile(
            r"([^\n:=]*\b"
            + re.escape(keyword)
            + r"\b[^\n:=]*?)\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*"
            + (re.escape(unit) if unit else "")
            + (r"(?![\d.])" if unit else r"\s*(?:$|[\n,;)])"),
            re.IGNORECASE | re.MULTILINE,
        )

        found: List[tuple] = []
        for match in pattern.finditer(stdout):
            label = " ".join(match.group(1).split()).strip("|- \t")
            if not label:
                label = keyword.capitalize()
            try:
                found.append((label, float(match.group(2))))
            except ValueError:
                continue
        return found

    @staticmethod
    def _calculation_summary(
        is_valid: bool,
        status: str,
        claims: List[FactClaimVerification],
        notes: List[str],
        reason: Optional[str] = None,
        stdout: str = "",
    ) -> Dict[str, Any]:
        """
        Shape the calculation verdict like a VerificationSummary so the same UI
        panel can render it, while keeping the keys the orchestrator reads.
        """
        supported = sum(1 for c in claims if c.status == FactVerificationStatus.SUPPORTED)
        unsupported = sum(1 for c in claims if c.status == FactVerificationStatus.UNSUPPORTED)
        needs_review = sum(1 for c in claims if c.status == FactVerificationStatus.NEEDS_REVIEW)

        payload: Dict[str, Any] = {
            "is_valid": is_valid,
            "status": status,
            "calculation_valid": is_valid,
            "total_claims": len(claims),
            "supported_claims": supported,
            "unsupported_claims": unsupported,
            "needs_review_claims": needs_review,
            "claims": [c.model_dump() for c in claims],
            "notes": notes,
        }
        if reason:
            payload["reason"] = reason
        if stdout:
            payload["stdout"] = stdout
        return payload

    def verify_calculation(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an engineering calculation executed in the sandbox.

        Checks execution health (exit code, timeout, output present) and then the
        physical plausibility of the numbers produced. A clean exit code alone is
        not evidence that an answer is correct.
        """
        status = execution_result.get("status", "error")
        stdout = execution_result.get("stdout", "") or ""
        stderr = execution_result.get("stderr", "") or ""
        exit_code = execution_result.get("exit_code", -1)

        def failure(reason: str, note: str) -> Dict[str, Any]:
            claim = FactClaimVerification(
                claim=reason,
                status=FactVerificationStatus.UNSUPPORTED,
                source_document="sandbox_execution",
                confidence=0.95,
                evidence=note,
            )
            return self._calculation_summary(False, "FAILED", [claim], [note], reason=reason)

        if status == "timeout":
            return failure(
                "Sandbox execution exceeded the timeout limit.",
                "Execution timed out. Reduce iterations or simplify the algorithm.",
            )

        if exit_code != 0 or status != "success":
            return failure(
                f"Execution failed with exit code {exit_code}.",
                f"Runtime error in Python code: {stderr.strip()}",
            )

        if not stdout.strip():
            return failure(
                "The script exited cleanly but printed no results.",
                "Calculation completed but did not write final results to stdout.",
            )

        stdout_lower = stdout.lower()
        if any(token in stdout_lower for token in ("nan", "infinity", "zerodivision")):
            return failure(
                "Calculation produced an undefined or infinite value.",
                "Detected NaN, Infinity or a division by zero in the output.",
            )

        claims: List[FactClaimVerification] = [
            FactClaimVerification(
                claim="Calculation ran to completion in the isolated sandbox (exit code 0).",
                status=FactVerificationStatus.SUPPORTED,
                source_document="sandbox_execution",
                confidence=0.99,
                evidence=stdout.strip()[:160],
            )
        ]
        notes: List[str] = ["Sandbox execution completed successfully with exit code 0."]
        is_valid = True
        breach_reason: Optional[str] = None

        for keyword, rule in self.QUANTITY_RULES.items():
            hard_low, hard_high = rule["hard"]
            typ_low, typ_high = rule["typical"]
            unit = rule["unit"]

            # A script often prints the same figure twice (once inline, once as a
            # final result); report each distinct value once.
            seen_values: set = set()
            for label, value in self._extract_labelled_values(stdout, keyword, unit):
                if round(value, 6) in seen_values:
                    continue
                seen_values.add(round(value, 6))

                if value < hard_low or value > hard_high:
                    is_valid = False
                    breach_reason = (
                        f"{label} of {value}{unit} is outside the physical "
                        f"{hard_low:g}-{hard_high:g}{unit} range."
                    )
                    notes.append(breach_reason)
                    claims.append(FactClaimVerification(
                        claim=f"{label} = {value}{unit}",
                        status=FactVerificationStatus.UNSUPPORTED,
                        source_document="physical_bounds_check",
                        confidence=0.95,
                        evidence=f"Physically impossible: outside {hard_low:g}-{hard_high:g}{unit}.",
                    ))
                elif value < typ_low or value > typ_high:
                    note = (
                        f"{label} of {value}{unit} is inside the physical range but outside the "
                        f"expected {typ_low:g}-{typ_high:g}{unit} band — {rule['typical_reason']}. "
                        "Confirm the formula and the input values before issuing this result."
                    )
                    notes.append(note)
                    claims.append(FactClaimVerification(
                        claim=f"{label} = {value}{unit}",
                        status=FactVerificationStatus.NEEDS_REVIEW,
                        source_document="physical_bounds_check",
                        confidence=0.45,
                        evidence=note,
                    ))
                else:
                    claims.append(FactClaimVerification(
                        claim=f"{label} = {value}{unit}",
                        status=FactVerificationStatus.SUPPORTED,
                        source_document="physical_bounds_check",
                        confidence=0.9,
                        evidence=f"Within the expected {typ_low:g}-{typ_high:g}{unit} band.",
                    ))

        if is_valid:
            needs_review = any(c.status == FactVerificationStatus.NEEDS_REVIEW for c in claims)
            verdict = "REVIEW" if needs_review else "PASSED"
        else:
            verdict = "FAILED"

        return self._calculation_summary(
            is_valid,
            verdict,
            claims,
            notes,
            reason=breach_reason,
            stdout=stdout.strip(),
        )


verifier = Verifier()
