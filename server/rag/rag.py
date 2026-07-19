from pipeline.aura_chat_graph import AuraChatGraph


class AURA:

    def __init__(self):

        # Phase B: Agent Orchestrator, per the architecture doc, is now a
        # LangGraph StateGraph (pipeline/aura_chat_graph.py) rather than the
        # hand-written if/return sequence in pipeline/aura_chat.py. The
        # latter is kept in the codebase as the reference implementation —
        # every node in the graph delegates to the same collaborators it
        # used to call directly.
        self.chatbot = AuraChatGraph()

    def ask(
        self,
        question,
        history=None,
        identity=None,
        display_profile=None,
    ):

        return self.chatbot.chat(
            query=question,
            history=history,
            identity=identity,
            display_profile=display_profile,
        )
