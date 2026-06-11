from Pipeline.retrieval.retrieval_pipeline import (
    RetrievalPipeline
)

from Pipeline.generation.answer_generator import (
    AnswerGenerator
)


class AuraChat:

    def __init__(self):

        self.pipeline = (
            RetrievalPipeline()
        )

        self.generator = (
            AnswerGenerator()
        )

    def chat(
        self,
        query,
        history=None
    ):

        retrieval_result = (
            self.pipeline.get_context(
                query,
                history=history
            )
        )


        answer = (
            self.generator.generate(

                query=query,

                context=retrieval_result[
                    "context"
                ],

                history=history
            )
        )

        return {

            "answer": answer,

            "sources":
                retrieval_result[
                    "sources"
                ]
        }