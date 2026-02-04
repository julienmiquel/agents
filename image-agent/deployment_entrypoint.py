from agent import root_agent

# The agent variable must be named 'agent' for the deployment to pick it up automatically

class AgentWrapper:
    def __init__(self, agent_instance):
        self._agent = agent_instance
    def set_up(self):
        # Safe OTel Logging Initialization
        try:
            from opentelemetry.instrumentation.logging import LoggingInstrumentor
            LoggingInstrumentor().instrument(set_logging_format=True)
        except Exception:
            pass

        # Ultra-robust JIT patching to ensure inner agent has the attribute
        # regardless of Pydantic or pickling restrictions.
        try:
             # Use object.__setattr__ to bypass Pydantic 'extra=forbid'
             object.__setattr__(self._agent, 'agent_framework', 'adk')
        except Exception:
             try:
                 # Fallback: Patch the class directly
                 self._agent.__class__.agent_framework = property(lambda x: "adk")
             except Exception:
                 pass

        # We intentionally DO NOT call self._agent.set_up() if it's likely to crash.
        # However, if patching succeeded above, it might be safe.
        # Following the previous 'pass' strategy as a baseline for stability.
        pass

    def query(self, *args, **kwargs):
        return self._agent.query(*args, **kwargs)

    def invoke(self, *args, **kwargs):
         # Support invoke if the agent has it
         if hasattr(self._agent, "invoke"):
             return self._agent.invoke(*args, **kwargs)
         return self._agent.query(*args, **kwargs)

    def __getattr__(self, name):
        # Delegate other attributes, safely handling _agent access
        if name == "_agent":
             raise AttributeError()
        return getattr(self._agent, name)

agent = AgentWrapper(root_agent)
