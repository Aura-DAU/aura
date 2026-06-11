from pipeline.aura_chat import AuraChat


class AURA:

    def __init__(self):

        self.chatbot = AuraChat()

    def ask(
        self,
        question,
        history=None,
        profile=None
    ):

        return self.chatbot.chat(
            query=question,
            history=history,
            profile=profile
        )