from typing import List, Dict, Any, Optional
import re
import logging
from guardrails_lib.core import BaseGuardrail, GuardrailResult
from guardrails_lib.topic_guardrail import TopicGuardrail
# Actually Factory calls Engine(guardrails=[...]). 
# But the NEW requirement says Engine handles YAML config directly?
# "Refactor core/engine.py ... Class: GuardrailsEngine ... __init__: Load the YAML config."
# So Engine will now take config directly, replacing Factory logic or merging it.

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

logger = logging.getLogger("sentinel_engine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class GuardrailsEngine:
    """
    v2.0 Semantic Sentinel Engine
    - Pre-compiled Regex (Performance)
    - Semantic Analysis (Sentence Transformers)
    - PII Redaction
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.detectors = config.get("detectors", {})
        self.profile_name = config.get("profile_name", "Unknown")

        # --- 1. Pre-compile PII Patterns ---
        self.pii_patterns = []
        if self.detectors.get("pii", {}).get("enabled", False):
            # Optimisation: Hardcoded common patterns for v2.0 performance
            # In a real app, these might come from a robust library or config list
            # We compile them ONCE here.
            patterns = {
                "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                "SSN": r"\b\d{3}-\d{2}-\d{4}\b"
            }
            # Only enable patterns listed in config or all if vague?
            # Config says: patterns: ["EMAIL", "PHONE"]
            enabled_keys = self.detectors["pii"].get("patterns", [])
            for key in enabled_keys:
                if key in patterns:
                    self.pii_patterns.append((key, re.compile(patterns[key])))
            logger.info(f"[{self.profile_name}] PII: Compiled {len(self.pii_patterns)} patterns.")

        # --- 2. Pre-compile Topic/Keyword Patterns ---
        self.topic_pattern = None
        if self.detectors.get("topics", {}).get("enabled", False):
            block_list = self.detectors["topics"].get("block_list", [])
            if block_list:
                pattern_str = r'\b(' + '|'.join(map(re.escape, block_list)) + r')\b'
                self.topic_pattern = re.compile(pattern_str, re.IGNORECASE)
                logger.info(f"[{self.profile_name}] Topics: Compiled regex with {len(block_list)} keywords.")

        # --- 3. Initialize Semantic Model ---
        self.semantic_model = None
        self.forbidden_embeddings = None
        self.semantic_threshold = 0.0
        
        semantic_cfg = self.detectors.get("semantic_blocking", {})
        if semantic_cfg.get("enabled", False):
            if not SEMANTIC_AVAILABLE:
                logger.warning("Semantic blocking enabled but 'sentence-transformers' not installed. Skipping.")
            else:
                try:
                    logger.info("Loading Semantic Model (all-MiniLM-L6-v2)...")
                    self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    intents = semantic_cfg.get("forbidden_intents", [])
                    if intents:
                        self.forbidden_embeddings = self.semantic_model.encode(intents)
                        self.semantic_threshold = semantic_cfg.get("threshold", 0.8)
                        logger.info(f"[{self.profile_name}] Semantic: Encoded {len(intents)} intents. Threshold: {self.semantic_threshold}")
                except Exception as e:
                    logger.error(f"Failed to load Semantic Model: {e}")
                    # Fail securely? or just log? User asked to "handle gracefully"
                    # We will continue without semantic checks but log error.

    def validate(self, text: str) -> GuardrailResult:
        """
        Public compatibility wrapper for existing code.
        Returns a simplified GuardrailResult.
        """
        result = self.scan(text)
        
        # If any rule triggered, it's invalid
        is_valid = len(result["triggered_rules"]) == 0
        
        sanitized = result["sanitized_prompt"]
        reason = ", ".join(result["triggered_rules"]) if not is_valid else ""
        
        # Determine action (blocked/redacted/allowed)
        action = "allowed"
        if not is_valid:
            if "PII:" in reason and len(result["triggered_rules"]) == 1:
                # If ONLY PII, it's valid but sanitized (technically 'valid' for processing, but modified)
                # Existing main.py logic expects valid=True for PII unless we return sanitized text
                # Actually main.py checks "if not result.valid: return 400".
                # So for PII redaction, we must return valid=True but with changed text.
                is_valid = True 
                reason = "PII Redacted"
                action = "redacted"
            else:
                action = "blocked"
        
        return GuardrailResult(
            valid=is_valid,
            sanitized_text=sanitized,
            reason=reason,
            action=action
        )

    def scan(self, prompt: str) -> Dict[str, Any]:
        """
        v2.0 Optimized Scan Pipeline
        """
        triggered = []
        sanitized_prompt = prompt
        semantic_score = 0.0

        # Step 1: PII Redaction
        for name, pattern in self.pii_patterns:
            if pattern.search(sanitized_prompt):
                # Redact
                msg = f"<{name}_REDACTED>"
                sanitized_prompt = pattern.sub(msg, sanitized_prompt)
                triggered.append(f"PII:{name}")

        # Step 2: Keyword Blocking (Topics)
        if self.topic_pattern:
            matches = self.topic_pattern.findall(sanitized_prompt)
            if matches:
                unique = sorted(list(set(matches)))
                triggered.append(f"Topic:{','.join(unique)}")

        # Step 3: Semantic Blocking
        # Only run if no blocking keywords found yet? Or always run?
        # Usually semantic is heavier, run last.
        if self.semantic_model and self.forbidden_embeddings is not None:
            # Encode prompt
            prompt_emb = self.semantic_model.encode([sanitized_prompt])
            # Compute similarity
            scores = cosine_similarity(prompt_emb, self.forbidden_embeddings)[0]
            max_score = float(max(scores))
            semantic_score = max_score
            
            if max_score > self.semantic_threshold:
                triggered.append(f"Semantic:Intent violation ({max_score:.2f})")
            
            logger.info(f"Semantic Check: Score={max_score:.4f} Threshold={self.semantic_threshold} Prompt='{sanitized_prompt[:30]}...'")

        return {
            "sanitized_prompt": sanitized_prompt,
            "triggered_rules": triggered,
            "semantic_score": semantic_score
        }
