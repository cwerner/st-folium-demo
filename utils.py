from prometheus_client import Summary


class REGISTRY:
    inited = False

    @classmethod
    def get_metrics(cls):
        if cls.inited:
            return cls
        else:
            # Register your metrics here
            cls.REQUEST_TIME = Summary(
                "some_summary", "Time spent in processing request"
            )
            cls.inited = True
