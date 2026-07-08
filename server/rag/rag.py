from pipeline.aura_chat import AuraChat


class AURA:

    def __init__(self):

        self.chatbot = AuraChat()

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
