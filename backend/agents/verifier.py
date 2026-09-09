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
                status = FactVerificationStatus.SUPPORTED
                confidence = round(max(0.75, min(0.99, match_ratio + 0.3)), 2)
                supported_count += 1
            elif match_ratio > 0.15:
                status = FactVerificationStatus.NEEDS_REVIEW
                confidence = 0.55
                needs_review_count += 1
            else:
                status = FactVerificationStatus.UNSUPPORTED
                confidence = 0.2
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

    def verify_calculation(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify engineering calculation executed in sandbox.
        Checks exit code, errors, timeout, and output validity.
        """
        status = execution_result.get("status", "error")
        stdout = execution_result.get("stdout", "")
        stderr = execution_result.get("stderr", "")
        exit_code = execution_result.get("exit_code", -1)

        notes = []
        is_valid = True

        if status == "timeout":
            return {
                "is_valid": False,
                "status": "FAILED",
                "reason": "Sandbox execution exceeded timeout limit.",
                "notes": ["Execution timed out. Optimize algorithm or reduce iterations."]
            }

        if exit_code != 0 or status != "success":
            return {
                "is_valid": False,
                "status": "FAILED",
                "reason": f"Execution failed with exit code {exit_code}: {stderr}",
                "notes": [f"Runtime error in Python code: {stderr.strip()}"]
            }

        if not stdout or not stdout.strip():
            return {
                "is_valid": False,
                "status": "FAILED",
                "reason": "Python script exited normally but produced no stdout output.",
                "notes": ["Calculation completed but did not print final results to stdout."]
            }

        # Check for numerical validity in stdout (e.g. negative efficiency, NaN, Inf)
        stdout_lower = stdout.lower()
        if "nan" in stdout_lower or "infinity" in stdout_lower or "zerodivision" in stdout_lower:
            return {
                "is_valid": False,
                "status": "FAILED",
                "reason": "Calculation produced undefined or infinite numerical output.",
                "notes": ["Detected NaN or Infinity in calculation output."]
            }

        # Efficiency range check if efficiency calculation
        if "efficiency" in stdout_lower:
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", stdout)
            if numbers:
                val = float(numbers[-1])
                if val < 0 or val > 100:
                    notes.append(f"Efficiency value {val}% is outside physical 0-100% boundary.")

        notes.append("Sandbox execution completed successfully with exit code 0.")
        return {
            "is_valid": is_valid,
            "status": "PASSED",
            "stdout": stdout.strip(),
            "notes": notes
        }


verifier = Verifier()
