class AURA:

    def __init__(self):
        # Phase B: Lazy load the chatbot state graph to prevent heavy imports
        # during light testing / CI collection steps.
        self._chatbot = None

    @property
    def chatbot(self):
        if self._chatbot is None:
            from pipeline.aura_chat_graph import AuraChatGraph
            self._chatbot = AuraChatGraph()
        return self._chatbot

    def ask(
        self,
        question,
        history=None,
        identity=None,
        display_profile=None,
        on_delta=None,
        summary=None,
    ):
        return self.chatbot.chat(
            query=question,
            history=history,
            identity=identity,
            display_profile=display_profile,
            on_delta=on_delta,
            summary=summary,
        )
