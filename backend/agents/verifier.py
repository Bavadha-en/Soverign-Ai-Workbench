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

    def verify_facts(
        self,
        claims: List[str],
        retrieved_context: List[Dict[str, Any]],
        document_text: Optional[str] = None
    ) -> VerificationSummary:
        """
        Verify each claim against retrieved RAG chunks and document text.
        Marks claims as SUPPORTED, UNSUPPORTED, or NEEDS REVIEW.
        """
        verified_claims: List[FactClaimVerification] = []
        supported_count = 0
        unsupported_count = 0
        needs_review_count = 0

        # Combine all source texts for substring / keyword checking
        all_context_text = " ".join([
            chunk.get("content", "") for chunk in retrieved_context
        ]).lower()
        if document_text:
            all_context_text += " " + document_text.lower()

        # Find default primary source
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

            # Extract key terms from claim (ignoring short stopwords)
            keywords = [w for w in re.findall(r"\b[a-zA-Z0-9\-_]{3,}\b", claim_lower) if w not in {
                "the", "and", "for", "with", "this", "that", "from", "are", "was", "were", "been", "have", "has", "must", "should"
            }]

            if not keywords:
                # Ambiguous short statement
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

            # Check keyword match ratio against ground truth context
            matches = [kw for kw in keywords if kw in all_context_text]
            match_ratio = len(matches) / len(keywords)

            # Check if source contains specific matching chunk
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
