from typing import List, Optional
from sentinel.engine import GuardrailsEngine

try:
    from llama_index.core.postprocessor.types import BaseNodePostprocessor
    from llama_index.core.schema import NodeWithScore, QueryBundle
    from pydantic import Field
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

if LLAMA_INDEX_AVAILABLE:
    class SentinelNodePostprocessor(BaseNodePostprocessor):
        """
        LlamaIndex Postprocessor to sanitise retrieved nodes.
        
        Usage:
            engine = GuardrailsFactory.load("finance")
            processor = SentinelNodePostprocessor(engine=engine)
            
            index.as_query_engine(
                node_postprocessors=[processor]
            )
        """
        engine: GuardrailsEngine = Field(..., description="The Sentinel Engine")
        redact_only: bool = Field(default=False, description="If True, redact PII but keep node. If False, drop blocked nodes.")

        def _postprocess_nodes(
            self,
            nodes: List[NodeWithScore],
            query_bundle: Optional[QueryBundle] = None,
        ) -> List[NodeWithScore]:
            
            safe_nodes = []
            
            for node_w_score in nodes:
                node_text = node_w_score.node.get_content()
                
                # Validate the retrieved context
                result = self.engine.validate(node_text)
                
                if result.valid:
                    # If valid but changed (redacted), update content
                    if result.sanitized_text != node_text:
                        node_w_score.node.set_content(result.sanitized_text)
                    safe_nodes.append(node_w_score)
                else:
                    # It was blocked
                    if self.redact_only:
                        # Replace content with redact message
                        node_w_score.node.set_content(f"[CONTENT REDACTED: {result.reason}]")
                        safe_nodes.append(node_w_score)
                    else:
                        # Drop the node entirely (default security behavior)
                        pass
                        
            return safe_nodes
else:
    class SentinelNodePostprocessor:
        def __init__(self, *args, **kwargs):
            raise ImportError("llama-index-core not installed. Run `pip install llama-index-core`")
