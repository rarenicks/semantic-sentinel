import yaml
import logging
from typing import Dict, Any, List
from guardrails_lib.engine import GuardrailsEngine
from guardrails_lib.core import BaseGuardrail

# Import Guardrail Implementations
# Note: In a larger framework, these could be dynamically imported via strings
from examples.pii_guardrail import PIIGuardrail
from examples.injection_guardrail import PromptInjectionGuardrail
from examples.secret_guardrail import SecretDetectionGuardrail
from guardrails_lib.topic_guardrail import TopicGuardrail

logger = logging.getLogger("sentinel_factory")

class GuardrailsFactory:
    """
    Factory to create a GuardrailsEngine instance from a YAML configuration file.
    """

    @staticmethod
    def load_from_file(config_path: str) -> GuardrailsEngine:
        """
        Loads a YAML config and rebuilds the engine.
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loading Sentinel Profile: {config.get('profile_name', 'Unknown')}")
            return GuardrailsFactory.create_engine(config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Fallback to empty or default engine? 
            # Better to crash loudly or return empty? let's return safe default
            logger.warning("Returning default engine with only basic Injection checks.")
            return GuardrailsEngine([PromptInjectionGuardrail()])

    @staticmethod
    def create_engine(config: Dict[str, Any]) -> GuardrailsEngine:
        target_guardrails: List[BaseGuardrail] = []
        detectors = config.get("detectors", {})

        # 1. Injection (Always critical, usually first)
        if detectors.get("injection", {}).get("enabled", False):
            keywords = detectors["injection"].get("keywords", [])
            target_guardrails.append(PromptInjectionGuardrail(keywords=keywords if keywords else None))

        # 2. Secrets
        if detectors.get("secrets", {}).get("enabled", False):
            # patterns currently hardcoded in class defaults or could be passed if structure aligned
            target_guardrails.append(SecretDetectionGuardrail())

        # 3. Topics (Content blocking)
        if detectors.get("topics", {}).get("enabled", False):
            block_list = detectors["topics"].get("block_list", [])
            target_guardrails.append(TopicGuardrail(block_list=block_list))

        # 4. PII (Sanitization)
        if detectors.get("pii", {}).get("enabled", False):
            # The PIIGuardrail implementation uses a Dict[name, pattern].
            # The config typically provides a list of names to enabled (patterns: ["EMAIL", ...])
            # We can modify PIIGuardrail to accept a list of enabled keys and use internal defaults, 
            # OR generic pattern config. 
            # Our current PIIGuardrail expects a dict or uses ALL defaults. 
            # Let's use ALL defaults for now as per current implementation, 
            # or filtering by list if we enhance PIIGuardrail later.
            # Simplified for MVP: Use default patterns.
            target_guardrails.append(PIIGuardrail())

        return GuardrailsEngine(guardrails=target_guardrails)
